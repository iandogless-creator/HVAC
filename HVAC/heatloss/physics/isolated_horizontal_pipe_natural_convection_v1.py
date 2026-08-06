# ======================================================================
# H-S66-N2A — Isolated horizontal-pipe natural-convection authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math


ABSOLUTE_ZERO_C_V1 = 273.15
STANDARD_GRAVITY_M_S2_V1 = 9.80665
DRY_AIR_GAS_CONSTANT_J_KG_K_V1 = 287.058
DRY_AIR_CP_J_KG_K_V1 = 1006.0

# The v1 dry-air property correlations are deliberately bounded rather than
# extrapolated.  These limits cover normal occupied-building pipe conditions.
MIN_FILM_TEMPERATURE_K_V1 = 200.0
MAX_FILM_TEMPERATURE_K_V1 = 400.0
MIN_PRESSURE_PA_V1 = 50_000.0
MAX_PRESSURE_PA_V1 = 120_000.0
MAX_RAYLEIGH_NUMBER_V1 = 1.0e12

CORRELATION_SOURCE_V1 = (
    "Churchill-Chu natural convection from an isolated horizontal cylinder"
)
AIR_PROPERTY_SOURCE_V1 = (
    "Dry air at film temperature: ideal-gas density, Sutherland viscosity, "
    "temperature-dependent conductivity, cp=1006 J/(kg K)"
)


@dataclass(frozen=True, slots=True)
class IsolatedHorizontalPipeNaturalConvectionV1:
    """Auditable isolated-cylinder natural-convection evidence.

    The coefficient is positive.  The downstream heat-loss authority retains
    the sign through its surface-minus-air temperature difference.
    """

    outer_diameter_m: float
    surface_temperature_C: float
    ambient_air_temperature_C: float
    film_temperature_C: float
    pressure_Pa: float
    air_density_kg_m3: float
    dynamic_viscosity_Pa_s: float
    thermal_conductivity_W_mK: float
    specific_heat_capacity_J_kgK: float
    kinematic_viscosity_m2_s: float
    thermal_diffusivity_m2_s: float
    prandtl_number: float
    rayleigh_number: float
    nusselt_number: float
    external_convection_coefficient_W_m2K: float
    correlation_source: str
    air_property_source: str
    status: str


def build_isolated_horizontal_pipe_natural_convection_v1(
        *,
        outer_diameter_m: float,
        surface_temperature_C: float,
        ambient_air_temperature_C: float,
        pressure_Pa: float,
) -> IsolatedHorizontalPipeNaturalConvectionV1:
    """Resolve natural convection for one unobstructed horizontal cylinder.

    Churchill and Chu's all-Rayleigh-number horizontal-cylinder correlation is
    used up to Ra_D = 1e12.  Dry-air properties are evaluated once at the
    arithmetic film temperature.  No pipe-pair, wall, enclosure, draught or
    forced-convection correction is applied here.
    """

    values = {
        "outside diameter": outer_diameter_m,
        "surface temperature": surface_temperature_C,
        "ambient air temperature": ambient_air_temperature_C,
        "pressure": pressure_Pa,
    }
    clean: dict[str, float] = {}
    for label, value in values.items():
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Isolated-pipe natural-convection {label} must be numeric"
            ) from None
        if not math.isfinite(number):
            raise ValueError(
                f"Isolated-pipe natural-convection {label} must be finite"
            )
        clean[label] = number

    diameter_m = clean["outside diameter"]
    surface_C = clean["surface temperature"]
    ambient_C = clean["ambient air temperature"]
    pressure = clean["pressure"]

    if diameter_m <= 0.0:
        raise ValueError("Isolated horizontal-pipe outside diameter must be positive")
    if surface_C <= -ABSOLUTE_ZERO_C_V1 or ambient_C <= -ABSOLUTE_ZERO_C_V1:
        raise ValueError("Isolated-pipe temperatures must be above absolute zero")
    if not MIN_PRESSURE_PA_V1 <= pressure <= MAX_PRESSURE_PA_V1:
        raise ValueError(
            "Isolated-pipe dry-air pressure must be between 50000 and 120000 Pa"
        )

    film_C = 0.5 * (surface_C + ambient_C)
    film_K = film_C + ABSOLUTE_ZERO_C_V1
    if not MIN_FILM_TEMPERATURE_K_V1 <= film_K <= MAX_FILM_TEMPERATURE_K_V1:
        raise ValueError(
            "Isolated-pipe air-property film temperature must be between "
            "200 and 400 K"
        )

    density = pressure / (DRY_AIR_GAS_CONSTANT_J_KG_K_V1 * film_K)
    dynamic_viscosity = _dry_air_dynamic_viscosity_v1(film_K)
    conductivity = _dry_air_thermal_conductivity_v1(film_K)
    cp = DRY_AIR_CP_J_KG_K_V1
    kinematic_viscosity = dynamic_viscosity / density
    thermal_diffusivity = conductivity / (density * cp)
    prandtl = kinematic_viscosity / thermal_diffusivity
    beta = 1.0 / film_K
    temperature_difference_K = abs(surface_C - ambient_C)
    rayleigh = (
        STANDARD_GRAVITY_M_S2_V1
        * beta
        * temperature_difference_K
        * diameter_m ** 3
        / (kinematic_viscosity * thermal_diffusivity)
    )
    if rayleigh > MAX_RAYLEIGH_NUMBER_V1:
        raise ValueError(
            "Isolated horizontal-pipe Rayleigh number exceeds the v1 "
            "Churchill-Chu authority limit"
        )

    nusselt = (
        0.60
        + 0.387 * rayleigh ** (1.0 / 6.0)
        / (1.0 + (0.559 / prandtl) ** (9.0 / 16.0)) ** (8.0 / 27.0)
    ) ** 2
    coefficient = nusselt * conductivity / diameter_m

    return IsolatedHorizontalPipeNaturalConvectionV1(
        outer_diameter_m=diameter_m,
        surface_temperature_C=surface_C,
        ambient_air_temperature_C=ambient_C,
        film_temperature_C=film_C,
        pressure_Pa=pressure,
        air_density_kg_m3=density,
        dynamic_viscosity_Pa_s=dynamic_viscosity,
        thermal_conductivity_W_mK=conductivity,
        specific_heat_capacity_J_kgK=cp,
        kinematic_viscosity_m2_s=kinematic_viscosity,
        thermal_diffusivity_m2_s=thermal_diffusivity,
        prandtl_number=prandtl,
        rayleigh_number=rayleigh,
        nusselt_number=nusselt,
        external_convection_coefficient_W_m2K=coefficient,
        correlation_source=CORRELATION_SOURCE_V1,
        air_property_source=AIR_PROPERTY_SOURCE_V1,
        status="Calculated — isolated horizontal-pipe natural convection",
    )


def _dry_air_dynamic_viscosity_v1(temperature_K: float) -> float:
    """Sutherland correlation for dilute dry air."""

    reference_temperature_K = 273.15
    reference_viscosity_Pa_s = 1.716e-5
    sutherland_temperature_K = 111.0
    return (
        reference_viscosity_Pa_s
        * (temperature_K / reference_temperature_K) ** 1.5
        * (reference_temperature_K + sutherland_temperature_K)
        / (temperature_K + sutherland_temperature_K)
    )


def _dry_air_thermal_conductivity_v1(temperature_K: float) -> float:
    """Bounded engineering correlation for dry-air conductivity."""

    reference_temperature_K = 273.15
    reference_conductivity_W_mK = 0.0241
    conductivity_temperature_K = 194.0
    return (
        reference_conductivity_W_mK
        * (temperature_K / reference_temperature_K) ** 1.5
        * (reference_temperature_K + conductivity_temperature_K)
        / (temperature_K + conductivity_temperature_K)
    )
