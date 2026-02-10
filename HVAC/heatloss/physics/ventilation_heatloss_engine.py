"""
ventilation_heatloss_engine.py
------------------------------

Ventilation & infiltration heat-loss engine for HVACgooee.

Supports:
    - ACH method (Air Changes per Hour)
    - Direct volumetric flow (m³/s, m³/h, L/s)
    - Temperature-driven sensible losses

Formula:
    Q = Vdot * rho * cp * (Ti - Te)

    rho ≈ 1.20 kg/m³     (air density)
    cp  ≈ 1005 J/kg·K    (specific heat)
"""

"""
ventilation_heatloss_engine.py
------------------------------

Ventilation & infiltration heat-loss engine for HVACgooee.

Supports:
    - ACH method (Air Changes per Hour)
    - Direct volumetric flow (m³/s, m³/h, L/s)
    - Sensible heat loss only (steady-state)

Formula:
    Q = V̇ · ρ · cₚ · (Ti − Te)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.constants.thermal import (
    DENSITY_AIR,
    SHC_AIR,
    SECONDS_PER_HOUR,
)


# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------

@dataclass
class VentilationParams:
    """
    Defines ventilation for a room.

    Provide ONE of:
        - ach            Air changes per hour
        - flow_m3_s      Volumetric flow (m³/s)
        - flow_l_s       Volumetric flow (L/s)
        - flow_m3_h      Volumetric flow (m³/h)
    """
    ach: Optional[float] = None
    flow_m3_s: Optional[float] = None
    flow_l_s: Optional[float] = None
    flow_m3_h: Optional[float] = None


# ------------------------------------------------------------------
# Conversions
# ------------------------------------------------------------------

def compute_airflow_m3_s(
    params: VentilationParams,
    room_volume_m3: float,
) -> float:
    """
    Convert ventilation specification to m³/s.

    Priority:
        1. m³/s
        2. L/s
        3. m³/h
        4. ACH
    """

    if params.flow_m3_s is not None:
        return params.flow_m3_s

    if params.flow_l_s is not None:
        return params.flow_l_s / 1000.0

    if params.flow_m3_h is not None:
        return params.flow_m3_h / SECONDS_PER_HOUR

    if params.ach is not None:
        return params.ach * room_volume_m3 / SECONDS_PER_HOUR

    return 0.0


# ------------------------------------------------------------------
# Core calculation
# ------------------------------------------------------------------

def compute_ventilation_loss(
    params: VentilationParams,
    room_volume_m3: float,
    temp_inside_C: float,
    temp_outside_C: float,
) -> float:
    """
    Compute sensible ventilation heat loss (W).

        Q = V̇ · ρ · cₚ · ΔT
    """

    delta_t = temp_inside_C - temp_outside_C
    if delta_t <= 0.0:
        return 0.0

    vdot = compute_airflow_m3_s(params, room_volume_m3)

    return vdot * DENSITY_AIR * SHC_AIR * delta_t
