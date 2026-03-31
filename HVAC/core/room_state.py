# ======================================================================
# HVAC/core/room_state.py
# ======================================================================
"""
HVACgooee — Room State v1 (CANONICAL)

Authority
---------
• Owns modelling intent only
• No GUI logic
• No physics
• No derived duplication
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from HVAC.core.fabric_element import FabricElementV1
from HVAC.core.room_geometry import RoomGeometryV1


# ======================================================================
# RoomStateV1
# ======================================================================

@dataclass(slots=True)
class RoomStateV1:

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    room_id: str
    name: str

    # ------------------------------------------------------------------
    # Authoritative intent
    # ------------------------------------------------------------------
    geometry: RoomGeometryV1 = field(default_factory=RoomGeometryV1)
    fabric_elements: List[FabricElementV1] = field(default_factory=list)

    internal_temp_override_C: Optional[float] = None
    ach_override: Optional[float] = None

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "geometry": self.geometry.to_dict(),
            "internal_temp_override_C": self.internal_temp_override_C,
            "ach_override": self.ach_override,
            "fabric_elements": [e.to_dict() for e in self.fabric_elements],
        }

    @classmethod
    def from_dict(cls, room_id: str, data: dict) -> "RoomStateV1":

        instance = cls(
            room_id=room_id,
            name=data.get("name", room_id),
            internal_temp_override_C=data.get("internal_temp_override_C"),
            ach_override=data.get("ach_override"),
        )

        # --------------------------------------------------
        # Geometry
        # --------------------------------------------------
        geom_data = data.get("geometry")

        if geom_data:
            polygon = geom_data.get("polygon")

            length_m = geom_data.get("length_m")
            width_m = geom_data.get("width_m")

            # derive from polygon (rectangular v1)
            if polygon and len(polygon) >= 4:
                try:
                    xs = [p[0] for p in polygon]
                    ys = [p[1] for p in polygon]

                    length_m = max(xs) - min(xs)
                    width_m = max(ys) - min(ys)
                except Exception:
                    pass

            instance.geometry = RoomGeometryV1(
                length_m=length_m,
                width_m=width_m,
                height_m=geom_data.get("height_m"),
            )

        return instance

    # ------------------------------------------------------------------
    # Convenience (intent only)
    # ------------------------------------------------------------------

    def add_fabric_element(self, element: FabricElementV1) -> None:
        self.fabric_elements.append(element)

    def clear_fabric_elements(self) -> None:
        self.fabric_elements.clear()

    def get_fabric_elements_by_class(
        self, element_class: str
    ) -> List[FabricElementV1]:
        return [
            e for e in self.fabric_elements
            if e.element_class == element_class
        ]

    # ------------------------------------------------------------------
    # Compatibility bridge (temporary)
    # ------------------------------------------------------------------

    @property
    def space(self) -> RoomGeometryV1:
        """
        Temporary bridge for legacy readiness checks.
        """
        return self.geometry