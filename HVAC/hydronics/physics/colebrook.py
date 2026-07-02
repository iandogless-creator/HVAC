# ------------------
# HVAC/hydronics/physics/colebrook.py
# Compatibility wrapper around shared fluid-friction core.
#
# H-S29-B:
# Preserve legacy hydronics imports:
#   colebrook(...)
#   reynolds_number(...)
#   darcy_weisbach(...)
#   CalcPipe(...)
#
# New canonical physics lives in:
#   HVAC.core.fluid_friction.friction_factor_v1
# ------------------

from __future__ import annotations

import math

from HVAC.core.fluid_friction.friction_factor_v1 import (
    colebrook_friction_factor,
    darcy_weisbach_pressure_drop,
    reynolds_number as _shared_reynolds_number,
)


def colebrook(Re, eD, tol=1e-6, max_iter=100):
    """
    Legacy-compatible Colebrook friction factor call.

    Re:
        Reynolds number

    eD:
        Relative roughness epsilon / diameter

    Returns:
        Darcy friction factor only, preserving the old public API.
    """
    result = colebrook_friction_factor(
        reynolds_number=float(Re),
        relative_roughness=float(eD),
        tolerance=float(tol),
        max_iterations=int(max_iter),
        initial_guess_method="haaland",
    )

    return result.friction_factor


def reynolds_number(velocity, diameter, kinematic_viscosity):
    """
    Legacy-compatible Reynolds number call.

    Old API:
        Re = velocity * diameter / kinematic_viscosity
    """
    return _shared_reynolds_number(
        velocity_m_s=float(velocity),
        internal_diameter_m=float(diameter),
        kinematic_viscosity_m2_s=float(kinematic_viscosity),
    )


def CalcPipe(
        flow_rate,
        diameter,
        length,
        roughness,
        density,
        kinematic_viscosity,
):
    """
    Legacy-compatible combined pipe calculator.

    Important:
        flow_rate is volumetric flow rate in m³/s.

    Hydronics mass flow kg/s must be converted before calling this legacy
    wrapper. Do not pass kg/s directly.
    """
    diameter = float(diameter)
    flow_rate = float(flow_rate)

    if diameter <= 0.0:
        raise ValueError("diameter must be > 0")

    area = math.pi * diameter**2 / 4.0
    velocity = flow_rate / area if flow_rate > 0.0 else 0.0

    Re = reynolds_number(
        velocity,
        diameter,
        kinematic_viscosity,
    )

    eD = float(roughness) / diameter

    f = colebrook(
        Re,
        eD,
    )

    dp = darcy_weisbach(
        f,
        length,
        diameter,
        density,
        velocity,
    )

    return {
        "velocity": velocity,
        "Re": Re,
        "friction_factor": f,
        "pressure_drop": dp,
    }


def darcy_weisbach(f, length, diameter, density, velocity):
    """
    Legacy-compatible Darcy-Weisbach pressure drop call.

    Returns pressure drop in Pa.
    """
    return darcy_weisbach_pressure_drop(
        friction_factor=float(f),
        length_m=float(length),
        internal_diameter_m=float(diameter),
        density_kg_m3=float(density),
        velocity_m_s=float(velocity),
    )