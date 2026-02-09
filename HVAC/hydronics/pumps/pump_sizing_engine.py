"""
HVACgooee — Pump Sizing Engine (Core v1)
=======================================

Purpose
-------
Provide core physics and sizing helpers for circulation pumps:

- Convert flow (L/h) + pressure drop (Pa) → pump duty point.
- Compute hydraulic power (W).
- Compute electrical input power (W) given efficiency.
- Apply safety / oversizing margins.
- Provide a clean data structure for GUI + reports.

This module is deliberately simple and generic:

• NO GUI
• NO DXF
• NO manufacturer databases (those can be separate add-ons)

Future expansions:
------------------
- Pump curve matching (select from manufacturer data).
- Variable-speed pump optimisation.
- Noise and NPSH checks (separate module).
"""

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class PumpDuty:
    """
    Represents the required duty point of a pump.
    """
    flow_lph: float               # volumetric flow (L/h)
    head_m: float                 # head (m of water)
    dp_Pa: float                  # equivalent pressure (Pa)


@dataclass
class PumpSizingConfig:
    """
    Configuration for pump sizing calculations.

    Attributes
    ----------
    efficiency : float
        Overall pump + motor efficiency (0–1).
    safety_factor_head : float
        Multiplicative safety factor applied to head.
    safety_factor_flow : float
        Multiplicative safety factor applied to flow.
    water_density_kg_m3 : float
        Density of water (kg/m³).
    g_m_s2 : float
        Gravitational acceleration (m/s²).
    """
    efficiency: float = 0.45
    safety_factor_head: float = 1.10
    safety_factor_flow: float = 1.05
    water_density_kg_m3: float = 1000.0
    g_m_s2: float = 9.81


@dataclass
class PumpSizingResult:
    """
    Output container for pump sizing results.
    """
    duty: PumpDuty
    hydraulic_power_W: float
    electrical_power_W: float
    config_used: PumpSizingConfig


# ---------------------------------------------------------------------------
# Core Calculations
# ---------------------------------------------------------------------------

def dp_Pa_to_head_m(dp_Pa: float, rho: float = 1000.0, g: float = 9.81) -> float:
    """
    Convert pressure drop (Pa) to head (m of water):

        H = ΔP / (ρ g)
    """
    if rho <= 0 or g <= 0:
        raise ValueError("Density and gravity must be positive.")
    return dp_Pa / (rho * g)


def head_m_to_dp_Pa(head_m: float, rho: float = 1000.0, g: float = 9.81) -> float:
    """
    Convert head (m of water) to pressure (Pa):

        ΔP = ρ g H
    """
    return rho * g * head_m


def hydraulic_power_W(flow_lph: float, dp_Pa: float) -> float:
    """
    Hydraulic power:

        P = Q * ΔP

    where:
        Q = volumetric flow (m³/s)
        ΔP = pressure (Pa)

    Flow conversion:
        L/h → m³/s
    """
    flow_m3_s = flow_lph / 1000.0 / 3600.0
    return flow_m3_s * dp_Pa


# ---------------------------------------------------------------------------
# Sizing API
# ---------------------------------------------------------------------------

def size_pump_from_flow_and_dp(
    flow_lph: float,
    total_dp_Pa: float,
    cfg: Optional[PumpSizingConfig] = None,
) -> PumpSizingResult:
    """
    Size a circulation pump based on required flow and pressure drop.

    Parameters
    ----------
    flow_lph : float
        Required system flow (L/h).
    total_dp_Pa : float
        Total system pressure drop at that flow (Pa).
    cfg : PumpSizingConfig
        Sizing configuration (safety factors, efficiency, etc.)

    Returns
    -------
    PumpSizingResult
    """
    cfg = cfg or PumpSizingConfig()

    if flow_lph <= 0:
        raise ValueError("flow_lph must be positive.")
    if total_dp_Pa <= 0:
        raise ValueError("total_dp_Pa must be positive.")

    # Apply safety factors
    flow_sf = flow_lph * cfg.safety_factor_flow
    dp_sf = total_dp_Pa * cfg.safety_factor_head

    # Convert to head
    head_m = dp_Pa_to_head_m(dp_sf, cfg.water_density_kg_m3, cfg.g_m_s2)

    # Hydraulic power at design point
    P_hyd = hydraulic_power_W(flow_sf, dp_sf)

    # Electrical input power (simple: P_elec = P_hyd / η)
    if cfg.efficiency <= 0 or cfg.efficiency > 1:
        raise ValueError("efficiency must be between 0 and 1.")
    P_elec = P_hyd / cfg.efficiency

    duty = PumpDuty(
        flow_lph=flow_sf,
        head_m=head_m,
        dp_Pa=dp_sf,
    )

    return PumpSizingResult(
        duty=duty,
        hydraulic_power_W=P_hyd,
        electrical_power_W=P_elec,
        config_used=cfg,
    )
