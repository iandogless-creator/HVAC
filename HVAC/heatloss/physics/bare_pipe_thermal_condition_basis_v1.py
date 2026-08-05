# ======================================================================
# H-S66-C — Explicit bare-pipe thermal-condition basis authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.heatloss.physics.pipe_catalogue_heat_loss_input_v1 import (
    BarePipeCatalogueInputHandoffV1,
    build_bare_pipe_heat_loss_input_from_catalogue_v1,
)
from HVAC.heatloss.physics.pipe_radiation_engine import ABS_ZERO_C


@dataclass(frozen=True, slots=True)
class BarePipeThermalConditionBasisV1:
    """One explicit steady-state external thermal-condition basis.

    No value is inferred from pipe material, paint colour, water temperature,
    room temperature or a generic default.  The coefficient is an accepted
    external convection input, not a natural-convection correlation result.
    """

    surface_temperature_C: float
    ambient_air_temperature_C: float
    mean_radiant_temperature_C: float
    emissivity: float
    external_convection_coefficient_W_m2K: float
    status: str


def build_explicit_bare_pipe_thermal_condition_basis_v1(
        *,
        surface_temperature_C: float,
        ambient_air_temperature_C: float,
        mean_radiant_temperature_C: float,
        emissivity: float,
        external_convection_coefficient_W_m2K: float,
) -> BarePipeThermalConditionBasisV1:
    """Validate and freeze explicitly supplied bare-pipe conditions."""

    values = {
        "surface temperature": surface_temperature_C,
        "ambient air temperature": ambient_air_temperature_C,
        "mean radiant temperature": mean_radiant_temperature_C,
        "emissivity": emissivity,
        "external convection coefficient": (
            external_convection_coefficient_W_m2K
        ),
    }
    for label, value in values.items():
        if not math.isfinite(float(value)):
            raise ValueError(
                f"Bare-pipe thermal-condition {label} must be finite"
            )

    for label, temperature_C in (
        ("surface", surface_temperature_C),
        ("ambient air", ambient_air_temperature_C),
        ("mean radiant", mean_radiant_temperature_C),
    ):
        if temperature_C <= -ABS_ZERO_C:
            raise ValueError(
                f"Bare-pipe {label} temperature must be above absolute zero"
            )
    if not 0.0 <= emissivity <= 1.0:
        raise ValueError("Bare-pipe emissivity must be between 0 and 1")
    if external_convection_coefficient_W_m2K < 0.0:
        raise ValueError(
            "Bare-pipe external convection coefficient cannot be negative"
        )

    return BarePipeThermalConditionBasisV1(
        surface_temperature_C=float(surface_temperature_C),
        ambient_air_temperature_C=float(ambient_air_temperature_C),
        mean_radiant_temperature_C=float(mean_radiant_temperature_C),
        emissivity=float(emissivity),
        external_convection_coefficient_W_m2K=float(
            external_convection_coefficient_W_m2K
        ),
        status="Ready — explicit bare-pipe thermal conditions accepted",
    )


def build_catalogue_bare_pipe_input_from_thermal_basis_v1(
        *,
        material_key: object,
        catalogue_size_key: int,
        length_m: float,
        thermal_basis: BarePipeThermalConditionBasisV1,
) -> BarePipeCatalogueInputHandoffV1:
    """Combine one accepted thermal basis with exact catalogue OD authority."""

    if not isinstance(thermal_basis, BarePipeThermalConditionBasisV1):
        raise TypeError("BarePipeThermalConditionBasisV1 required")
    return build_bare_pipe_heat_loss_input_from_catalogue_v1(
        material_key=material_key,
        catalogue_size_key=catalogue_size_key,
        surface_temperature_C=thermal_basis.surface_temperature_C,
        ambient_air_temperature_C=thermal_basis.ambient_air_temperature_C,
        mean_radiant_temperature_C=thermal_basis.mean_radiant_temperature_C,
        length_m=length_m,
        emissivity=thermal_basis.emissivity,
        external_convection_coefficient_W_m2K=(
            thermal_basis.external_convection_coefficient_W_m2K
        ),
    )
