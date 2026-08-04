# ======================================================================
# H-S66-B — Exact catalogue outside-diameter heat-loss input handoff
# ======================================================================

from __future__ import annotations

import math

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.heatloss.physics.pipe_catalogue_heat_loss_input_v1 import (
    build_bare_pipe_heat_loss_input_from_catalogue_v1,
)
from HVAC.heatloss.physics.pipe_radiation_engine import (
    compute_bare_pipe_heat_loss_v1,
)


THERMAL_INPUTS = {
    "surface_temperature_C": 60.0,
    "ambient_air_temperature_C": 20.0,
    "mean_radiant_temperature_C": 18.0,
    "length_m": 2.0,
    "emissivity": 0.95,
    "external_convection_coefficient_W_m2K": 5.0,
}


def _build(material_key: str, size_key: int):
    return build_bare_pipe_heat_loss_input_from_catalogue_v1(
        material_key=material_key,
        catalogue_size_key=size_key,
        **THERMAL_INPUTS,
    )


def _expect_error(error_type, **kwargs) -> None:
    try:
        build_bare_pipe_heat_loss_input_from_catalogue_v1(
            **kwargs,
            **THERMAL_INPUTS,
        )
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}")


def main() -> None:
    copper_material = get_material("copper")
    steel_material = get_material("steel")
    assert copper_material is not None
    assert steel_material is not None
    before_copper = repr(copper_material)
    before_steel = repr(steel_material)

    copper = _build("copper", 22)
    copper_repeated = _build("copper", 22)
    assert copper == copper_repeated
    assert copper.material_key == "copper"
    assert copper.material_label == "Copper EN1057"
    assert copper.catalogue_size_key == 22
    assert math.isclose(
        copper.actual_outside_diameter_mm,
        22.0,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        copper.actual_outside_diameter_m,
        0.022,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        copper.bare_pipe_heat_loss_input.outer_diameter_m,
        0.022,
        abs_tol=1.0e-12,
    )
    assert copper.bare_pipe_heat_loss_input.surface_temperature_C == 60.0
    assert copper.bare_pipe_heat_loss_input.emissivity == 0.95
    assert copper.status == "Ready — exact catalogue outside diameter resolved"

    copper_loss = compute_bare_pipe_heat_loss_v1(
        copper.bare_pipe_heat_loss_input
    )
    assert math.isclose(
        copper_loss.exposed_area_m2,
        math.pi * 0.022 * 2.0,
        abs_tol=1.0e-12,
    )

    # Steel size key 32 is nominal DN/BSP identity.  Its exposed pipe OD is
    # the exact catalogue 42.4 mm — never 32 mm and never the 35.1 mm bore.
    steel = _build("steel", 32)
    assert steel.material_label == "Steel Medium"
    assert steel.catalogue_size_key == 32
    assert math.isclose(
        steel.actual_outside_diameter_mm,
        42.4,
        abs_tol=1.0e-12,
    )
    assert not math.isclose(steel.actual_outside_diameter_mm, 32.0)
    assert not math.isclose(steel.actual_outside_diameter_mm, 35.1)
    steel_loss = compute_bare_pipe_heat_loss_v1(
        steel.bare_pipe_heat_loss_input
    )
    assert math.isclose(
        steel_loss.exposed_area_m2,
        math.pi * 0.0424 * 2.0,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        steel_loss.total_heat_loss_W / copper_loss.total_heat_loss_W,
        42.4 / 22.0,
        abs_tol=1.0e-12,
    )

    mlcp = _build("mlcp", 26)
    pex = _build("pex", 20)
    assert math.isclose(mlcp.actual_outside_diameter_mm, 26.0)
    assert math.isclose(pex.actual_outside_diameter_mm, 20.0)

    assert repr(copper_material) == before_copper
    assert repr(steel_material) == before_steel

    _expect_error(
        ValueError,
        material_key="unknown",
        catalogue_size_key=22,
    )
    _expect_error(
        ValueError,
        material_key="steel",
        catalogue_size_key=22,
    )
    _expect_error(
        TypeError,
        material_key="copper",
        catalogue_size_key=22.0,
    )
    _expect_error(
        TypeError,
        material_key="copper",
        catalogue_size_key=True,
    )

    print(
        "OK — H-S66-B exact catalogue outside-diameter handoff to "
        "bare-pipe heat-loss inputs passed."
    )


if __name__ == "__main__":
    main()
