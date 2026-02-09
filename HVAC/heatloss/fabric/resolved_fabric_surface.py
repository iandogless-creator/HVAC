# ======================================================================
# HVAC/heatloss/fabric/resolved_fabric_surface.py
# ======================================================================

"""
HVACgooee — Resolved Fabric Surface DTO (v1)
--------------------------------------------

Canonical upstream fabric result object consumed by heat-loss
aggregation (room qf).

This DTO represents a *fully resolved* fabric surface:
    • Geometry is known
    • U-value is fixed
    • Dynamic effects (Y) are resolved
    • Linear bridges (Ψ) are resolved

RULES
-----
• NO construction logic
• NO layer data
• NO calculations beyond aggregation
• NO mutation after creation
• Heat-loss may only READ this object
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from HVAC_legacy.spaces.surface_engine_v1 import Surface


# ----------------------------------------------------------------------
# Supporting DTO — Linear Thermal Bridge
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class LinearThermalBridge:
    """
    Resolved linear thermal bridge (Ψ-term).

    Units:
        psi_W_mK : W/m·K
        length_m : m
    """
    description: str
    psi_W_mK: float
    length_m: float


# ----------------------------------------------------------------------
# Core DTO — Resolved Fabric Surface
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ResolvedFabricSurface:
    """
    Fully resolved fabric surface ready for heat-loss aggregation.

    This object is the ONLY fabric input allowed into room qf.
    """

    # --------------------------------------------------------------
    # Geometry (authoritative)
    # --------------------------------------------------------------
    surface: Surface

    # --------------------------------------------------------------
    # Fabric transmission
    # --------------------------------------------------------------
    u_value_W_m2K: float

    # --------------------------------------------------------------
    # Dynamic / intermittency effect (optional)
    # --------------------------------------------------------------
    y_value_W_m2K: float = 0.0

    # --------------------------------------------------------------
    # Linear thermal bridges (optional)
    # --------------------------------------------------------------
    linear_bridges: Optional[List[LinearThermalBridge]] = None

    # --------------------------------------------------------------
    # Metadata (non-functional)
    # --------------------------------------------------------------
    construction_id: Optional[str] = None
    notes: Optional[str] = None
