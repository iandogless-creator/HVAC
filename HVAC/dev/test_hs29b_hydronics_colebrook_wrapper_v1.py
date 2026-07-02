from __future__ import annotations

import math

from HVAC.hydronics.physics.colebrook import (
    CalcPipe,
    colebrook,
    darcy_weisbach,
    reynolds_number,
)


def test_legacy_reynolds_number_signature() -> None:
    re = reynolds_number(
        velocity=1.0,
        diameter=0.02,
        kinematic_viscosity=1.0e-6,
    )

    assert abs(re - 20000.0) < 1.0e-9


def test_legacy_colebrook_returns_float() -> None:
    f = colebrook(
        Re=100000.0,
        eD=0.00075,
        tol=1.0e-6,
        max_iter=100,
    )

    assert isinstance(f, float)
    assert 0.015 < f < 0.03


def test_legacy_darcy_weisbach_signature() -> None:
    dp = darcy_weisbach(
        f=0.02,
        length=10.0,
        diameter=0.02,
        density=998.0,
        velocity=1.0,
    )

    assert abs(dp - 4990.0) < 1.0e-9


def test_legacy_calcpipe_uses_volumetric_flow_m3_s() -> None:
    flow_rate_m3_s = 0.0003
    diameter_m = 0.02
    length_m = 10.0
    roughness_m = 0.000015
    density_kg_m3 = 998.0
    kinematic_viscosity_m2_s = 1.0e-6

    result = CalcPipe(
        flow_rate=flow_rate_m3_s,
        diameter=diameter_m,
        length=length_m,
        roughness=roughness_m,
        density=density_kg_m3,
        kinematic_viscosity=kinematic_viscosity_m2_s,
    )

    expected_area = math.pi * diameter_m**2 / 4.0
    expected_velocity = flow_rate_m3_s / expected_area
    expected_re = expected_velocity * diameter_m / kinematic_viscosity_m2_s

    assert abs(result["velocity"] - expected_velocity) < 1.0e-12
    assert abs(result["Re"] - expected_re) < 1.0e-9
    assert 0.0 < result["friction_factor"] < 0.1
    assert result["pressure_drop"] > 0.0


if __name__ == "__main__":
    test_legacy_reynolds_number_signature()
    test_legacy_colebrook_returns_float()
    test_legacy_darcy_weisbach_signature()
    test_legacy_calcpipe_uses_volumetric_flow_m3_s()
    print("OK — H-S29-B hydronics Colebrook compatibility wrapper passed.")