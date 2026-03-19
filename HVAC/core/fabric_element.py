# ======================================================================
# HVAC/core/fabric_element.py
# ======================================================================
"""
HVACgooee — Fabric Element v1 (CANONICAL)

A FabricElement is *declared modelling intent* stored inside RoomStateV1.

It is NOT a geometric surface.
It is the minimal heat-loss modelling unit (U × A × ΔT).

Notes
-----
• Stored in RoomStateV1.fabric_elements
• A construction_id references ProjectState.construction_library (v1)
• Later versions can extend with adjacency, internal ΔT rules, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class FabricElementV1:
    element_class: str          # e.g. "external_wall", "window", "door", "roof", "floor"
    area_m2: float
    construction_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "element_class": self.element_class,
            "area_m2": float(self.area_m2),
            "construction_id": self.construction_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FabricElementV1":
        return cls(
            element_class=str(data["element_class"]),
            area_m2=float(data["area_m2"]),
            construction_id=data.get("construction_id"),
        )