from __future__ import annotations

from HVAC.core.fluid_friction.friction_factor_v1 import (
    darcy_weisbach_pressure_gradient as shared_darcy_gradient,
    haaland_friction_factor as shared_haaland,
    reynolds_number as shared_reynolds,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    darcy_pressure_gradient_Pa_per_m,
    haaland_friction_factor,
    reynolds_number,
)


def test_basic_ps_reynolds_matches_shared_core() -> None:
    basic = reynolds_number(
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
        water_density_kg_m3=998.0,
        dynamic_viscosity_Pa_s=0.001,
    )

    shared = shared_reynolds(
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
        density_kg_m3=998.0,
        dynamic_viscosity_pa_s=0.001,
    )

    assert abs(basic - shared) < 1.0e-12


def test_basic_ps_haaland_matches_shared_core() -> None:
    basic = haaland_friction_factor(
        reynolds_number=100000.0,
        internal_diameter_m=0.02,
        roughness_m=0.0000015,
    )

    shared = shared_haaland(
        reynolds_number=100000.0,
        relative_roughness=0.0000015 / 0.02,
    )

    assert abs(basic - shared) < 1.0e-12


def test_basic_ps_darcy_gradient_matches_shared_core() -> None:
    basic = darcy_pressure_gradient_Pa_per_m(
        friction_factor=0.02,
        water_density_kg_m3=998.0,
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
    )

    shared = shared_darcy_gradient(
        friction_factor=0.02,
        density_kg_m3=998.0,
        velocity_m_s=1.0,
        internal_diameter_m=0.02,
    )

    assert abs(basic - shared) < 1.0e-12


if __name__ == "__main__":
    test_basic_ps_reynolds_matches_shared_core()
    test_basic_ps_haaland_matches_shared_core()
    test_basic_ps_darcy_gradient_matches_shared_core()
    print("OK — H-S29-D Basic PS friction helpers use shared core.")