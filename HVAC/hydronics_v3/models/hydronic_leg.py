#-----------------------------------------------
# HVAC/hydronics/models/hydronic_skeleton_v1.py
#-----------------------------------------------

from dataclasses import dataclass, field
from typing import List, Optional

from HVAC.hydronics_v3.models.pipe_segment import PipeSegment



@dataclass(slots=True)
class HydronicLeg:
    """
    Hydronic leg (v2 – recursive).

    STRUCTURAL RULES (LOCKED)
    -------------------------
    • Legs feed legs
    • Sub-legs own rooms
    • Rooms own emitters
    • Emitters never attach to legs directly

    A leg may:
        • have child legs (recursive hydronics)
        • OR own rooms (leaf level)
        • BUT NOT BOTH
    """

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    leg_id: str

    # -------------------------------------------------
    # Design intent
    # -------------------------------------------------
    design_qt_w: float

    # -------------------------------------------------
    # Geometry (critical path)
    # -------------------------------------------------
    pipe_segments: List[PipeSegment] = field(default_factory=list)

    # -------------------------------------------------
    # Recursive structure
    # -------------------------------------------------
    parent_leg_id: Optional[str] = None
    child_legs: List["HydronicLeg"] = field(default_factory=list)

    # -------------------------------------------------
    # Leaf attachment (ONLY at leaf level)
    # -------------------------------------------------
    room_names: List[str] = field(default_factory=list)

    # -------------------------------------------------
    # Safe helpers (NO physics)
    # -------------------------------------------------
    def total_length_m(self) -> float:
        """
        Total developed length of this leg (geometry only).
        """
        return sum(seg.length_m for seg in self.pipe_segments)

    def is_leaf(self) -> bool:
        """
        A leaf leg owns rooms.
        """
        return bool(self.room_names)

    def is_branch(self) -> bool:
        """
        A branch leg feeds other legs.
        """
        return bool(self.child_legs)

    def validate_structure(self) -> None:
        """
        Enforce structural rules.

        Raises:
            ValueError if the leg violates the hydronic hierarchy.
        """
        if self.child_legs and self.room_names:
            raise ValueError(
                f"HydronicLeg '{self.leg_id}' cannot have both "
                f"child_legs and room_names."
            )
