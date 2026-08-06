from __future__ import annotations

import math

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    CommittedFlowReturnPairingTemperatureRowV1,
    FLOW_PIPE_V1,
    LOWER_POSITION_V1,
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
from HVAC.heatloss.physics.stacked_pipe_pair_external_convection_correction_v1 import (
    build_stacked_pipe_pair_external_convection_correction_v1,
)


AMBIENT_C = 20.0
PRESSURE_PA = 101325.0
DIAMETER_MM = 28.0


def _surface_temperature_for_ra(target_ra: float) -> float:
    low = AMBIENT_C + 0.001
    high = 180.0
    for _ in range(100):
        middle = 0.5 * (low + high)
        result = build_isolated_horizontal_pipe_natural_convection_v1(
            outer_diameter_m=DIAMETER_MM / 1000.0,
            surface_temperature_C=middle,
            ambient_air_temperature_C=AMBIENT_C,
            pressure_Pa=PRESSURE_PA,
        )
        if result.rayleigh_number < target_ra:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def _pairing_row(
        *,
        upper_role: str,
        upper_temperature_C: float,
        lower_temperature_C: float,
) -> CommittedFlowReturnPairingTemperatureRowV1:
    lower_role = RETURN_PIPE_V1 if upper_role == FLOW_PIPE_V1 else FLOW_PIPE_V1
    flow_temperature = (
        upper_temperature_C if upper_role == FLOW_PIPE_V1 else lower_temperature_C
    )
    return_temperature = (
        upper_temperature_C if upper_role == RETURN_PIPE_V1 else lower_temperature_C
    )
    return CommittedFlowReturnPairingTemperatureRowV1(
        section_id="section-001",
        section_scope="shared",
        order=1,
        external_arrangement=STACKED_FLOW_RETURN_PAIR_V1,
        paired=True,
        material_key="copper",
        material_label="Copper",
        catalogue_size_key=28,
        actual_outside_diameter_mm=DIAMETER_MM,
        upper_pipe_role=upper_role,
        lower_pipe_role=lower_role,
        flow_pipe_vertical_position=(
            UPPER_POSITION_V1 if upper_role == FLOW_PIPE_V1 else LOWER_POSITION_V1
        ),
        return_pipe_vertical_position=(
            UPPER_POSITION_V1 if upper_role == RETURN_PIPE_V1 else LOWER_POSITION_V1
        ),
        flow_pipe_surface_temperature_C=flow_temperature,
        return_pipe_surface_temperature_C=return_temperature,
        vertical_order_source="test",
        temperature_source="test",
        ready=True,
        status="Ready",
    )


def _spacing(spacing_mm: float = 56.0) -> EffectiveCommittedPipePairSpacingV1:
    return EffectiveCommittedPipePairSpacingV1(
        section_id="section-001",
        external_arrangement=STACKED_FLOW_RETURN_PAIR_V1,
        actual_outside_diameter_mm=DIAMETER_MM,
        nominal_default_outside_diameter_mm=28,
        support_type="moulded_plastic_double_clip",
        support_label="Moulded plastic double clip",
        centre_spacing_mm=spacing_mm,
        locally_overridden=False,
        source="test",
        status="Ready",
    )


upper_temperature = _surface_temperature_for_ra(1.0e5)

# r=0.5 anchor: flow is upper, cooler return is lower.
lower_temperature = AMBIENT_C + 0.5 * (upper_temperature - AMBIENT_C)
flow_upper = build_stacked_pipe_pair_external_convection_correction_v1(
    pairing_row=_pairing_row(
        upper_role=FLOW_PIPE_V1,
        upper_temperature_C=upper_temperature,
        lower_temperature_C=lower_temperature,
    ),
    effective_spacing=_spacing(),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert flow_upper.ready, flow_upper.blockers
assert math.isclose(flow_upper.spacing_to_diameter_ratio, 2.0)
assert math.isclose(flow_upper.lower_to_upper_temperature_excess_ratio, 0.5)
assert math.isclose(flow_upper.upper_pipe_correction_factor, 0.98)
assert math.isclose(
    flow_upper.upper_pipe_corrected_coefficient_W_m2K,
    0.98 * flow_upper.upper_pipe_isolated_coefficient_W_m2K,
)
assert math.isclose(
    flow_upper.lower_pipe_corrected_coefficient_W_m2K,
    flow_upper.lower_pipe_isolated_coefficient_W_m2K,
)
assert math.isclose(
    flow_upper.flow_pipe_external_convection_coefficient_W_m2K,
    flow_upper.upper_pipe_corrected_coefficient_W_m2K,
)

# r=2 anchor: return is upper, hotter flow is lower.
hotter_lower_temperature = AMBIENT_C + 2.0 * (upper_temperature - AMBIENT_C)
return_upper = build_stacked_pipe_pair_external_convection_correction_v1(
    pairing_row=_pairing_row(
        upper_role=RETURN_PIPE_V1,
        upper_temperature_C=upper_temperature,
        lower_temperature_C=hotter_lower_temperature,
    ),
    effective_spacing=_spacing(),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert return_upper.ready, return_upper.blockers
assert math.isclose(return_upper.upper_pipe_correction_factor, 0.39)
assert math.isclose(
    return_upper.return_pipe_external_convection_coefficient_W_m2K,
    return_upper.upper_pipe_corrected_coefficient_W_m2K,
)
assert math.isclose(
    return_upper.flow_pipe_external_convection_coefficient_W_m2K,
    return_upper.lower_pipe_corrected_coefficient_W_m2K,
)

# Bounded interpolation is deterministic at r=0.75.
middle_lower_temperature = AMBIENT_C + 0.75 * (upper_temperature - AMBIENT_C)
interpolated = build_stacked_pipe_pair_external_convection_correction_v1(
    pairing_row=_pairing_row(
        upper_role=FLOW_PIPE_V1,
        upper_temperature_C=upper_temperature,
        lower_temperature_C=middle_lower_temperature,
    ),
    effective_spacing=_spacing(),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert interpolated.ready, interpolated.blockers
assert math.isclose(interpolated.upper_pipe_correction_factor, 0.92)

# The live 28 mm OD / 50 mm c/c example must not be extrapolated.
outside_spacing_domain = build_stacked_pipe_pair_external_convection_correction_v1(
    pairing_row=_pairing_row(
        upper_role=FLOW_PIPE_V1,
        upper_temperature_C=upper_temperature,
        lower_temperature_C=lower_temperature,
    ),
    effective_spacing=_spacing(50.0),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert not outside_spacing_domain.ready
assert any("S/D=1.78571" in blocker for blocker in outside_spacing_domain.blockers)

# No extrapolation beyond the measured temperature-ratio anchors.
outside_temperature_domain = build_stacked_pipe_pair_external_convection_correction_v1(
    pairing_row=_pairing_row(
        upper_role=FLOW_PIPE_V1,
        upper_temperature_C=upper_temperature,
        lower_temperature_C=(
            AMBIENT_C + 0.4 * (upper_temperature - AMBIENT_C)
        ),
    ),
    effective_spacing=_spacing(),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert not outside_temperature_domain.ready
assert any("outside 0.5–2.0" in blocker for blocker in outside_temperature_domain.blockers)

print(
    "OK — H-S66-N2C deterministic stacked-pair external-convection "
    "correction passed."
)
