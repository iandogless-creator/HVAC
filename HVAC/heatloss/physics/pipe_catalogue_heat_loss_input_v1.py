# ======================================================================
# H-S66-B — Exact catalogue outside-diameter heat-loss input handoff
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.heatloss.physics.pipe_radiation_engine import (
    BarePipeHeatLossInputV1,
)


@dataclass(frozen=True, slots=True)
class BarePipeCatalogueInputHandoffV1:
    """Resolved catalogue identity plus the exact H-S66-A calculation input."""

    material_key: str
    material_label: str
    catalogue_size_key: int
    actual_outside_diameter_mm: float
    actual_outside_diameter_m: float
    bare_pipe_heat_loss_input: BarePipeHeatLossInputV1
    status: str


def build_bare_pipe_heat_loss_input_from_catalogue_v1(
        *,
        material_key: object,
        catalogue_size_key: int,
        surface_temperature_C: float,
        ambient_air_temperature_C: float,
        mean_radiant_temperature_C: float,
        length_m: float,
        emissivity: float,
        external_convection_coefficient_W_m2K: float,
) -> BarePipeCatalogueInputHandoffV1:
    """Resolve actual exposed OD and construct one explicit H-S66-A input.

    ``catalogue_size_key`` retains material-specific semantics:

    * copper EN 1057 uses declared tube outside diameter in millimetres;
    * steel uses nominal DN/BSP pipe identity;
    * plastic and multilayer families retain their catalogue size keys.

    Heat-transfer area always uses ``PipeSize.od_mm``.  It is never inferred
    from DN, BSP wording, a display label, wall thickness or hydraulic bore.
    Thermal conditions remain explicit caller inputs; this handoff supplies
    no surface-temperature, emissivity or convection defaults.
    """

    key = str(material_key or "").strip().lower()
    material = get_material(key)
    if material is None:
        raise ValueError(
            f"Bare-pipe catalogue material is unavailable: {key or '—'}"
        )
    if isinstance(catalogue_size_key, bool) or not isinstance(
            catalogue_size_key,
            int,
    ):
        raise TypeError("Bare-pipe catalogue size key must be an integer")

    size = material.sizes.get(catalogue_size_key)
    if size is None:
        available = ", ".join(str(value) for value in sorted(material.sizes))
        raise ValueError(
            f"Bare-pipe catalogue size is unavailable for {key}: "
            f"{catalogue_size_key}; available keys: {available or '—'}"
        )

    outside_diameter_mm = float(size.od_mm)
    if not math.isfinite(outside_diameter_mm) or outside_diameter_mm <= 0.0:
        raise ValueError(
            f"Bare-pipe catalogue outside diameter is invalid for "
            f"{key} {catalogue_size_key}"
        )
    outside_diameter_m = outside_diameter_mm / 1000.0

    calculation_input = BarePipeHeatLossInputV1(
        surface_temperature_C=surface_temperature_C,
        ambient_air_temperature_C=ambient_air_temperature_C,
        mean_radiant_temperature_C=mean_radiant_temperature_C,
        outer_diameter_m=outside_diameter_m,
        length_m=length_m,
        emissivity=emissivity,
        external_convection_coefficient_W_m2K=(
            external_convection_coefficient_W_m2K
        ),
    )

    return BarePipeCatalogueInputHandoffV1(
        material_key=key,
        material_label=str(material.name),
        catalogue_size_key=catalogue_size_key,
        actual_outside_diameter_mm=outside_diameter_mm,
        actual_outside_diameter_m=outside_diameter_m,
        bare_pipe_heat_loss_input=calculation_input,
        status="Ready — exact catalogue outside diameter resolved",
    )
