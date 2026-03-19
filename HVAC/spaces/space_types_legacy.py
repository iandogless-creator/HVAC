"""
space_types.py
--------------

HVACgooee — Space Model v1 (pipeline-safe)

Defines the canonical Space object used by:
    • SpacesManager
    • Heat-loss engines (later)
    • Ventilation engines (later)
    • Future adjacency + zoning logic

V1 RULES
--------
• Space does NOT own geometry
• Geometry is attached structurally by SpacesManager
• Height is uniform per space
• No constructions, no adjacencies yet
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Space:
    """
    Canonical Space object (v1).

    Geometry is NOT stored here.
    Geometry ownership belongs to SpacesManager.
    """

    # Identity
    name: str

    # Vertical intent
    height_m: float = 2.4  # ← DEFAULT HEIGHT (CRITICAL)

    # Thermal intent
    design_temp_C: float = 21.0
