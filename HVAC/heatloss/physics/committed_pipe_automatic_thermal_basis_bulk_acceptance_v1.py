# ======================================================================
# H-S66-N2D1B — Atomic missing automatic thermal-basis acceptance
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    CommittedPipeSectionThermalConditionBasisIntentV1,
)


@dataclass(frozen=True, slots=True)
class CommittedPipeAutomaticThermalBasisBulkAcceptanceV1:
    """One validated replacement intent for an exact committed schedule."""

    intent: CommittedPipeSectionThermalConditionBasisIntentV1
    section_count: int
    preserved_section_count: int
    added_section_count: int
    status: str


def build_committed_pipe_automatic_thermal_basis_bulk_acceptance_v1(
        *,
        committed_schedule_fingerprint: str,
        committed_section_ids: Iterable[str],
        automatic_resolution: Any,
        existing_intent: CommittedPipeSectionThermalConditionBasisIntentV1 | None,
) -> CommittedPipeAutomaticThermalBasisBulkAcceptanceV1:
    """Accept every missing complete preview without mutating existing intent.

    All identities and every missing automatic basis are validated before a
    cloned intent is changed. Existing bases and sparse emissivity overrides
    therefore remain authoritative and a failure cannot partly fill a schedule.
    """

    fingerprint = str(committed_schedule_fingerprint or "").strip()
    if not fingerprint:
        raise ValueError("Committed pipe schedule fingerprint is required")

    section_ids = tuple(
        str(section_id or "").strip()
        for section_id in committed_section_ids
    )
    if not section_ids or any(not section_id for section_id in section_ids):
        raise ValueError("Every committed pipe section requires stable identity")
    if len(set(section_ids)) != len(section_ids):
        raise ValueError("Committed pipe section identities must be unique")

    if not bool(getattr(automatic_resolution, "ready", False)):
        raise ValueError(
            "Automatic committed-section thermal-basis resolution is not ready"
        )
    automatic_rows = tuple(
        getattr(automatic_resolution, "sections", ()) or ()
    )
    automatic_by_id: dict[str, Any] = {}
    for row in automatic_rows:
        section_id = str(getattr(row, "section_id", "") or "").strip()
        if not section_id:
            raise ValueError(
                "Every automatic thermal-basis row requires section identity"
            )
        if section_id in automatic_by_id:
            raise ValueError(
                f"Duplicate automatic thermal-basis identity: {section_id}"
            )
        automatic_by_id[section_id] = row
    if set(automatic_by_id) != set(section_ids):
        raise ValueError(
            "Automatic thermal-basis identities must exactly match the "
            "committed pipe schedule"
        )

    if existing_intent is None:
        source_intent = CommittedPipeSectionThermalConditionBasisIntentV1()
    elif isinstance(
        existing_intent,
        CommittedPipeSectionThermalConditionBasisIntentV1,
    ):
        source_intent = existing_intent
    else:
        raise TypeError(
            "CommittedPipeSectionThermalConditionBasisIntentV1 required"
        )

    stored_fingerprint = str(
        source_intent.committed_schedule_fingerprint or ""
    ).strip()
    if stored_fingerprint and stored_fingerprint != fingerprint:
        raise ValueError(
            "Persisted section thermal bases are stale; clear them before "
            "accepting the current committed schedule"
        )
    existing_ids = set(source_intent.basis_by_section_id)
    if not existing_ids.issubset(set(section_ids)):
        raise ValueError(
            "Persisted section thermal bases contain non-current identity"
        )

    missing_ids = tuple(
        section_id for section_id in section_ids
        if section_id not in existing_ids
    )
    candidates: list[tuple[str, object]] = []
    for section_id in missing_ids:
        row = automatic_by_id[section_id]
        if not bool(getattr(row, "complete", False)):
            blockers = "; ".join(
                str(value).strip()
                for value in tuple(getattr(row, "blockers", ()) or ())
                if str(value).strip()
            )
            raise ValueError(
                f"{section_id}: complete automatic thermal basis is required"
                + (f" — {blockers}" if blockers else "")
            )
        candidates.append(
            (
                section_id,
                build_explicit_bare_pipe_thermal_condition_basis_v1(
                    surface_temperature_C=getattr(
                        row, "surface_temperature_C", None
                    ),
                    ambient_air_temperature_C=getattr(
                        row, "ambient_air_temperature_C", None
                    ),
                    mean_radiant_temperature_C=getattr(
                        row, "mean_radiant_temperature_C", None
                    ),
                    emissivity=getattr(row, "emissivity", None),
                    external_convection_coefficient_W_m2K=getattr(
                        row,
                        "external_convection_coefficient_W_m2K",
                        None,
                    ),
                ),
            )
        )

    replacement = CommittedPipeSectionThermalConditionBasisIntentV1.from_dict(
        source_intent.to_dict()
    )
    for section_id, thermal_basis in candidates:
        replacement.set_section_basis(
            section_id=section_id,
            committed_schedule_fingerprint=fingerprint,
            thermal_basis=thermal_basis,
            emissivity_override=None,
        )

    if set(replacement.basis_by_section_id) != set(section_ids):
        raise ValueError(
            "Atomic automatic thermal-basis acceptance did not complete the "
            "exact committed schedule"
        )
    return CommittedPipeAutomaticThermalBasisBulkAcceptanceV1(
        intent=replacement,
        section_count=len(section_ids),
        preserved_section_count=len(existing_ids),
        added_section_count=len(candidates),
        status=(
            f"Ready — preserved {len(existing_ids)} and accepted "
            f"{len(candidates)} missing automatic section basis/bases"
        ),
    )
