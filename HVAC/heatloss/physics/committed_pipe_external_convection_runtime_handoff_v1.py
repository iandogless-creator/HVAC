# ======================================================================
# H-S66-N2D — Committed pipe external-convection runtime handoff
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    CommittedFlowReturnPairingTemperatureEvidenceV1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.heatloss.physics.committed_pipe_pair_spacing_override_intent_v1 import (
    EffectiveCommittedPipePairSpacingV1,
)
from HVAC.heatloss.physics.isolated_horizontal_pipe_natural_convection_v1 import (
    build_isolated_horizontal_pipe_natural_convection_v1,
)
from HVAC.heatloss.physics.normal_support_spacing_stacked_pipe_convection_resolver_v1 import (
    resolve_normal_support_spacing_stacked_pipe_convection_v1,
)


@dataclass(frozen=True, slots=True)
class CommittedPipeExternalConvectionRuntimeRowV1:
    """Per-pipe evidence plus the scalar required by H-S66-J."""

    section_id: str
    external_arrangement: str
    flow_pipe_surface_temperature_C: float
    return_pipe_surface_temperature_C: float
    mean_surface_temperature_C: float
    ambient_air_temperature_C: float
    ambient_air_temperature_source: str
    flow_pipe_external_convection_coefficient_W_m2K: float
    return_pipe_external_convection_coefficient_W_m2K: float
    effective_external_convection_coefficient_W_m2K: float
    effective_coefficient_basis: str
    conservative_fallback: bool
    source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedPipeExternalConvectionRuntimeHandoffV1:
    schema: str = "committed_pipe_external_convection_runtime_handoff_v1"
    ready: bool = False
    sections: tuple[CommittedPipeExternalConvectionRuntimeRowV1, ...] = ()
    section_count: int = 0
    stacked_section_count: int = 0
    separate_section_count: int = 0
    status: str = "Committed pipe external-convection handoff not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Retains individual flow/return convection coefficients. The scalar "
        "handed to H-S66-J preserves average per-pipe convection heat flux "
        "at the arithmetic mean surface temperature; it is not a total-pair "
        "area multiplier. Ta is the local air temperature surrounding the "
        "pipe and is intended to become section-resolved Tai; it is distinct "
        "from mean radiant temperature. No persistence, space mapping or "
        "heat-loss calculation occurs."
    )


def build_committed_pipe_external_convection_runtime_handoff_v1(
        *,
        pairing_evidence: CommittedFlowReturnPairingTemperatureEvidenceV1,
        effective_spacing_by_section_id: Mapping[
            str, EffectiveCommittedPipePairSpacingV1
        ],
        ambient_air_temperature_C: object,
        pressure_Pa: object,
        ambient_air_temperature_source: object = (
            "Runtime local ambient-air input — future section-resolved Tai"
        ),
) -> CommittedPipeExternalConvectionRuntimeHandoffV1:
    """Resolve separate/stacked coefficients and form H-S66-J evidence."""

    if not isinstance(
        pairing_evidence,
        CommittedFlowReturnPairingTemperatureEvidenceV1,
    ):
        return _blocked_v1(
            "Committed flow/return pairing temperature evidence is required"
        )
    blockers: list[str] = []
    if not pairing_evidence.ready:
        blockers.extend(
            pairing_evidence.blockers
            or ("Committed flow/return pairing evidence is not ready",)
        )
    try:
        ambient_C = _finite_v1(
            ambient_air_temperature_C, "Ambient air temperature"
        )
        pressure = _positive_finite_v1(pressure_Pa, "Dry-air pressure")
        ambient_source = _text_v1(ambient_air_temperature_source)
        if not ambient_source:
            raise ValueError("Ambient air temperature source is required")
    except ValueError as exc:
        blockers.append(str(exc))
        ambient_C = pressure = math.nan
        ambient_source = ""

    if not isinstance(effective_spacing_by_section_id, Mapping):
        blockers.append("Effective stacked-pair spacing mapping is required")
        spacing_by_id: dict[str, object] = {}
    else:
        spacing_by_id = {}
        for raw_section_id, spacing in effective_spacing_by_section_id.items():
            section_id = _text_v1(raw_section_id)
            if not section_id or section_id != raw_section_id:
                blockers.append(
                    "Every effective spacing entry requires canonical section_id"
                )
            elif section_id in spacing_by_id:
                blockers.append(f"Duplicate effective spacing identity: {section_id}")
            else:
                spacing_by_id[section_id] = spacing

    rows_by_id: dict[str, object] = {}
    for row in tuple(pairing_evidence.sections or ()):
        section_id = _text_v1(getattr(row, "section_id", ""))
        if not section_id:
            blockers.append("Every pairing row requires section_id")
        elif section_id in rows_by_id:
            blockers.append(f"Duplicate pairing section identity: {section_id}")
        else:
            rows_by_id[section_id] = row
    if not rows_by_id:
        blockers.append("Committed flow/return pairing rows are required")

    stacked_ids = {
        section_id
        for section_id, row in rows_by_id.items()
        if getattr(row, "external_arrangement", "")
        == STACKED_FLOW_RETURN_PAIR_V1
    }
    separate_ids = {
        section_id
        for section_id, row in rows_by_id.items()
        if getattr(row, "external_arrangement", "") == SEPARATE_PIPE_V1
    }
    unsupported_ids = set(rows_by_id) - stacked_ids - separate_ids
    for section_id in sorted(unsupported_ids):
        blockers.append(f"{section_id}: committed external arrangement is unsupported")
    for section_id in sorted(stacked_ids - set(spacing_by_id)):
        blockers.append(f"{section_id}: effective stacked-pair spacing is required")
    for section_id in sorted(set(spacing_by_id) - stacked_ids):
        if section_id in separate_ids:
            blockers.append(
                f"{section_id}: stacked-pair spacing must remain dormant for "
                "separate pipework"
            )
        else:
            blockers.append(
                f"{section_id}: effective spacing has no committed stacked section"
            )
    if blockers:
        return _blocked_v1(*blockers)

    resolved: list[CommittedPipeExternalConvectionRuntimeRowV1] = []
    for section_id, pairing_row in rows_by_id.items():
        try:
            flow_C = _finite_v1(
                getattr(pairing_row, "flow_pipe_surface_temperature_C", None),
                "Flow-pipe surface temperature",
            )
            return_C = _finite_v1(
                getattr(pairing_row, "return_pipe_surface_temperature_C", None),
                "Return-pipe surface temperature",
            )
            diameter_mm = _positive_finite_v1(
                getattr(pairing_row, "actual_outside_diameter_mm", None),
                "Exact pipe outside diameter",
            )
            if flow_C <= ambient_C or return_C <= ambient_C:
                raise ValueError(
                    "Both flow and return pipe surfaces must be above ambient"
                )

            arrangement = str(pairing_row.external_arrangement)
            conservative = False
            if arrangement == STACKED_FLOW_RETURN_PAIR_V1:
                stacked = (
                    resolve_normal_support_spacing_stacked_pipe_convection_v1(
                        pairing_row=pairing_row,
                        effective_spacing=spacing_by_id[section_id],
                        ambient_air_temperature_C=ambient_C,
                        pressure_Pa=pressure,
                    )
                )
                if not stacked.ready:
                    raise ValueError(
                        "; ".join(stacked.blockers or (stacked.status,))
                    )
                flow_h = _positive_finite_v1(
                    stacked.flow_pipe_external_convection_coefficient_W_m2K,
                    "Resolved flow-pipe convection coefficient",
                )
                return_h = _positive_finite_v1(
                    stacked.return_pipe_external_convection_coefficient_W_m2K,
                    "Resolved return-pipe convection coefficient",
                )
                conservative = bool(stacked.conservative_fallback)
                source = f"Stacked pair — {stacked.source}"
            else:
                flow_isolated = (
                    build_isolated_horizontal_pipe_natural_convection_v1(
                        outer_diameter_m=diameter_mm / 1000.0,
                        surface_temperature_C=flow_C,
                        ambient_air_temperature_C=ambient_C,
                        pressure_Pa=pressure,
                    )
                )
                return_isolated = (
                    build_isolated_horizontal_pipe_natural_convection_v1(
                        outer_diameter_m=diameter_mm / 1000.0,
                        surface_temperature_C=return_C,
                        ambient_air_temperature_C=ambient_C,
                        pressure_Pa=pressure,
                    )
                )
                flow_h = flow_isolated.external_convection_coefficient_W_m2K
                return_h = (
                    return_isolated.external_convection_coefficient_W_m2K
                )
                source = (
                    "Separate pipework — individual N2A isolated horizontal-"
                    "cylinder natural-convection coefficients"
                )

            mean_C = 0.5 * (flow_C + return_C)
            mean_excess_K = mean_C - ambient_C
            if mean_excess_K <= 0.0:
                raise ValueError(
                    "Mean flow/return pipe surface temperature must exceed ambient"
                )
            effective_h = (
                flow_h * (flow_C - ambient_C)
                + return_h * (return_C - ambient_C)
            ) / (2.0 * mean_excess_K)
            resolved.append(
                CommittedPipeExternalConvectionRuntimeRowV1(
                    section_id=section_id,
                    external_arrangement=arrangement,
                    flow_pipe_surface_temperature_C=flow_C,
                    return_pipe_surface_temperature_C=return_C,
                    mean_surface_temperature_C=mean_C,
                    ambient_air_temperature_C=ambient_C,
                    ambient_air_temperature_source=ambient_source,
                    flow_pipe_external_convection_coefficient_W_m2K=flow_h,
                    return_pipe_external_convection_coefficient_W_m2K=return_h,
                    effective_external_convection_coefficient_W_m2K=effective_h,
                    effective_coefficient_basis=(
                        "Arithmetic per-pipe convection heat-flux equivalent "
                        "at mean flow/return surface temperature"
                    ),
                    conservative_fallback=conservative,
                    source=source,
                    ready=True,
                    status=(
                        "Ready — external convection resolved for automatic "
                        "committed-section thermal basis"
                    ),
                )
            )
        except (TypeError, ValueError) as exc:
            blockers.append(f"{section_id}: {exc}")

    clean = _unique_v1(blockers)
    if clean:
        return _blocked_v1(*clean)
    ordered = tuple(sorted(resolved, key=lambda row: row.section_id))
    return CommittedPipeExternalConvectionRuntimeHandoffV1(
        ready=True,
        sections=ordered,
        section_count=len(ordered),
        stacked_section_count=sum(
            row.external_arrangement == STACKED_FLOW_RETURN_PAIR_V1
            for row in ordered
        ),
        separate_section_count=sum(
            row.external_arrangement == SEPARATE_PIPE_V1 for row in ordered
        ),
        status=(
            "Ready — separate/stacked external convection handed to the "
            "automatic committed-section thermal-basis resolver"
        ),
        blockers=(),
    )


def external_convection_mapping_from_runtime_handoff_v1(
        handoff: CommittedPipeExternalConvectionRuntimeHandoffV1,
) -> dict[str, CommittedPipeExternalConvectionRuntimeRowV1]:
    """Return an exact section mapping only from a ready N2D handoff."""

    if not isinstance(handoff, CommittedPipeExternalConvectionRuntimeHandoffV1):
        raise TypeError("CommittedPipeExternalConvectionRuntimeHandoffV1 required")
    if not handoff.ready:
        raise ValueError("Ready committed external-convection handoff required")
    mapping = {row.section_id: row for row in handoff.sections}
    if len(mapping) != len(handoff.sections):
        raise ValueError("Duplicate committed external-convection section identity")
    return mapping


def _blocked_v1(*blockers: str) -> CommittedPipeExternalConvectionRuntimeHandoffV1:
    clean = _unique_v1(blockers)
    return CommittedPipeExternalConvectionRuntimeHandoffV1(
        ready=False,
        sections=(),
        section_count=0,
        stacked_section_count=0,
        separate_section_count=0,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _finite_v1(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be numeric") from None
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _positive_finite_v1(value: object, label: str) -> float:
    number = _finite_v1(value, label)
    if number <= 0.0:
        raise ValueError(f"{label} must be positive")
    return number


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: object) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_text_v1(value) for value in values if _text_v1(value)))
