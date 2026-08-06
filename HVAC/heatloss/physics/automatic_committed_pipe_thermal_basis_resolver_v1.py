# ======================================================================
# H-S66-J — Automatic committed-section bare-pipe thermal-basis resolver
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True, slots=True)
class AutomaticCommittedPipeSectionThermalBasisV1:
    """Resolved or partially resolved conditions for one committed section.

    A row is calculation-ready only when every value is present.  Automatically
    derived values remain preview evidence until H-S66-I explicitly persists
    the complete basis through H-S66-F.
    """

    section_id: str
    surface_temperature_C: float | None
    ambient_air_temperature_C: float | None
    mean_radiant_temperature_C: float | None
    emissivity: float | None
    external_convection_coefficient_W_m2K: float | None
    surface_temperature_source: str
    ambient_air_temperature_source: str
    mean_radiant_temperature_source: str
    emissivity_source: str
    external_convection_source: str
    complete: bool
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AutomaticCommittedPipeThermalBasisResolutionV1:
    """Non-mutating automatic/override resolution for one exact schedule."""

    ready: bool
    sections: tuple[AutomaticCommittedPipeSectionThermalBasisV1, ...]
    section_count: int
    complete_section_count: int
    status: str
    blockers: tuple[str, ...]


def build_automatic_committed_pipe_thermal_basis_resolution_v1(
        *,
        committed_authority: Any,
        committed_schedule_fingerprint: str,
        design_flow_temperature_C: object,
        design_return_temperature_C: object,
        default_internal_temperature_C: object,
        default_pipe_emissivity: object = None,
        thermal_basis_intent: Any = None,
        external_convection_by_section_id: Mapping[str, object] | None = None,
) -> AutomaticCommittedPipeThermalBasisResolutionV1:
    """Resolve defensible v1 values without silently committing assumptions.

    Automatic preview rules
    -----------------------
    * Surface temperature is the arithmetic design mean-water temperature.
      This is explicitly a no-temperature-decay approximation.
    * Ambient air uses the project Environment internal-temperature default.
    * MRT equals that same Environment value as an explicit v1 approximation.
    * Emissivity inherits the explicit Environment project default unless a
      fresh committed-section local override exists.
    * External convection remains unresolved unless exact fresh N2D runtime
      evidence is supplied for the committed section.

    A fresh H-S66-F manual entry has precedence over every automatic preview
    value.  This function performs no persistence and no heat-loss calculation.
    """

    authority_blockers: list[str] = []
    if not bool(getattr(committed_authority, "ready", False)):
        authority_blockers.append(
            "Committed proportioning hydraulic-input authority is not ready"
        )
    sections = tuple(getattr(committed_authority, "sections", ()) or ())
    if not sections:
        authority_blockers.append("Committed pipe sections are required")
    fingerprint = str(committed_schedule_fingerprint or "").strip()
    if not fingerprint:
        authority_blockers.append(
            "Committed pipe schedule thermal fingerprint is required"
        )

    mean_water_temperature_C, water_blocker = _mean_water_temperature_v1(
        design_flow_temperature_C,
        design_return_temperature_C,
    )
    internal_temperature_C, internal_blocker = _temperature_v1(
        default_internal_temperature_C,
        "Environment default internal temperature",
    )
    universal_emissivity, emissivity_blocker = _emissivity_v1(
        default_pipe_emissivity,
        "Environment universal bare-pipe emissivity",
    )

    stored_fingerprint = str(
        getattr(thermal_basis_intent, "committed_schedule_fingerprint", "")
        or ""
    ).strip()
    stale_manual = bool(
        stored_fingerprint and stored_fingerprint != fingerprint
    )
    manual_entries = (
        dict(getattr(thermal_basis_intent, "basis_by_section_id", {}) or {})
        if not stale_manual
        else {}
    )
    has_override_contract = hasattr(
        thermal_basis_intent, "emissivity_override_by_section_id"
    )
    emissivity_overrides = (
        dict(
            getattr(
                thermal_basis_intent,
                "emissivity_override_by_section_id",
                {},
            )
            or {}
        )
        if not stale_manual
        else {}
    )
    convection_by_id: dict[str, object] = {}
    if external_convection_by_section_id is not None:
        if not isinstance(external_convection_by_section_id, Mapping):
            authority_blockers.append(
                "Committed external-convection section mapping is required"
            )
        else:
            for raw_section_id, evidence in (
                external_convection_by_section_id.items()
            ):
                section_id = str(raw_section_id or "").strip()
                if not section_id or section_id != raw_section_id:
                    authority_blockers.append(
                        "Every external-convection entry requires canonical "
                        "section identity"
                    )
                elif section_id in convection_by_id:
                    authority_blockers.append(
                        f"Duplicate external-convection identity: {section_id}"
                    )
                else:
                    convection_by_id[section_id] = evidence

    resolved: list[AutomaticCommittedPipeSectionThermalBasisV1] = []
    seen: set[str] = set()
    for section in sections:
        section_id = str(getattr(section, "section_id", "") or "").strip()
        if not section_id:
            authority_blockers.append(
                "Every committed pipe section requires stable identity"
            )
            continue
        if section_id in seen:
            authority_blockers.append(
                f"Duplicate committed pipe section identity: {section_id}"
            )
            continue
        seen.add(section_id)
        manual = manual_entries.get(section_id)
        local_emissivity = emissivity_overrides.get(section_id)
        effective_emissivity = (
            float(local_emissivity)
            if local_emissivity is not None
            else universal_emissivity
        )
        emissivity_source = (
            "Committed-section local emissivity override"
            if local_emissivity is not None
            else (
                "Environment universal bare-pipe emissivity"
                if universal_emissivity is not None
                else "Unresolved"
            )
        )
        if manual is not None:
            if not has_override_contract and effective_emissivity is None:
                # Compatibility for pre-H-S66-K intent-like fixtures.
                effective_emissivity = float(
                    getattr(manual, "emissivity")
                )
                emissivity_source = "Legacy explicit H-S66-F emissivity"
            resolved.append(
                _manual_row_v1(
                    section_id,
                    manual,
                    emissivity=effective_emissivity,
                    emissivity_source=emissivity_source,
                    emissivity_blocker=emissivity_blocker,
                )
            )
            continue

        blockers: list[str] = []
        if water_blocker:
            blockers.append(water_blocker)
        if internal_blocker:
            blockers.append(internal_blocker)
        if effective_emissivity is None:
            blockers.append(emissivity_blocker)
        convection_evidence = convection_by_id.get(section_id)
        convection_coefficient = None
        convection_blockers: list[str] = []
        convection_source = (
            "Explicit value required — no orientation/correlation authority"
        )
        if convection_evidence is None:
            convection_blockers.append(
                "External convection coefficient requires explicit review"
            )
        else:
            evidence_section_id = str(
                getattr(convection_evidence, "section_id", "") or ""
            ).strip()
            if evidence_section_id != section_id:
                convection_blockers.append(
                    f"{section_id}: external-convection evidence identity "
                    "mismatch"
                )
            elif not bool(getattr(convection_evidence, "ready", False)):
                convection_blockers.append(
                    f"{section_id}: external-convection evidence is not ready"
                )
            else:
                try:
                    evidence_ambient_C = float(
                        getattr(
                            convection_evidence,
                            "ambient_air_temperature_C",
                        )
                    )
                    evidence_mean_surface_C = float(
                        getattr(
                            convection_evidence,
                            "mean_surface_temperature_C",
                        )
                    )
                except (TypeError, ValueError, AttributeError):
                    convection_blockers.append(
                        f"{section_id}: N2D ambient and mean surface "
                        "temperatures are required"
                    )
                else:
                    if (
                        internal_temperature_C is not None
                        and not math.isclose(
                            evidence_ambient_C,
                            internal_temperature_C,
                            rel_tol=0.0,
                            abs_tol=1.0e-9,
                        )
                    ):
                        convection_blockers.append(
                            f"{section_id}: N2D local ambient-air "
                            "temperature does not match this automatic "
                            "thermal-basis air temperature"
                        )
                    if (
                        mean_water_temperature_C is not None
                        and not math.isclose(
                            evidence_mean_surface_C,
                            mean_water_temperature_C,
                            rel_tol=0.0,
                            abs_tol=1.0e-9,
                        )
                    ):
                        convection_blockers.append(
                            f"{section_id}: N2D mean pipe-surface "
                            "temperature does not match this automatic "
                            "thermal-basis surface temperature"
                        )
                try:
                    candidate = float(
                        getattr(
                            convection_evidence,
                            "effective_external_convection_coefficient_W_m2K",
                        )
                    )
                except (TypeError, ValueError, AttributeError):
                    convection_blockers.append(
                        f"{section_id}: effective external-convection "
                        "coefficient is required"
                    )
                else:
                    if not math.isfinite(candidate) or candidate <= 0.0:
                        convection_blockers.append(
                            f"{section_id}: effective external-convection "
                            "coefficient must be positive and finite"
                        )
                    elif not convection_blockers:
                        # N2D is independent preview evidence.  Preserve its
                        # valid coefficient even while an unrelated thermal
                        # input (for example emissivity) remains unresolved.
                        convection_coefficient = candidate
                        convection_source = str(
                            getattr(convection_evidence, "source", "")
                            or "H-S66-N2D committed external-convection evidence"
                        )
        blockers.extend(convection_blockers)
        complete = bool(
            mean_water_temperature_C is not None
            and internal_temperature_C is not None
            and effective_emissivity is not None
            and convection_coefficient is not None
            and not blockers
        )
        resolved.append(
            AutomaticCommittedPipeSectionThermalBasisV1(
                section_id=section_id,
                surface_temperature_C=mean_water_temperature_C,
                ambient_air_temperature_C=internal_temperature_C,
                mean_radiant_temperature_C=internal_temperature_C,
                emissivity=effective_emissivity,
                external_convection_coefficient_W_m2K=(
                    convection_coefficient
                ),
                surface_temperature_source=(
                    "Environment design flow/return arithmetic mean — "
                    "no temperature decay"
                    if mean_water_temperature_C is not None
                    else "Unresolved"
                ),
                ambient_air_temperature_source=(
                    "Environment default internal temperature"
                    if internal_temperature_C is not None
                    else "Unresolved"
                ),
                mean_radiant_temperature_source=(
                    "Environment default internal temperature — "
                    "MRT equals air v1 approximation"
                    if internal_temperature_C is not None
                    else "Unresolved"
                ),
                emissivity_source=emissivity_source,
                external_convection_source=convection_source,
                complete=complete,
                status=_automatic_row_status_v1(
                    complete=complete,
                    convection_resolved=convection_coefficient is not None,
                    blockers=blockers,
                ),
                blockers=tuple(blockers),
            )
        )

    committed_ids = seen
    for section_id in sorted(set(convection_by_id) - committed_ids):
        authority_blockers.append(
            f"{section_id}: external-convection evidence has no committed "
            "section"
        )

    if stale_manual:
        authority_blockers.append(
            "Persisted committed-section thermal bases are stale"
        )
    clean_blockers = _unique_v1(authority_blockers)
    complete_count = sum(row.complete for row in resolved)
    ready = bool(resolved) and not clean_blockers
    status = (
        f"Ready — automatic thermal-basis preview for {len(resolved)} "
        f"section(s); {complete_count} complete"
        if ready
        else "Blocked — automatic committed-section thermal-basis resolution"
    )
    return AutomaticCommittedPipeThermalBasisResolutionV1(
        ready=ready,
        sections=tuple(resolved),
        section_count=len(resolved),
        complete_section_count=complete_count,
        status=status,
        blockers=clean_blockers,
    )


def _automatic_row_status_v1(
        *,
        complete: bool,
        convection_resolved: bool,
        blockers: list[str],
) -> str:
    if complete:
        return (
            "Ready — automatic Environment temperatures, effective "
            "emissivity and N2D external convection resolved"
        )
    blocker_text = "; ".join(_unique_v1(blockers)) or "Unresolved input"
    if convection_resolved:
        return (
            "Partial — N2D external convection resolved independently; "
            f"complete thermal basis blocked: {blocker_text}"
        )
    return f"Partial — external convection unresolved: {blocker_text}"


def _manual_row_v1(
        section_id: str,
        manual: Any,
        *,
        emissivity: float | None,
        emissivity_source: str,
        emissivity_blocker: str,
) -> AutomaticCommittedPipeSectionThermalBasisV1:
    values = (
        float(getattr(manual, "surface_temperature_C")),
        float(getattr(manual, "ambient_air_temperature_C")),
        float(getattr(manual, "mean_radiant_temperature_C")),
        float(getattr(manual, "external_convection_coefficient_W_m2K")),
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{section_id}: persisted thermal basis must be finite")
    return AutomaticCommittedPipeSectionThermalBasisV1(
        section_id=section_id,
        surface_temperature_C=values[0],
        ambient_air_temperature_C=values[1],
        mean_radiant_temperature_C=values[2],
        emissivity=emissivity,
        external_convection_coefficient_W_m2K=values[3],
        surface_temperature_source="Manual H-S66-F override",
        ambient_air_temperature_source="Manual H-S66-F override",
        mean_radiant_temperature_source="Manual H-S66-F override",
        emissivity_source=emissivity_source,
        external_convection_source="Manual H-S66-F override",
        complete=emissivity is not None,
        status=(
            "Ready — fresh H-S66-F basis with effective emissivity"
            if emissivity is not None
            else "Partial — fresh H-S66-F basis; emissivity unresolved"
        ),
        blockers=() if emissivity is not None else (emissivity_blocker,),
    )


def _mean_water_temperature_v1(
        flow_value: object,
        return_value: object,
) -> tuple[float | None, str]:
    flow, flow_blocker = _temperature_v1(
        flow_value, "Hydronic design flow temperature"
    )
    ret, return_blocker = _temperature_v1(
        return_value, "Hydronic design return temperature"
    )
    if flow_blocker or return_blocker:
        return None, flow_blocker or return_blocker
    if flow is None or ret is None or flow <= ret:
        return None, "Hydronic design flow temperature must exceed return"
    return (flow + ret) / 2.0, ""


def _temperature_v1(
        value: object,
        label: str,
) -> tuple[float | None, str]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label} is required"
    if not math.isfinite(number) or number <= -273.15:
        return None, f"{label} is invalid"
    return number, ""


def _emissivity_v1(
        value: object,
        label: str,
) -> tuple[float | None, str]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label} is required"
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        return None, f"{label} must be between 0 and 1"
    return number, ""


def _unique_v1(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
