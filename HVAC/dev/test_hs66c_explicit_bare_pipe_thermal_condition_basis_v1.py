# ======================================================================
# H-S66-C — Explicit bare-pipe thermal-condition basis authority
# ======================================================================

from __future__ import annotations

import inspect
import math

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    BarePipeThermalConditionBasisV1,
    build_catalogue_bare_pipe_input_from_thermal_basis_v1,
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.pipe_radiation_engine import (
    ABS_ZERO_C,
    compute_bare_pipe_heat_loss_v1,
)


EXPLICIT = {
    "surface_temperature_C": 60.0,
    "ambient_air_temperature_C": 20.0,
    "mean_radiant_temperature_C": 18.0,
    "emissivity": 0.95,
    "external_convection_coefficient_W_m2K": 5.0,
}


def _basis(**overrides) -> BarePipeThermalConditionBasisV1:
    values = dict(EXPLICIT)
    values.update(overrides)
    return build_explicit_bare_pipe_thermal_condition_basis_v1(**values)


def _expect_value_error(**overrides) -> None:
    try:
        _basis(**overrides)
    except ValueError:
        return
    raise AssertionError("Expected ValueError")


def main() -> None:
    signature = inspect.signature(
        build_explicit_bare_pipe_thermal_condition_basis_v1
    )
    for name in EXPLICIT:
        assert signature.parameters[name].default is inspect.Parameter.empty

    basis = _basis()
    repeated = _basis()
    assert basis == repeated
    assert basis.surface_temperature_C == 60.0
    assert basis.ambient_air_temperature_C == 20.0
    assert basis.mean_radiant_temperature_C == 18.0
    assert basis.emissivity == 0.95
    assert basis.external_convection_coefficient_W_m2K == 5.0
    assert basis.status == (
        "Ready — explicit bare-pipe thermal conditions accepted"
    )

    copper = build_catalogue_bare_pipe_input_from_thermal_basis_v1(
        material_key="copper",
        catalogue_size_key=22,
        length_m=2.0,
        thermal_basis=basis,
    )
    steel = build_catalogue_bare_pipe_input_from_thermal_basis_v1(
        material_key="steel",
        catalogue_size_key=32,
        length_m=2.0,
        thermal_basis=basis,
    )
    assert math.isclose(copper.actual_outside_diameter_mm, 22.0)
    assert math.isclose(steel.actual_outside_diameter_mm, 42.4)

    calculation_input = copper.bare_pipe_heat_loss_input
    assert calculation_input.surface_temperature_C == 60.0
    assert calculation_input.ambient_air_temperature_C == 20.0
    assert calculation_input.mean_radiant_temperature_C == 18.0
    assert calculation_input.emissivity == 0.95
    assert calculation_input.external_convection_coefficient_W_m2K == 5.0
    assert math.isclose(calculation_input.outer_diameter_m, 0.022)

    result = compute_bare_pipe_heat_loss_v1(calculation_input)
    assert result.convection_heat_loss_W > 0.0
    assert result.radiation_heat_loss_W > 0.0
    assert math.isclose(
        result.total_heat_loss_W,
        result.convection_heat_loss_W + result.radiation_heat_loss_W,
        abs_tol=1.0e-12,
    )

    # Paint colour is deliberately absent from the authority.  Equal accepted
    # long-wave emissivity and conditions produce the same thermal basis.
    assert _basis(emissivity=0.95) == _basis(emissivity=0.95)

    _expect_value_error(surface_temperature_C=float("nan"))
    _expect_value_error(ambient_air_temperature_C=float("inf"))
    _expect_value_error(mean_radiant_temperature_C=-ABS_ZERO_C)
    _expect_value_error(emissivity=-0.01)
    _expect_value_error(emissivity=1.01)
    _expect_value_error(external_convection_coefficient_W_m2K=-0.01)

    try:
        build_catalogue_bare_pipe_input_from_thermal_basis_v1(
            material_key="copper",
            catalogue_size_key=22,
            length_m=2.0,
            thermal_basis=object(),
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Expected typed thermal-basis handoff")

    print(
        "OK — H-S66-C explicit bare-pipe thermal-condition basis "
        "authority passed."
    )


if __name__ == "__main__":
    main()
