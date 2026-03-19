# ======================================================================
# HVAC/topology/boundary_segment_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

BoundaryKind = Literal["EXTERNAL", "INTER_ROOM", "ADIABATIC"]


@dataclass(slots=True)
class BoundarySegmentV1:
    """
    Authoritative room-boundary segment.

    Phase IV-A rules
    ----------------
    • Exactly one owner room
    • geometry_ref links the segment to a stable room edge identity
    • INTER_ROOM requires adjacent_room_id
    • EXTERNAL / ADIABATIC must not reference adjacent_room_id
    """

    segment_id: str
    owner_room_id: str
    geometry_ref: str
    length_m: float

    boundary_kind: BoundaryKind
    adjacent_room_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Deserialization (Phase IV-A)
    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict) -> "BoundarySegmentV1":
        return cls(
            segment_id=data.get("segment_id"),
            owner_room_id=data.get("owner_room_id"),
            geometry_ref=data.get("geometry_ref"),
            length_m=data.get("length_m", 0.0),
            boundary_kind=data.get("boundary_kind", "EXTERNAL"),
            adjacent_room_id=data.get("adjacent_room_id"),
        )

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "owner_room_id": self.owner_room_id,
            "geometry_ref": self.geometry_ref,
            "length_m": self.length_m,
            "boundary_kind": self.boundary_kind,
            "adjacent_room_id": self.adjacent_room_id,
        }


