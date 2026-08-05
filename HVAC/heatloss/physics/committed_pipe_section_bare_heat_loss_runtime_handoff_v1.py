# ======================================================================
# H-S66-G — Runtime handoff into committed pipe-section heat-loss evidence
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.heatloss.physics.committed_pipe_section_bare_heat_loss_evidence_v1 import (
    CommittedPipeSectionBareHeatLossEvidenceV1,
    build_committed_pipe_section_bare_heat_loss_evidence_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    CommittedPipeSectionThermalConditionBasisEntryV1,
    CommittedPipeSectionThermalConditionBasisIntentV1,
    build_committed_pipe_schedule_thermal_fingerprint_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionBareHeatLossRuntimeHandoffV1:
    """Freshness-gated runtime handoff; no persistence or mutation."""

    schema: str = (
        "committed_pipe_section_bare_heat_loss_runtime_handoff_v1"
    )
    ready: bool = False
    evidence: CommittedPipeSectionBareHeatLossEvidenceV1 | None = None
    current_schedule_fingerprint: str = ""
    persisted_schedule_fingerprint: str = ""
    section_count: int = 0
    status: str = "Committed pipe-section heat-loss handoff not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Fresh persisted section thermal bases delegated to H-S66-E only — "
        "no ProjectState mutation, GUI authority, insulation, temperature "
        "decay or hydraulic change."
    )


def build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        thermal_basis_intent: (
            CommittedPipeSectionThermalConditionBasisIntentV1 | None
        ),
) -> CommittedPipeSectionBareHeatLossRuntimeHandoffV1:
    """Resolve fresh persisted intent and delegate calculation to H-S66-E."""

    try:
        current_fingerprint = (
            build_committed_pipe_schedule_thermal_fingerprint_v1(
                committed_authority
            )
        )
    except (TypeError, ValueError) as exc:
        return _blocked_v1(str(exc))

    if not isinstance(
        thermal_basis_intent,
        CommittedPipeSectionThermalConditionBasisIntentV1,
    ):
        return _blocked_v1(
            "Persisted committed-section thermal-condition basis intent "
            "is required",
            current_schedule_fingerprint=current_fingerprint,
        )

    persisted_fingerprint = str(
        thermal_basis_intent.committed_schedule_fingerprint or ""
    ).strip()
    if not persisted_fingerprint:
        return _blocked_v1(
            "Persisted committed pipe schedule fingerprint is required",
            current_schedule_fingerprint=current_fingerprint,
        )
    if persisted_fingerprint != current_fingerprint:
        return _blocked_v1(
            "Persisted committed-section thermal-condition basis fingerprint "
            "is stale",
            current_schedule_fingerprint=current_fingerprint,
            persisted_schedule_fingerprint=persisted_fingerprint,
        )

    blockers: list[str] = []
    basis_by_section_id = {}
    for section_id, entry in sorted(
        thermal_basis_intent.basis_by_section_id.items(),
        key=lambda item: str(item[0]),
    ):
        stable_section_id = str(section_id or "").strip()
        if not isinstance(
            entry,
            CommittedPipeSectionThermalConditionBasisEntryV1,
        ):
            blockers.append(
                f"{stable_section_id or '—'}: persisted section thermal "
                "basis entry is invalid"
            )
            continue
        entry_section_id = str(entry.section_id or "").strip()
        if not stable_section_id or stable_section_id != entry_section_id:
            blockers.append(
                f"{stable_section_id or '—'}: persisted section thermal "
                "basis identity mismatch"
            )
            continue
        try:
            basis_by_section_id[stable_section_id] = entry.to_thermal_basis()
        except (TypeError, ValueError) as exc:
            blockers.append(f"{stable_section_id}: {exc}")

    clean_blockers = _unique_v1(blockers)
    if clean_blockers:
        return _blocked_v1(
            *clean_blockers,
            current_schedule_fingerprint=current_fingerprint,
            persisted_schedule_fingerprint=persisted_fingerprint,
        )

    evidence = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=committed_authority,
        thermal_basis_by_section_id=basis_by_section_id,
    )
    if not evidence.ready:
        return _blocked_v1(
            *(evidence.blockers or (evidence.status,)),
            current_schedule_fingerprint=current_fingerprint,
            persisted_schedule_fingerprint=persisted_fingerprint,
        )

    return CommittedPipeSectionBareHeatLossRuntimeHandoffV1(
        ready=True,
        evidence=evidence,
        current_schedule_fingerprint=current_fingerprint,
        persisted_schedule_fingerprint=persisted_fingerprint,
        section_count=evidence.section_count,
        status=(
            "Ready — fresh persisted section thermal bases handed to "
            "H-S66-E"
        ),
        blockers=(),
    )


def _blocked_v1(
        *blockers: str,
        current_schedule_fingerprint: str = "",
        persisted_schedule_fingerprint: str = "",
) -> CommittedPipeSectionBareHeatLossRuntimeHandoffV1:
    clean = _unique_v1(blockers)
    return CommittedPipeSectionBareHeatLossRuntimeHandoffV1(
        ready=False,
        evidence=None,
        current_schedule_fingerprint=current_schedule_fingerprint,
        persisted_schedule_fingerprint=persisted_schedule_fingerprint,
        section_count=0,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _unique_v1(values: object) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)
