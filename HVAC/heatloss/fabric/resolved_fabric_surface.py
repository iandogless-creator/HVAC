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
from typing import List

from HVAC.spaces.surface_engine_v1 import Surface


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
    Fully resolved fabric surface (read-only).

    Notes
    -----
    • `surface` carries geometry + identity (surface_id, name, class, area, etc.)
    • `room_id` is duplicated here as authoritative linkage for aggregation
    """
    surface: Surface

    # Authoritative linkage
    room_id: str

    # Resolved thermal properties
    u_value_W_m2K: float
    y_value_W_m2K: float

    # Provenance / linkage
    construction_id: str
    notes: str = ""

    @property
    def display_name(self) -> str:
        """
        UI-safe display label for this surface.

        Rules:
        • Never raises
        • Never touches ProjectState
        • Uses only local surface identity fields
        """
        return (
            getattr(self.surface, "name", None)
            or getattr(self.surface, "surface_id", None)
            or "unknown surface"
        )