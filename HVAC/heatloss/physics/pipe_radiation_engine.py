"""
pipe_radiation_engine.py
------------------------

HVACgooee — Pipe Radiation Physics Engine (v1.1, LOCKED)

Subsystem
=========
Heat-Loss → Physics (CORE)

Purpose
=======
Provides HVAC-grade radiative heat-loss calculations for pipework:

    • Radiation from a long cylindrical pipe to ambient
    • Bundle / parallel pipe view-factor approximations
    • Convenience helpers for hydronic distribution losses

This module owns ALL radiative heat-transfer physics.
Hydronics and other subsystems may import and use it,
but MUST NOT re-implement radiation logic.

Design Intent
=============
• Grey, diffuse surfaces
• Long cylinders (L ≫ D)
• HVAC temperature ranges (≈ 0–120 °C)
• Engineering approximations (not furnace-grade radiation)

This file is CORE PHYSICS and must remain GPL / stable.
"""

# =====================================================================
# IMPORTS
# =====================================================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.data.pipe_emissivity import suggest_emissivity

# =====================================================================
# CONSTANTS
# =====================================================================
STEFAN_BOLTZMANN = 5.670374419e-8  # W / m² · K⁴
ABS_ZERO_C = 273.15

# =====================================================================
# DATA STRUCTURES
# =====================================================================

@dataclass(frozen=True)
class PipeRadiationInput:
    """
    Canonical input set for pipe radiation.

    All temperatures are surface / ambient bulk values.
    """
    surface_temperature_C: float
    ambient_temperature_C: float
    outer_diameter_m: float
    length_m: float
    emissivity: float
    view_factor_to_env: float = 1.0


@dataclass(frozen=True)
class PipeRadiationResult:
    """
    Canonical radiation result.
    """
    area_m2: float
    heat_loss_W: float
    heat_loss_W_per_m: float
    emissivity_used: float
    view_factor_to_env: float


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def _to_kelvin(temp_c: float) -> float:
    """Convert Celsius to Kelvin."""
    return temp_c + ABS_ZERO_C


def _clamp_01(x: float) -> float:
    """Clamp value into [0, 1]."""
    return max(0.0, min(1.0, float(x)))


# =====================================================================
# CORE RADIATION CALCULATION
# =====================================================================

def compute_pipe_radiation(
    input_data: PipeRadiationInput,
) -> PipeRadiationResult:
    """
    Compute radiative heat loss from a cylindrical pipe:

        q = ε · σ · F · A · (T_s⁴ − T_env⁴)

    Where:
        A = π · D · L

    Returns total loss and loss per metre.
    """
    eps = _clamp_01(input_data.emissivity)
    F = _clamp_01(input_data.view_factor_to_env)

    T_s = _to_kelvin(input_data.surface_temperature_C)
    T_env = _to_kelvin(input_data.ambient_temperature_C)

    area = 3.141592653589793 * input_data.outer_diameter_m * input_data.length_m

    q = eps * STEFAN_BOLTZMANN * F * area * (T_s**4 - T_env**4)

    q_per_m = q / input_data.length_m if input_data.length_m > 0 else 0.0

    return PipeRadiationResult(
        area_m2=area,
        heat_loss_W=q,
        heat_loss_W_per_m=q_per_m,
        emissivity_used=eps,
        view_factor_to_env=F,
    )


# =====================================================================
# VIEW-FACTOR APPROXIMATIONS (ENGINEERING-LEVEL)
# =====================================================================

def approximate_view_factor_parallel_pipes(
    diameter_m: float,
    centre_spacing_m: float,
) -> float:
    """
    Approximate view factor for two parallel long cylinders.

    This is an HVAC-grade approximation, NOT a full radiation solution.

    Behaviour:
        • Touching / very tight → F ≈ 0.6–0.7
        • Typical bundles     → F ≈ 0.3–0.5
        • Widely spaced       → F → 0.01–0.05
    """
    D = max(1e-6, float(diameter_m))
    S = max(D * 1.001, float(centre_spacing_m))

    gap = max(1e-6, S - D)
    g_over_D = gap / D

    if g_over_D <= 0.1:
        F = 0.65
    elif g_over_D <= 0.5:
        F = 0.65 - (0.35 * (g_over_D - 0.1) / 0.4)
    elif g_over_D <= 2.0:
        F = max(0.05, 0.30 * (0.5 / g_over_D))
    else:
        F = 0.01

    return _clamp_01(F)


def bundle_radiation_correction_factor(
    emissivity: float,
    n_pipes: int,
    diameter_m: float,
    centre_spacing_m: float,
) -> float:
    """
    Estimate fractional radiation loss for a pipe bundle:

        q_bundle = q_isolated × correction

    correction ≈ fraction of pipe surface still seeing the environment.
    """
    if n_pipes <= 1:
        return 1.0

    eps = _clamp_01(emissivity)
    F_pair = approximate_view_factor_parallel_pipes(diameter_m, centre_spacing_m)

    if n_pipes == 2:
        neighbour_fraction = F_pair * eps
    else:
        neighbour_fraction = min(0.8, 2.0 * F_pair * eps)

    F_env = max(0.0, 1.0 - neighbour_fraction)

    # Do not allow unrealistically low radiation
    return max(0.2, F_env)


# =====================================================================
# CONVENIENCE WRAPPERS (SAFE FOR HYDRONICS)
# =====================================================================

def estimate_radiative_loss_per_m_simple(
    surface_temperature_C: float,
    ambient_temperature_C: float,
    outer_diameter_m: float,
    emissivity_key: Optional[str],
) -> float:
    """
    Isolated pipe radiation loss per metre (F = 1).
    """
    eps = suggest_emissivity(emissivity_key, fallback=0.90)

    inp = PipeRadiationInput(
        surface_temperature_C=surface_temperature_C,
        ambient_temperature_C=ambient_temperature_C,
        outer_diameter_m=outer_diameter_m,
        length_m=1.0,
        emissivity=eps,
        view_factor_to_env=1.0,
    )
    return compute_pipe_radiation(inp).heat_loss_W_per_m


def estimate_radiative_loss_per_m_bundle(
    surface_temperature_C: float,
    ambient_temperature_C: float,
    outer_diameter_m: float,
    emissivity_key: Optional[str],
    n_pipes: int,
    centre_spacing_m: float,
) -> float:
    """
    Bundle-corrected radiation loss per metre.
    """
    eps = suggest_emissivity(emissivity_key, fallback=0.90)

    q_iso = estimate_radiative_loss_per_m_simple(
        surface_temperature_C,
        ambient_temperature_C,
        outer_diameter_m,
        emissivity_key,
    )

    correction = bundle_radiation_correction_factor(
        emissivity=eps,
        n_pipes=n_pipes,
        diameter_m=outer_diameter_m,
        centre_spacing_m=centre_spacing_m,
    )

    return q_iso * correction
