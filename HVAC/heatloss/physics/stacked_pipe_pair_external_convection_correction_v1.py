# ======================================================================
# H-S66-N2C — Deterministic stacked-pair external-convection correction
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    CommittedFlowReturnPairingTemperatureRowV1,
    FLOW_PIPE_V1,
    RETURN_PIPE_V1,
    UPPER_POSITION_V1,
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


SCHEMA_V1 = "stacked_pipe_pair_external_convection_correction_v1"
SOURCE_V1 = (
    "Sparrow-Niethammer experiment as reproduced by Foroushani, Naylor and "
    "Wright (2015), Table 1: S/D=2, Ra_upper=1e5, Pr=0.7"
)
MIN_TEMPERATURE_EXCESS_RATIO_V1 = 0.5
MAX_TEMPERATURE_EXCESS_RATIO_V1 = 2.0
SOURCE_SPACING_RATIO_V1 = 2.0
SOURCE_UPPER_RAYLEIGH_V1 = 1.0e5
RAYLEIGH_RELATIVE_TOLERANCE_V1 = 0.005
PRANDTL_MIN_V1 = 0.68
PRANDTL_MAX_V1 = 0.72

# Experimental upper-cylinder Nu/Nu_isolated values at Ra=1e5.
_UPPER_CORRECTION_ANCHORS_V1 = (
    (0.5, 0.98),
    (1.0, 0.86),
    (2.0, 0.39),
)


@dataclass(frozen=True, slots=True)
class StackedPipePairExternalConvectionCorrectionV1:
    schema: str = SCHEMA_V1
    ready: bool = False
    section_id: str = ""
    upper_pipe_role: str = ""
    lower_pipe_role: str = ""
    upper_surface_temperature_C: float | None = None
    lower_surface_temperature_C: float | None = None
    ambient_air_temperature_C: float | None = None
    outside_diameter_mm: float | None = None
    centre_spacing_mm: float | None = None
    spacing_to_diameter_ratio: float | None = None
    lower_to_upper_temperature_excess_ratio: float | None = None
    upper_pipe_rayleigh_number: float | None = None
    upper_pipe_prandtl_number: float | None = None
    upper_pipe_isolated_coefficient_W_m2K: float | None = None
    lower_pipe_isolated_coefficient_W_m2K: float | None = None
    upper_pipe_correction_factor: float | None = None
    upper_pipe_corrected_coefficient_W_m2K: float | None = None
    lower_pipe_corrected_coefficient_W_m2K: float | None = None
    flow_pipe_external_convection_coefficient_W_m2K: float | None = None
    return_pipe_external_convection_coefficient_W_m2K: float | None = None
    source: str = SOURCE_V1
    status: str = "Stacked-pair external convection not ready"
    blockers: tuple[str, ...] = ()


def build_stacked_pipe_pair_external_convection_correction_v1(
        *,
        pairing_row: CommittedFlowReturnPairingTemperatureRowV1,
        effective_spacing: EffectiveCommittedPipePairSpacingV1,
        ambient_air_temperature_C: object,
        pressure_Pa: object,
) -> StackedPipePairExternalConvectionCorrectionV1:
    """Correct one exact committed stacked pair inside the v1 source domain.

    The lower pipe retains its isolated-cylinder coefficient.  Only the upper
    pipe is corrected.  v1 deliberately interpolates only between the three
    published temperature-ratio anchors and refuses spacing/Ra extrapolation.
    """

    if not isinstance(pairing_row, CommittedFlowReturnPairingTemperatureRowV1):
        return _blocked_v1("Committed flow/return pairing row is required")
    if not isinstance(effective_spacing, EffectiveCommittedPipePairSpacingV1):
        return _blocked_v1("Effective committed pipe-pair spacing is required")

    section_id = _text_v1(pairing_row.section_id)
    blockers: list[str] = []
    if not pairing_row.ready:
        blockers.append(f"{section_id}: committed pairing evidence is not ready")
    if not pairing_row.paired or pairing_row.external_arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        blockers.append(f"{section_id}: committed stacked flow/return pair is required")
    if _text_v1(effective_spacing.section_id) != section_id:
        blockers.append(f"{section_id}: effective spacing belongs to another section")
    if effective_spacing.external_arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        blockers.append(f"{section_id}: effective spacing is not for stacked pipework")
    if pairing_row.upper_pipe_role not in {FLOW_PIPE_V1, RETURN_PIPE_V1}:
        blockers.append(f"{section_id}: explicit upper-pipe role is required")
    if pairing_row.lower_pipe_role not in {FLOW_PIPE_V1, RETURN_PIPE_V1}:
        blockers.append(f"{section_id}: explicit lower-pipe role is required")
    if pairing_row.upper_pipe_role == pairing_row.lower_pipe_role:
        blockers.append(f"{section_id}: upper and lower pipe roles must differ")

    try:
        diameter_mm = _positive_finite_v1(
            pairing_row.actual_outside_diameter_mm, "outside diameter"
        )
        spacing_mm = _positive_finite_v1(
            effective_spacing.centre_spacing_mm, "centre spacing"
        )
        ambient_C = _finite_v1(ambient_air_temperature_C, "ambient temperature")
        pressure = _positive_finite_v1(pressure_Pa, "air pressure")
    except ValueError as exc:
        blockers.append(f"{section_id}: {exc}")
        diameter_mm = spacing_mm = pressure = math.nan
        ambient_C = math.nan

    if not blockers and not math.isclose(
        diameter_mm,
        float(effective_spacing.actual_outside_diameter_mm),
        rel_tol=0.0,
        abs_tol=1.0e-9,
    ):
        blockers.append(f"{section_id}: pairing and spacing pipe diameters disagree")
    if not blockers and spacing_mm <= diameter_mm:
        blockers.append(f"{section_id}: centre spacing must exceed pipe diameter")

    flow_C = float(pairing_row.flow_pipe_surface_temperature_C)
    return_C = float(pairing_row.return_pipe_surface_temperature_C)
    upper_role = _text_v1(pairing_row.upper_pipe_role)
    lower_role = _text_v1(pairing_row.lower_pipe_role)
    upper_C = flow_C if upper_role == FLOW_PIPE_V1 else return_C
    lower_C = flow_C if lower_role == FLOW_PIPE_V1 else return_C
    if not all(math.isfinite(value) for value in (flow_C, return_C, upper_C, lower_C)):
        blockers.append(f"{section_id}: individual pipe temperatures must be finite")
    elif upper_C <= ambient_C or lower_C <= ambient_C:
        blockers.append(
            f"{section_id}: v1 correction requires both pipe surfaces above ambient"
        )

    if blockers:
        return _blocked_v1(*blockers, section_id=section_id)

    diameter_m = diameter_mm / 1000.0
    try:
        upper_isolated = build_isolated_horizontal_pipe_natural_convection_v1(
            outer_diameter_m=diameter_m,
            surface_temperature_C=upper_C,
            ambient_air_temperature_C=ambient_C,
            pressure_Pa=pressure,
        )
        lower_isolated = build_isolated_horizontal_pipe_natural_convection_v1(
            outer_diameter_m=diameter_m,
            surface_temperature_C=lower_C,
            ambient_air_temperature_C=ambient_C,
            pressure_Pa=pressure,
        )
    except (TypeError, ValueError) as exc:
        return _blocked_v1(f"{section_id}: {exc}", section_id=section_id)

    spacing_ratio = spacing_mm / diameter_mm
    temperature_ratio = (lower_C - ambient_C) / (upper_C - ambient_C)
    if not math.isclose(
        spacing_ratio, SOURCE_SPACING_RATIO_V1, rel_tol=0.0, abs_tol=1.0e-9
    ):
        blockers.append(
            f"{section_id}: spacing ratio S/D={spacing_ratio:.6g} is outside "
            "the v1 validated value S/D=2"
        )
    if not math.isclose(
        upper_isolated.rayleigh_number,
        SOURCE_UPPER_RAYLEIGH_V1,
        rel_tol=RAYLEIGH_RELATIVE_TOLERANCE_V1,
        abs_tol=0.0,
    ):
        blockers.append(
            f"{section_id}: upper-pipe Ra={upper_isolated.rayleigh_number:.6g} "
            "is outside the v1 validated Ra=1e5 anchor"
        )
    if not PRANDTL_MIN_V1 <= upper_isolated.prandtl_number <= PRANDTL_MAX_V1:
        blockers.append(
            f"{section_id}: upper-pipe Pr={upper_isolated.prandtl_number:.6g} "
            "is outside the v1 air range 0.68–0.72"
        )
    if not MIN_TEMPERATURE_EXCESS_RATIO_V1 <= temperature_ratio <= MAX_TEMPERATURE_EXCESS_RATIO_V1:
        blockers.append(
            f"{section_id}: lower/upper temperature-excess ratio "
            f"{temperature_ratio:.6g} is outside 0.5–2.0"
        )
    if blockers:
        return _blocked_v1(*blockers, section_id=section_id)

    factor = _interpolate_upper_correction_factor_v1(temperature_ratio)
    upper_corrected = (
        upper_isolated.external_convection_coefficient_W_m2K * factor
    )
    lower_corrected = lower_isolated.external_convection_coefficient_W_m2K
    if upper_role == FLOW_PIPE_V1:
        flow_coefficient = upper_corrected
        return_coefficient = lower_corrected
    else:
        flow_coefficient = lower_corrected
        return_coefficient = upper_corrected

    return StackedPipePairExternalConvectionCorrectionV1(
        ready=True,
        section_id=section_id,
        upper_pipe_role=upper_role,
        lower_pipe_role=lower_role,
        upper_surface_temperature_C=upper_C,
        lower_surface_temperature_C=lower_C,
        ambient_air_temperature_C=ambient_C,
        outside_diameter_mm=diameter_mm,
        centre_spacing_mm=spacing_mm,
        spacing_to_diameter_ratio=spacing_ratio,
        lower_to_upper_temperature_excess_ratio=temperature_ratio,
        upper_pipe_rayleigh_number=upper_isolated.rayleigh_number,
        upper_pipe_prandtl_number=upper_isolated.prandtl_number,
        upper_pipe_isolated_coefficient_W_m2K=(
            upper_isolated.external_convection_coefficient_W_m2K
        ),
        lower_pipe_isolated_coefficient_W_m2K=(
            lower_isolated.external_convection_coefficient_W_m2K
        ),
        upper_pipe_correction_factor=factor,
        upper_pipe_corrected_coefficient_W_m2K=upper_corrected,
        lower_pipe_corrected_coefficient_W_m2K=lower_corrected,
        flow_pipe_external_convection_coefficient_W_m2K=flow_coefficient,
        return_pipe_external_convection_coefficient_W_m2K=return_coefficient,
        status=(
            "Calculated — validated stacked-pair upper-pipe correction; "
            "lower pipe retains isolated-cylinder coefficient"
        ),
        blockers=(),
    )


def _interpolate_upper_correction_factor_v1(temperature_ratio: float) -> float:
    ratio = float(temperature_ratio)
    for (left_r, left_factor), (right_r, right_factor) in zip(
        _UPPER_CORRECTION_ANCHORS_V1,
        _UPPER_CORRECTION_ANCHORS_V1[1:],
    ):
        if left_r <= ratio <= right_r:
            fraction = (ratio - left_r) / (right_r - left_r)
            return left_factor + fraction * (right_factor - left_factor)
    raise ValueError("Temperature-excess ratio is outside correction anchors")


def _blocked_v1(
        *blockers: str,
        section_id: str = "",
) -> StackedPipePairExternalConvectionCorrectionV1:
    clean = tuple(dict.fromkeys(_text_v1(value) for value in blockers if _text_v1(value)))
    return StackedPipePairExternalConvectionCorrectionV1(
        ready=False,
        section_id=_text_v1(section_id),
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
