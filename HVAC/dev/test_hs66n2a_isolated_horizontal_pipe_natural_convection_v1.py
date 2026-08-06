# ======================================================================
# H-S66-N2A — Isolated horizontal-pipe natural-convection authority
# ======================================================================

from __future__ import annotations

import math

from HVAC.heatloss.physics.isolated_horizontal_pipe_natural_convection_v1 import (
    build_isolated_horizontal_pipe_natural_convection_v1,
)


def _expect_value_error(**overrides: object) -> None:
    inputs: dict[str, object] = {
        "outer_diameter_m": 0.028,
        "surface_temperature_C": 60.0,
        "ambient_air_temperature_C": 20.0,
        "pressure_Pa": 101_325.0,
    }
    inputs.update(overrides)
    try:
        build_isolated_horizontal_pipe_natural_convection_v1(**inputs)
    except ValueError:
        return
    raise AssertionError("Expected ValueError")


def main() -> None:
    result = build_isolated_horizontal_pipe_natural_convection_v1(
        outer_diameter_m=0.028,
        surface_temperature_C=60.0,
        ambient_air_temperature_C=20.0,
        pressure_Pa=101_325.0,
    )
    repeated = build_isolated_horizontal_pipe_natural_convection_v1(
        outer_diameter_m=0.028,
        surface_temperature_C=60.0,
        ambient_air_temperature_C=20.0,
        pressure_Pa=101_325.0,
    )
    assert result == repeated
    assert result.film_temperature_C == 40.0
    assert 0.69 < result.prandtl_number < 0.73
    assert 1.0e4 < result.rayleigh_number < 1.0e6
    assert 4.0 < result.external_convection_coefficient_W_m2K < 8.0

    reconstructed_nusselt = (
        0.60
        + 0.387 * result.rayleigh_number ** (1.0 / 6.0)
        / (
            1.0 + (0.559 / result.prandtl_number) ** (9.0 / 16.0)
        ) ** (8.0 / 27.0)
    ) ** 2
    assert math.isclose(
        result.nusselt_number,
        reconstructed_nusselt,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        result.external_convection_coefficient_W_m2K,
        result.nusselt_number
        * result.thermal_conductivity_W_mK
        / result.outer_diameter_m,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert "Churchill-Chu" in result.correlation_source
    assert result.status == (
        "Calculated — isolated horizontal-pipe natural convection"
    )

    # A cold pipe uses the same positive coefficient authority; the later heat-
    # loss calculation retains the heat-flow sign through its temperature delta.
    cold = build_isolated_horizontal_pipe_natural_convection_v1(
        outer_diameter_m=0.028,
        surface_temperature_C=10.0,
        ambient_air_temperature_C=20.0,
        pressure_Pa=101_325.0,
    )
    assert cold.external_convection_coefficient_W_m2K > 0.0
    assert cold.rayleigh_number > 0.0

    equilibrium = build_isolated_horizontal_pipe_natural_convection_v1(
        outer_diameter_m=0.028,
        surface_temperature_C=20.0,
        ambient_air_temperature_C=20.0,
        pressure_Pa=101_325.0,
    )
    assert equilibrium.rayleigh_number == 0.0
    assert math.isclose(equilibrium.nusselt_number, 0.36, abs_tol=1e-15)

    for invalid in (
        {"outer_diameter_m": 0.0},
        {"outer_diameter_m": -0.028},
        {"surface_temperature_C": -273.15},
        {"ambient_air_temperature_C": float("nan")},
        {"pressure_Pa": 49_999.0},
        {"pressure_Pa": 120_001.0},
        {"surface_temperature_C": 150.0, "ambient_air_temperature_C": 150.0},
        {"surface_temperature_C": "not-a-temperature"},
    ):
        _expect_value_error(**invalid)

    print(
        "OK — H-S66-N2A isolated horizontal-pipe natural-convection "
        "authority passed."
    )


if __name__ == "__main__":
    main()
