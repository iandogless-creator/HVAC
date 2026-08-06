# ======================================================================
# H-S66-N2C1 — Normal-support-spacing stacked-pipe convection resolver
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    CommittedFlowReturnPairingTemperatureRowV1,
    FLOW_PIPE_V1,
    RETURN_PIPE_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.heatloss.physics.committed_pipe_pair_spacing_override_intent_v1 import (
    EffectiveCommittedPipePairSpacingV1,
)
from HVAC.heatloss.physics.isolated_horizontal_pipe_natural_convection_v1 import (
    build_isolated_horizontal_pipe_natural_convection_v1,
)
from HVAC.heatloss.physics.stacked_pipe_pair_external_convection_correction_v1 import (
    StackedPipePairExternalConvectionCorrectionV1,
    build_stacked_pipe_pair_external_convection_correction_v1,
)


SCHEMA_V1 = "normal_support_spacing_stacked_pipe_convection_resolver_v1"
EMPIRICAL_N2C_METHOD_V1 = "bounded_n2c_empirical_correction"
CONSERVATIVE_ISOLATED_METHOD_V1 = "conservative_isolated_cylinder_envelope"
MIN_NORMAL_SUPPORT_SPACING_RATIO_V1 = 1.5
MAX_NORMAL_SUPPORT_SPACING_RATIO_V1 = 3.0
CONSERVATIVE_SOURCE_V1 = (
    "N2A isolated horizontal-cylinder coefficients retained without stacked "
    "interaction credit inside the normal support-spacing envelope"
)


@dataclass(frozen=True, slots=True)
class NormalSupportSpacingStackedPipeConvectionV1:
    schema: str = SCHEMA_V1
    ready: bool = False
    section_id: str = ""
    resolution_method: str = ""
    conservative_fallback: bool = False
    upper_pipe_role: str = ""
    lower_pipe_role: str = ""
    upper_surface_temperature_C: float | None = None
    lower_surface_temperature_C: float | None = None
    ambient_air_temperature_C: float | None = None
    outside_diameter_mm: float | None = None
    centre_spacing_mm: float | None = None
    spacing_to_diameter_ratio: float | None = None
    upper_pipe_correction_factor: float | None = None
    lower_pipe_correction_factor: float | None = None
    upper_pipe_external_convection_coefficient_W_m2K: float | None = None
    lower_pipe_external_convection_coefficient_W_m2K: float | None = None
    flow_pipe_external_convection_coefficient_W_m2K: float | None = None
    return_pipe_external_convection_coefficient_W_m2K: float | None = None
    source: str = ""
    empirical_correction_blockers: tuple[str, ...] = ()
    status: str = "Normal-support-spacing stacked convection not ready"
    blockers: tuple[str, ...] = ()


def resolve_normal_support_spacing_stacked_pipe_convection_v1(
        *,
        pairing_row: CommittedFlowReturnPairingTemperatureRowV1,
        effective_spacing: EffectiveCommittedPipePairSpacingV1,
        ambient_air_temperature_C: object,
        pressure_Pa: object,
) -> NormalSupportSpacingStackedPipeConvectionV1:
    """Resolve N2C where valid, otherwise retain conservative N2A values.

    The fallback is a design envelope, not an empirical plume-interaction
    prediction.  It intentionally takes no heat-loss reduction credit.
    """

    empirical = build_stacked_pipe_pair_external_convection_correction_v1(
        pairing_row=pairing_row,
        effective_spacing=effective_spacing,
        ambient_air_temperature_C=ambient_air_temperature_C,
        pressure_Pa=pressure_Pa,
    )
    if empirical.ready:
        return _from_empirical_n2c_v1(empirical)

    blockers: list[str] = []
    if not isinstance(pairing_row, CommittedFlowReturnPairingTemperatureRowV1):
        return _blocked_v1("Committed flow/return pairing row is required")
    if not isinstance(effective_spacing, EffectiveCommittedPipePairSpacingV1):
        return _blocked_v1("Effective committed pipe-pair spacing is required")

    section_id = _text_v1(pairing_row.section_id)
    if not section_id:
        blockers.append("Exact committed section identity is required")
    if not pairing_row.ready:
        blockers.append(f"{section_id}: committed pairing evidence is not ready")
    if not pairing_row.paired or pairing_row.external_arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        blockers.append(f"{section_id}: committed stacked flow/return pair is required")
    if _text_v1(effective_spacing.section_id) != section_id:
        blockers.append(f"{section_id}: effective spacing belongs to another section")
    if effective_spacing.external_arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        blockers.append(f"{section_id}: effective spacing is not for stacked pipework")

    upper_role = _text_v1(pairing_row.upper_pipe_role)
    lower_role = _text_v1(pairing_row.lower_pipe_role)
    if {upper_role, lower_role} != {FLOW_PIPE_V1, RETURN_PIPE_V1}:
        blockers.append(f"{section_id}: one explicit upper and lower pipe role is required")

    try:
        diameter_mm = _positive_finite_v1(
            pairing_row.actual_outside_diameter_mm, "outside diameter"
        )
        spacing_mm = _positive_finite_v1(
            effective_spacing.centre_spacing_mm, "centre spacing"
        )
        spacing_diameter_mm = _positive_finite_v1(
            effective_spacing.actual_outside_diameter_mm,
            "spacing-evidence outside diameter",
        )
        ambient_C = _finite_v1(ambient_air_temperature_C, "ambient temperature")
        pressure = _positive_finite_v1(pressure_Pa, "air pressure")
        flow_C = _finite_v1(
            pairing_row.flow_pipe_surface_temperature_C,
            "flow-pipe surface temperature",
        )
        return_C = _finite_v1(
            pairing_row.return_pipe_surface_temperature_C,
            "return-pipe surface temperature",
        )
    except ValueError as exc:
        blockers.append(f"{section_id}: {exc}")
        diameter_mm = spacing_mm = spacing_diameter_mm = pressure = math.nan
        ambient_C = flow_C = return_C = math.nan

    if not blockers and not math.isclose(
        diameter_mm, spacing_diameter_mm, rel_tol=0.0, abs_tol=1.0e-9
    ):
        blockers.append(f"{section_id}: pairing and spacing pipe diameters disagree")

    spacing_ratio = spacing_mm / diameter_mm if diameter_mm > 0.0 else math.nan
    if not blockers and not (
        MIN_NORMAL_SUPPORT_SPACING_RATIO_V1
        <= spacing_ratio
        <= MAX_NORMAL_SUPPORT_SPACING_RATIO_V1
    ):
        blockers.append(
            f"{section_id}: spacing ratio S/D={spacing_ratio:.6g} is outside "
            "the normal support-spacing envelope 1.5–3.0"
        )

    upper_C = flow_C if upper_role == FLOW_PIPE_V1 else return_C
    lower_C = flow_C if lower_role == FLOW_PIPE_V1 else return_C
    if not blockers and (upper_C <= ambient_C or lower_C <= ambient_C):
        blockers.append(
            f"{section_id}: conservative v1 resolution requires both pipe "
            "surfaces above ambient"
        )
    if blockers:
        return _blocked_v1(
            *blockers,
            section_id=section_id,
            empirical_blockers=empirical.blockers,
        )

    try:
        upper_isolated = build_isolated_horizontal_pipe_natural_convection_v1(
            outer_diameter_m=diameter_mm / 1000.0,
            surface_temperature_C=upper_C,
            ambient_air_temperature_C=ambient_C,
            pressure_Pa=pressure,
        )
        lower_isolated = build_isolated_horizontal_pipe_natural_convection_v1(
            outer_diameter_m=diameter_mm / 1000.0,
            surface_temperature_C=lower_C,
            ambient_air_temperature_C=ambient_C,
            pressure_Pa=pressure,
        )
    except (TypeError, ValueError) as exc:
        return _blocked_v1(
            f"{section_id}: {exc}",
            section_id=section_id,
            empirical_blockers=empirical.blockers,
        )

    upper_h = upper_isolated.external_convection_coefficient_W_m2K
    lower_h = lower_isolated.external_convection_coefficient_W_m2K
    if upper_role == FLOW_PIPE_V1:
        flow_h, return_h = upper_h, lower_h
    else:
        flow_h, return_h = lower_h, upper_h

    return NormalSupportSpacingStackedPipeConvectionV1(
        ready=True,
        section_id=section_id,
        resolution_method=CONSERVATIVE_ISOLATED_METHOD_V1,
        conservative_fallback=True,
        upper_pipe_role=upper_role,
        lower_pipe_role=lower_role,
        upper_surface_temperature_C=upper_C,
        lower_surface_temperature_C=lower_C,
        ambient_air_temperature_C=ambient_C,
        outside_diameter_mm=diameter_mm,
        centre_spacing_mm=spacing_mm,
        spacing_to_diameter_ratio=spacing_ratio,
        upper_pipe_correction_factor=1.0,
        lower_pipe_correction_factor=1.0,
        upper_pipe_external_convection_coefficient_W_m2K=upper_h,
        lower_pipe_external_convection_coefficient_W_m2K=lower_h,
        flow_pipe_external_convection_coefficient_W_m2K=flow_h,
        return_pipe_external_convection_coefficient_W_m2K=return_h,
        source=CONSERVATIVE_SOURCE_V1,
        empirical_correction_blockers=empirical.blockers,
        status=(
            "Calculated — conservative normal-support-spacing envelope; "
            "individual isolated-cylinder coefficients retained and no "
            "stacked interaction reduction credited"
        ),
        blockers=(),
    )


def _from_empirical_n2c_v1(
        value: StackedPipePairExternalConvectionCorrectionV1,
) -> NormalSupportSpacingStackedPipeConvectionV1:
    return NormalSupportSpacingStackedPipeConvectionV1(
        ready=True,
        section_id=value.section_id,
        resolution_method=EMPIRICAL_N2C_METHOD_V1,
        conservative_fallback=False,
        upper_pipe_role=value.upper_pipe_role,
        lower_pipe_role=value.lower_pipe_role,
        upper_surface_temperature_C=value.upper_surface_temperature_C,
        lower_surface_temperature_C=value.lower_surface_temperature_C,
        ambient_air_temperature_C=value.ambient_air_temperature_C,
        outside_diameter_mm=value.outside_diameter_mm,
        centre_spacing_mm=value.centre_spacing_mm,
        spacing_to_diameter_ratio=value.spacing_to_diameter_ratio,
        upper_pipe_correction_factor=value.upper_pipe_correction_factor,
        lower_pipe_correction_factor=1.0,
        upper_pipe_external_convection_coefficient_W_m2K=(
            value.upper_pipe_corrected_coefficient_W_m2K
        ),
        lower_pipe_external_convection_coefficient_W_m2K=(
            value.lower_pipe_corrected_coefficient_W_m2K
        ),
        flow_pipe_external_convection_coefficient_W_m2K=(
            value.flow_pipe_external_convection_coefficient_W_m2K
        ),
        return_pipe_external_convection_coefficient_W_m2K=(
            value.return_pipe_external_convection_coefficient_W_m2K
        ),
        source=value.source,
        empirical_correction_blockers=(),
        status=value.status,
        blockers=(),
    )


def _blocked_v1(
        *blockers: str,
        section_id: str = "",
        empirical_blockers: tuple[str, ...] = (),
) -> NormalSupportSpacingStackedPipeConvectionV1:
    clean = tuple(dict.fromkeys(_text_v1(value) for value in blockers if _text_v1(value)))
    return NormalSupportSpacingStackedPipeConvectionV1(
        ready=False,
        section_id=_text_v1(section_id),
        empirical_correction_blockers=tuple(empirical_blockers or ()),
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
