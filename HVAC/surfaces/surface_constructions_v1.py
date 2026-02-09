"""
surface_constructions_v1.py
---------------------------

HVACgooee — Surface ↔ Construction Bridge (v1.1, 2025 edition)

This module enriches geometric surfaces with construction physics:

    • U-values
    • Areal heat capacity (C_areal)
    • Dynamic thermal admittance Y [W/m²K]
    • Decrement factor f
    • Time lag φ [hours]

It does NOT compute heat loss. That is handled by HeatLossController.
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from HVAC_legacy.spaces.surface_engine_v1 import Surface, SurfaceType
from HVAC_legacy.heatloss.physics.constructions import Construction
from HVAC_legacy.heatloss.physics.y_value_engine import compute_y_value
# ================================================================
# END IMPORTS
# ================================================================



# ================================================================
# BEGIN DATA STRUCTURES
# ================================================================

@dataclass
class SurfaceConstructed:
    """
    A geometric surface with its assigned construction
    and all derived thermal properties.
    """
    surface: Surface
    construction: Construction

    # Steady-state
    u_value_W_m2K: float
    C_areal_J_m2K: float

    # Dynamic (periodic) thermal parameters
    Y_value_W_m2K: float
    decrement_factor_f: float
    time_lag_hours_phi: float
# ================================================================
# END DATA STRUCTURES
# ================================================================



# ================================================================
# BEGIN CORE FUNCTION
# ================================================================
def assign_constructions_to_surfaces(
    surfaces: List[Surface],
    construction_map: Dict[SurfaceType, Construction],
    *,
    heating_period: str = "24h",
) -> List[SurfaceConstructed]:
    """
    Create SurfaceConstructed objects by attaching Construction physics.

    Steps:
        • Look up construction by SurfaceType
        • cons.recalc() ensures U and C_areal are up to date
        • Compute dynamic Y-value
        • Estimate decrement factor f and time lag φ

    Returns:
        List[SurfaceConstructed]
    """
    results: List[SurfaceConstructed] = []

    for surf in surfaces:
        cons = construction_map.get(surf.surface_type, None)
        if cons is None:
            continue

        # Recalculate construction physics
        cons.recalc()

        U = cons.U_value
        C_areal = cons.C_areal

        # ---- Dynamic Y-value ----
        Y = compute_y_value(
            surface_type=surf.surface_type.name.lower(),
            U=U,
            period=heating_period,
            C_areal=C_areal,
        )

        # ---- Derive f and φ from simplified physical relationships ----
        # Educational approximations (bounded, monotonic):
        #
        #   f ≈ Y / (U + 1e-9) * 0.25     → 0–1 range
        #   φ ≈ (C_areal / 36000) hours  → typical 0–12 h
        #
        # These are placeholders until the full ISO 13786 engine arrives.

        if U > 0:
            decrement_f = min(1.0, max(0.0, (Y / (U + 1e-9)) * 0.25))
        else:
            decrement_f = 0.0

        time_lag_h = max(0.0, min(12.0, C_areal / 36000.0))

        # Bundle everything
        results.append(
            SurfaceConstructed(
                surface=surf,
                construction=cons,
                u_value_W_m2K=U,
                C_areal_J_m2K=C_areal,
                Y_value_W_m2K=Y,
                decrement_factor_f=decrement_f,
                time_lag_hours_phi=time_lag_h,
            )
        )

    return results
# ================================================================
# END CORE FUNCTION
# ================================================================
