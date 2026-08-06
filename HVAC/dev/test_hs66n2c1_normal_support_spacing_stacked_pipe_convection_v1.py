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
from HVAC.heatloss.physics.normal_support_spacing_stacked_pipe_convection_resolver_v1 import (
    CONSERVATIVE_ISOLATED_METHOD_V1,
    EMPIRICAL_N2C_METHOD_V1,
    resolve_normal_support_spacing_stacked_pipe_convection_v1,
)


AMBIENT_C = 21.0
PRESSURE_PA = 101325.0
DIAMETER_MM = 28.0


def _row(upper_role: str, flow_C: float, return_C: float):
    lower_role = RETURN_PIPE_V1 if upper_role == FLOW_PIPE_V1 else FLOW_PIPE_V1
    return CommittedFlowReturnPairingTemperatureRowV1(
        section_id="section-001",
        section_scope="route-exclusive",
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
        flow_pipe_surface_temperature_C=flow_C,
        return_pipe_surface_temperature_C=return_C,
        vertical_order_source="test",
        temperature_source="test",
        ready=True,
        status="Ready",
    )


def _spacing(centre_spacing_mm: float):
    return EffectiveCommittedPipePairSpacingV1(
        section_id="section-001",
        external_arrangement=STACKED_FLOW_RETURN_PAIR_V1,
        actual_outside_diameter_mm=DIAMETER_MM,
        nominal_default_outside_diameter_mm=28,
        support_type="paired_individual_plastic_clips",
        support_label="Paired individual plastic clips",
        centre_spacing_mm=centre_spacing_mm,
        locally_overridden=False,
        source="test",
        status="Ready",
    )


def _isolated(surface_C: float) -> float:
    return build_isolated_horizontal_pipe_natural_convection_v1(
        outer_diameter_m=DIAMETER_MM / 1000.0,
        surface_temperature_C=surface_C,
        ambient_air_temperature_C=AMBIENT_C,
        pressure_Pa=PRESSURE_PA,
    ).external_convection_coefficient_W_m2K


# Live example: 28 mm OD / 50 mm c/c with flow above return.
live_flow_upper = resolve_normal_support_spacing_stacked_pipe_convection_v1(
    pairing_row=_row(FLOW_PIPE_V1, 75.0, 65.0),
    effective_spacing=_spacing(50.0),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert live_flow_upper.ready, live_flow_upper.blockers
assert live_flow_upper.conservative_fallback
assert live_flow_upper.resolution_method == CONSERVATIVE_ISOLATED_METHOD_V1
assert math.isclose(live_flow_upper.spacing_to_diameter_ratio, 50.0 / 28.0)
assert math.isclose(live_flow_upper.upper_pipe_correction_factor, 1.0)
assert math.isclose(live_flow_upper.lower_pipe_correction_factor, 1.0)
assert math.isclose(
    live_flow_upper.flow_pipe_external_convection_coefficient_W_m2K,
    _isolated(75.0),
)
assert math.isclose(
    live_flow_upper.return_pipe_external_convection_coefficient_W_m2K,
    _isolated(65.0),
)
assert live_flow_upper.empirical_correction_blockers
assert "no stacked interaction reduction credited" in live_flow_upper.status

# Reversing the order preserves individual temperatures and role mapping.
live_return_upper = resolve_normal_support_spacing_stacked_pipe_convection_v1(
    pairing_row=_row(RETURN_PIPE_V1, 75.0, 65.0),
    effective_spacing=_spacing(50.0),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert live_return_upper.ready
assert live_return_upper.upper_pipe_role == RETURN_PIPE_V1
assert math.isclose(
    live_return_upper.flow_pipe_external_convection_coefficient_W_m2K,
    _isolated(75.0),
)
assert math.isclose(
    live_return_upper.return_pipe_external_convection_coefficient_W_m2K,
    _isolated(65.0),
)

# All Environment defaults fall inside the declared normal envelope.
for diameter_mm, spacing_mm in (
    (10.0, 25.0),
    (15.0, 30.0),
    (22.0, 40.0),
    (28.0, 50.0),
    (35.0, 60.0),
    (42.0, 70.0),
    (54.0, 90.0),
):
    ratio = spacing_mm / diameter_mm
    assert 1.5 <= ratio <= 3.0

# Outside the normal support envelope still fails closed.
too_close = resolve_normal_support_spacing_stacked_pipe_convection_v1(
    pairing_row=_row(FLOW_PIPE_V1, 75.0, 65.0),
    effective_spacing=_spacing(40.0),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert not too_close.ready
assert any("outside the normal support-spacing envelope" in value for value in too_close.blockers)


# The exact N2C experimental anchor still takes precedence over fallback.
def _temperature_for_ra(target_ra: float) -> float:
    low, high = AMBIENT_C + 0.001, 180.0
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


upper_C = _temperature_for_ra(1.0e5)
lower_C = AMBIENT_C + 0.5 * (upper_C - AMBIENT_C)
empirical = resolve_normal_support_spacing_stacked_pipe_convection_v1(
    pairing_row=_row(FLOW_PIPE_V1, upper_C, lower_C),
    effective_spacing=_spacing(56.0),
    ambient_air_temperature_C=AMBIENT_C,
    pressure_Pa=PRESSURE_PA,
)
assert empirical.ready, empirical.blockers
assert not empirical.conservative_fallback
assert empirical.resolution_method == EMPIRICAL_N2C_METHOD_V1
assert math.isclose(empirical.upper_pipe_correction_factor, 0.98)
assert math.isclose(empirical.lower_pipe_correction_factor, 1.0)

print(
    "OK — H-S66-N2C1 normal support-spacing stacked-pipe convection "
    "resolution passed."
)
