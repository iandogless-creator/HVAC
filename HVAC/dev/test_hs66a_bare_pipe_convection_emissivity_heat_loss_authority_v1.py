# ======================================================================
# H-S66-A — Deterministic bare-pipe convection and emissivity heat loss
# ======================================================================

from __future__ import annotations

import math

from HVAC.heatloss.physics.pipe_radiation_engine import (
    ABS_ZERO_C,
    STEFAN_BOLTZMANN,
    BarePipeHeatLossInputV1,
    compute_bare_pipe_heat_loss_v1,
    estimate_radiative_loss_per_m_simple,
)


def _input(*, length_m: float = 3.0) -> BarePipeHeatLossInputV1:
    return BarePipeHeatLossInputV1(
        surface_temperature_C=60.0,
        ambient_air_temperature_C=20.0,
        mean_radiant_temperature_C=18.0,
        outer_diameter_m=0.022,
        length_m=length_m,
        emissivity=0.95,
        external_convection_coefficient_W_m2K=5.0,
    )


def _assert_raises_value_error(input_data: BarePipeHeatLossInputV1) -> None:
    try:
        compute_bare_pipe_heat_loss_v1(input_data)
    except ValueError:
        return
    raise AssertionError("Expected ValueError")


def main() -> None:
    input_data = _input()
    before = repr(input_data)
    result = compute_bare_pipe_heat_loss_v1(input_data)
    repeated = compute_bare_pipe_heat_loss_v1(input_data)

    assert result == repeated
    assert repr(input_data) == before

    expected_area = math.pi * 0.022 * 3.0
    expected_convection = 5.0 * expected_area * (60.0 - 20.0)
    expected_radiation = (
        0.95
        * STEFAN_BOLTZMANN
        * expected_area
        * ((60.0 + ABS_ZERO_C) ** 4 - (18.0 + ABS_ZERO_C) ** 4)
    )
    expected_total = expected_convection + expected_radiation

    assert math.isclose(result.exposed_area_m2, expected_area, abs_tol=1e-12)
    assert math.isclose(
        result.convection_heat_loss_W,
        expected_convection,
        abs_tol=1e-12,
    )
    assert math.isclose(
        result.radiation_heat_loss_W,
        expected_radiation,
        abs_tol=1e-12,
    )
    assert math.isclose(result.total_heat_loss_W, expected_total, abs_tol=1e-12)
    assert math.isclose(
        result.total_heat_loss_W,
        result.convection_heat_loss_W + result.radiation_heat_loss_W,
        abs_tol=1e-12,
    )
    assert math.isclose(
        result.total_heat_loss_W_per_m,
        result.total_heat_loss_W / input_data.length_m,
        abs_tol=1e-12,
    )
    assert result.status == "Calculated — bare-pipe convection and radiation only"

    doubled = compute_bare_pipe_heat_loss_v1(_input(length_m=6.0))
    assert math.isclose(
        doubled.total_heat_loss_W,
        2.0 * result.total_heat_loss_W,
        abs_tol=1e-12,
    )
    assert math.isclose(
        doubled.total_heat_loss_W_per_m,
        result.total_heat_loss_W_per_m,
        abs_tol=1e-12,
    )

    # Paint colour is not an inferred input: equal long-wave emissivity gives
    # equal radiation for otherwise identical black/white painted surfaces.
    black_paint = compute_bare_pipe_heat_loss_v1(_input())
    white_paint = compute_bare_pipe_heat_loss_v1(_input())
    assert black_paint == white_paint

    equilibrium = compute_bare_pipe_heat_loss_v1(
        BarePipeHeatLossInputV1(
            surface_temperature_C=20.0,
            ambient_air_temperature_C=20.0,
            mean_radiant_temperature_C=20.0,
            outer_diameter_m=0.0213,
            length_m=1.0,
            emissivity=0.95,
            external_convection_coefficient_W_m2K=5.0,
        )
    )
    assert equilibrium.convection_heat_loss_W == 0.0
    assert equilibrium.radiation_heat_loss_W == 0.0
    assert equilibrium.total_heat_loss_W == 0.0

    inward = compute_bare_pipe_heat_loss_v1(
        BarePipeHeatLossInputV1(
            surface_temperature_C=10.0,
            ambient_air_temperature_C=20.0,
            mean_radiant_temperature_C=20.0,
            outer_diameter_m=0.0213,
            length_m=1.0,
            emissivity=0.95,
            external_convection_coefficient_W_m2K=5.0,
        )
    )
    assert inward.total_heat_loss_W < 0.0

    invalid_inputs = (
        BarePipeHeatLossInputV1(60.0, 20.0, 20.0, 0.0, 1.0, 0.95, 5.0),
        BarePipeHeatLossInputV1(60.0, 20.0, 20.0, 0.022, 0.0, 0.95, 5.0),
        BarePipeHeatLossInputV1(60.0, 20.0, 20.0, 0.022, 1.0, 1.01, 5.0),
        BarePipeHeatLossInputV1(60.0, 20.0, 20.0, 0.022, 1.0, 0.95, -1.0),
        BarePipeHeatLossInputV1(
            -ABS_ZERO_C,
            20.0,
            20.0,
            0.022,
            1.0,
            0.95,
            5.0,
        ),
        BarePipeHeatLossInputV1(
            float("nan"),
            20.0,
            20.0,
            0.022,
            1.0,
            0.95,
            5.0,
        ),
    )
    for invalid in invalid_inputs:
        _assert_raises_value_error(invalid)

    # The historical convenience wrapper remains importable even though its
    # optional legacy surface-key data module is absent from the current tree.
    legacy = estimate_radiative_loss_per_m_simple(
        surface_temperature_C=60.0,
        ambient_temperature_C=20.0,
        outer_diameter_m=0.022,
        emissivity_key=None,
    )
    assert legacy > 0.0

    print(
        "OK — H-S66-A deterministic bare-pipe convection and emissivity "
        "heat-loss authority passed."
    )


if __name__ == "__main__":
    main()
