from __future__ import annotations
import math
from types import SimpleNamespace

from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    _basic_ps_result_pipe_identity_v1,
)
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)


def test_exact_basic_ps_identity_ignores_display_wording() -> None:
    result = SimpleNamespace(
        material_key="mlcp",
        pipe_size_key=20,
        pipe_size_label="deliberately not a size",
    )
    assert _basic_ps_result_pipe_identity_v1(result) == ("mlcp", 20)


def test_mass_flow_wrapper_uses_copper_10_catalogue_basis() -> None:
    mass_flow_kg_s = 0.02

    wrapper_result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=mass_flow_kg_s,
        material="copper",
        dn=10,
        length_m=1.0,
        friction_method="colebrook",
    )

    # Copper tube 10 mm OD × 0.6 mm wall in the current v1 series.
    # Hydraulic ID is 8.8 mm; roughness remains 0.0015 mm.
    expected_internal_diameter_m = 0.0088
    expected_roughness_m = 0.0000015
    expected_volume_flow_m3_s = mass_flow_kg_s / 998.0
    expected_area_m2 = math.pi * expected_internal_diameter_m**2 / 4.0
    expected_velocity_m_s = expected_volume_flow_m3_s / expected_area_m2

    assert abs(wrapper_result.internal_diameter_m - expected_internal_diameter_m) < 1.0e-12
    assert abs(wrapper_result.roughness_m - expected_roughness_m) < 1.0e-12
    assert abs(wrapper_result.volume_flow_m3_s - expected_volume_flow_m3_s) < 1.0e-12
    assert abs(wrapper_result.velocity_m_s - expected_velocity_m_s) < 1.0e-12

    assert wrapper_result.pressure_gradient_pa_per_m > 0.0
    assert wrapper_result.pressure_drop_pa > 0.0
    assert wrapper_result.colebrook_converged is True


if __name__ == "__main__":
    test_exact_basic_ps_identity_ignores_display_wording()
    test_mass_flow_wrapper_uses_copper_10_catalogue_basis()
    print("OK — H-S29-E route pressure uses hydronic mass-flow wrapper.")
