# ======================================================================
# H-S66-J — Automatic committed-section bare-pipe thermal-basis resolver
# ======================================================================

from __future__ import annotations

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
    * External convection is not inferred until an orientation/correlation
      authority exists.

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
        blockers.append(
            "External convection coefficient requires explicit review"
        )
        resolved.append(
            AutomaticCommittedPipeSectionThermalBasisV1(
                section_id=section_id,
                surface_temperature_C=mean_water_temperature_C,
                ambient_air_temperature_C=internal_temperature_C,
                mean_radiant_temperature_C=internal_temperature_C,
                emissivity=effective_emissivity,
                external_convection_coefficient_W_m2K=None,
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
                external_convection_source=(
                    "Explicit value required — no orientation/correlation "
                    "authority"
                ),
                complete=False,
                status=(
                    "Partial — automatic Environment preview; external "
                    "convection requires explicit review"
                    if effective_emissivity is not None
                    else (
                        "Partial — automatic temperature preview; universal "
                        "emissivity and external convection are unresolved"
                    )
                ),
                blockers=tuple(blockers),
            )
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
