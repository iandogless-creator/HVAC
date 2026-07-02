from __future__ import annotations
import math
from types import SimpleNamespace

from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    _dn_from_pipe_size_label_v1,
    _route_pressure_material_v1,
    build_route_pressure_accumulator_v1,
)
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)


def test_dn_parser_reads_common_labels() -> None:
    assert _dn_from_pipe_size_label_v1("10 mm") == 10
    assert _dn_from_pipe_size_label_v1("DN15") == 15
    assert _dn_from_pipe_size_label_v1("Copper 22 mm") == 22


def test_material_defaults_to_copper() -> None:
    project_state = SimpleNamespace()
    assert _route_pressure_material_v1(project_state) == "copper"


def test_mass_flow_wrapper_uses_copper_10_catalogue_basis() -> None:
    mass_flow_kg_s = 0.02

    wrapper_result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=mass_flow_kg_s,
        material="copper",
        dn=10,
        length_m=1.0,
        friction_method="colebrook",
    )

    # Copper DN10 in pipe_materials_library.py:
    # OD 12.0 mm, ID 10.0 mm, roughness 0.0015 mm.
    expected_internal_diameter_m = 0.010
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
    test_dn_parser_reads_common_labels()
    test_material_defaults_to_copper()
    test_mass_flow_wrapper_uses_copper_10_catalogue_basis()
    print("OK — H-S29-E route pressure uses hydronic mass-flow wrapper.")
