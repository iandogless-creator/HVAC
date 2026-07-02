from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ColebrookFrictionFactorResultV1:
    friction_factor: float
    iteration_count: int
    converged: bool
    residual: float
    method: str
    status: str


def reynolds_number(
    *,
    velocity_m_s: float,
    internal_diameter_m: float,
    density_kg_m3: float | None = None,
    dynamic_viscosity_pa_s: float | None = None,
    kinematic_viscosity_m2_s: float | None = None,
) -> float:
    """
    Return Reynolds number.

    Supports either:
        Re = vD / nu

    or:
        Re = rho v D / mu
    """
    if velocity_m_s <= 0.0:
        return 0.0

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    if kinematic_viscosity_m2_s is not None:
        if kinematic_viscosity_m2_s <= 0.0:
            raise ValueError("kinematic_viscosity_m2_s must be > 0")
        return velocity_m_s * internal_diameter_m / kinematic_viscosity_m2_s

    if density_kg_m3 is None or dynamic_viscosity_pa_s is None:
        raise ValueError(
            "Either kinematic_viscosity_m2_s or both "
            "density_kg_m3 and dynamic_viscosity_pa_s are required"
        )

    if density_kg_m3 <= 0.0:
        raise ValueError("density_kg_m3 must be > 0")

    if dynamic_viscosity_pa_s <= 0.0:
        raise ValueError("dynamic_viscosity_pa_s must be > 0")

    return (
        density_kg_m3
        * velocity_m_s
        * internal_diameter_m
        / dynamic_viscosity_pa_s
    )


def haaland_friction_factor(
    *,
    reynolds_number: float,
    relative_roughness: float,
) -> float:
    """
    Return Darcy friction factor using:

    Laminar:
        f = 64 / Re

    Turbulent/transitional preview:
        Haaland explicit approximation.
    """
    if reynolds_number <= 0.0:
        return 0.0

    if relative_roughness < 0.0:
        raise ValueError("relative_roughness must be >= 0")

    if reynolds_number < 2300.0:
        return 64.0 / reynolds_number

    term = ((relative_roughness / 3.7) ** 1.11) + (
        6.9 / reynolds_number
    )

    if term <= 0.0:
        return 0.0

    inverse_sqrt_f = -1.8 * math.log10(term)

    if inverse_sqrt_f <= 0.0:
        return 0.0

    return 1.0 / inverse_sqrt_f**2


def colebrook_friction_factor(
    *,
    reynolds_number: float,
    relative_roughness: float,
    tolerance: float = 1.0e-6,
    max_iterations: int = 100,
    initial_guess_method: str = "haaland",
) -> ColebrookFrictionFactorResultV1:
    """
    Solve Colebrook-White for Darcy friction factor.

    Uses Haaland as the default first estimate.
    Returns iteration metadata for engineering preview/debug use.
    """
    if reynolds_number <= 0.0:
        return ColebrookFrictionFactorResultV1(
            friction_factor=0.0,
            iteration_count=0,
            converged=True,
            residual=0.0,
            method="none",
            status="No flow",
        )

    if relative_roughness < 0.0:
        raise ValueError("relative_roughness must be >= 0")

    if tolerance <= 0.0:
        raise ValueError("tolerance must be > 0")

    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")

    if reynolds_number < 2300.0:
        return ColebrookFrictionFactorResultV1(
            friction_factor=64.0 / reynolds_number,
            iteration_count=0,
            converged=True,
            residual=0.0,
            method="laminar",
            status="Laminar — f = 64/Re",
        )

    if initial_guess_method == "haaland":
        f = haaland_friction_factor(
            reynolds_number=reynolds_number,
            relative_roughness=relative_roughness,
        )
        method = "colebrook(initial=haaland)"
    elif initial_guess_method == "fixed_0.02":
        f = 0.02
        method = "colebrook(initial=fixed_0.02)"
    else:
        raise ValueError(
            "initial_guess_method must be 'haaland' or 'fixed_0.02'"
        )

    if f <= 0.0:
        f = 0.02

    residual = _colebrook_residual(
        friction_factor=f,
        reynolds_number=reynolds_number,
        relative_roughness=relative_roughness,
    )

    for iteration_count in range(1, max_iterations + 1):
        sqrt_f = math.sqrt(f)

        term = (
            relative_roughness / 3.7
            + 2.51 / (reynolds_number * sqrt_f)
        )

        if term <= 0.0:
            break

        next_f = (-2.0 * math.log10(term)) ** -2

        residual = _colebrook_residual(
            friction_factor=next_f,
            reynolds_number=reynolds_number,
            relative_roughness=relative_roughness,
        )

        if residual <= tolerance:
            return ColebrookFrictionFactorResultV1(
                friction_factor=next_f,
                iteration_count=iteration_count,
                converged=True,
                residual=residual,
                method=method,
                status="Converged",
            )

        f = next_f

    return ColebrookFrictionFactorResultV1(
        friction_factor=f,
        iteration_count=max_iterations,
        converged=False,
        residual=residual,
        method=method,
        status="Did not converge within max_iterations",
    )


def darcy_weisbach_pressure_gradient(
    *,
    friction_factor: float,
    density_kg_m3: float,
    velocity_m_s: float,
    internal_diameter_m: float,
) -> float:
    """
    Darcy-Weisbach pressure gradient:

        Δp/L = f × rho × v² / (2D)
    """
    if friction_factor <= 0.0 or velocity_m_s <= 0.0:
        return 0.0

    if density_kg_m3 <= 0.0:
        raise ValueError("density_kg_m3 must be > 0")

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    return (
        friction_factor
        * density_kg_m3
        * velocity_m_s**2
        / (2.0 * internal_diameter_m)
    )


def darcy_weisbach_pressure_drop(
    *,
    friction_factor: float,
    length_m: float,
    internal_diameter_m: float,
    density_kg_m3: float,
    velocity_m_s: float,
) -> float:
    """
    Darcy-Weisbach pressure drop:

        Δp = f × L/D × rho × v²/2
    """
    if length_m <= 0.0:
        return 0.0

    return (
        darcy_weisbach_pressure_gradient(
            friction_factor=friction_factor,
            density_kg_m3=density_kg_m3,
            velocity_m_s=velocity_m_s,
            internal_diameter_m=internal_diameter_m,
        )
        * length_m
    )


def _colebrook_residual(
    *,
    friction_factor: float,
    reynolds_number: float,
    relative_roughness: float,
) -> float:
    if friction_factor <= 0.0:
        return float("inf")

    sqrt_f = math.sqrt(friction_factor)

    term = (
        relative_roughness / 3.7
        + 2.51 / (reynolds_number * sqrt_f)
    )

    if term <= 0.0:
        return float("inf")

    return abs(
        (1.0 / sqrt_f)
        + 2.0 * math.log10(term)
    )