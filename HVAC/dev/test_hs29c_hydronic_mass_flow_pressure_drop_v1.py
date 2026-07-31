from __future__ import annotations

import math

from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)


def test_copper_22_mass_flow_uses_catalogue_id_and_roughness() -> None:
    result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=0.1,
        material="copper",
        dn=22,
        length_m=10.0,
        friction_method="colebrook",
    )

    assert result.material == "copper"
    assert result.dn == 22

    # Copper tube 22 mm OD × 0.9 mm wall in the v1 series.
    assert abs(result.internal_diameter_m - 0.0202) < 1.0e-12
    assert abs(result.roughness_m - 0.0000015) < 1.0e-12

    expected_volume_flow = 0.1 / 998.0
    expected_area = math.pi * 0.0202**2 / 4.0
    expected_velocity = expected_volume_flow / expected_area

    assert abs(result.volume_flow_m3_s - expected_volume_flow) < 1.0e-12
    assert abs(result.velocity_m_s - expected_velocity) < 1.0e-12

    assert result.reynolds_number > 0.0
    assert result.haaland_friction_factor > 0.0
    assert result.selected_friction_factor > 0.0
    assert result.friction_method == "colebrook"
    assert result.colebrook_iteration_count <= 100
    assert result.colebrook_converged is True
    assert result.pressure_gradient_pa_per_m > 0.0
    assert result.pressure_drop_pa > 0.0


def test_haaland_mode_is_available() -> None:
    result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=0.1,
        material="copper",
        dn=22,
        length_m=10.0,
        friction_method="haaland",
    )

    assert result.friction_method == "haaland"
    assert result.colebrook_iteration_count == 0
    assert result.colebrook_converged is True
    assert result.colebrook_residual is None
    assert result.selected_friction_factor == result.haaland_friction_factor
    assert result.status == "First-pass Haaland estimate"


def test_zero_flow_returns_zero_pressure_drop_but_keeps_catalogue_basis() -> None:
    result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=0.0,
        material="copper",
        dn=22,
        length_m=10.0,
    )

    assert result.internal_diameter_m == 0.0202
    assert result.roughness_m == 0.0000015
    assert result.volume_flow_m3_s == 0.0
    assert result.velocity_m_s == 0.0
    assert result.reynolds_number == 0.0
    assert result.pressure_gradient_pa_per_m == 0.0
    assert result.pressure_drop_pa == 0.0
    assert result.status == "No flow"


def test_unknown_material_raises() -> None:
    try:
        calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
            mass_flow_kg_s=0.1,
            material="unknown-material",
            dn=22,
            length_m=10.0,
        )
    except ValueError as exc:
        assert "No internal diameter" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown material")


def test_unknown_dn_raises() -> None:
    try:
        calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
            mass_flow_kg_s=0.1,
            material="copper",
            dn=999,
            length_m=10.0,
        )
    except ValueError as exc:
        assert "No internal diameter" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown DN")


if __name__ == "__main__":
    test_copper_22_mass_flow_uses_catalogue_id_and_roughness()
    test_haaland_mode_is_available()
    test_zero_flow_returns_zero_pressure_drop_but_keeps_catalogue_basis()
    test_unknown_material_raises()
    test_unknown_dn_raises()
    print("OK — H-S29-C hydronic mass-flow pressure drop wrapper passed.")