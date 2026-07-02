from __future__ import annotations

from HVAC.core.fluid_friction.friction_factor_v1 import (
    colebrook_friction_factor,
    darcy_weisbach_pressure_drop,
    darcy_weisbach_pressure_gradient,
    haaland_friction_factor,
    reynolds_number,
)


def test_reynolds_number_dynamic_viscosity() -> None:
    re = reynolds_number(
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
        density_kg_m3=998.0,
        dynamic_viscosity_pa_s=0.001,
    )

    assert abs(re - 19960.0) < 1.0e-9


def test_reynolds_number_kinematic_viscosity() -> None:
    re = reynolds_number(
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
        kinematic_viscosity_m2_s=1.0e-6,
    )

    assert abs(re - 20000.0) < 1.0e-9


def test_haaland_laminar() -> None:
    f = haaland_friction_factor(
        reynolds_number=1000.0,
        relative_roughness=0.0,
    )

    assert abs(f - 0.064) < 1.0e-12


def test_haaland_turbulent_range() -> None:
    f = haaland_friction_factor(
        reynolds_number=100000.0,
        relative_roughness=0.00075,
    )

    assert 0.015 < f < 0.03


def test_colebrook_converges_from_haaland() -> None:
    result = colebrook_friction_factor(
        reynolds_number=100000.0,
        relative_roughness=0.00075,
        tolerance=1.0e-6,
        max_iterations=100,
        initial_guess_method="haaland",
    )

    assert result.converged is True
    assert result.iteration_count <= 100
    assert result.residual <= 1.0e-6
    assert 0.015 < result.friction_factor < 0.03
    assert result.method == "colebrook(initial=haaland)"


def test_darcy_pressure_gradient() -> None:
    gradient = darcy_weisbach_pressure_gradient(
        friction_factor=0.02,
        density_kg_m3=998.0,
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
    )

    assert abs(gradient - 499.0) < 1.0e-9


def test_darcy_pressure_drop() -> None:
    dp = darcy_weisbach_pressure_drop(
        friction_factor=0.02,
        length_m=10.0,
        internal_diameter_m=0.02,
        density_kg_m3=998.0,
        velocity_m_s=1.0,
    )

    assert abs(dp - 4990.0) < 1.0e-9


if __name__ == "__main__":
    test_reynolds_number_dynamic_viscosity()
    test_reynolds_number_kinematic_viscosity()
    test_haaland_laminar()
    test_haaland_turbulent_range()
    test_colebrook_converges_from_haaland()
    test_darcy_pressure_gradient()
    test_darcy_pressure_drop()
    print("OK — H-S29-A shared friction-factor core passed.")