# ======================================================================
# HVAC/core/opening_schedule_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field


# ======================================================================
# OpeningScheduleItemV1
# ======================================================================

@dataclass(slots=True)
class OpeningScheduleItemV1:
    """
    Room-level opening schedule item.

    V1 authority
    ------------
    • Belongs to a room-level opening schedule
    • Does not know wall placement
    • Does not mutate fabric rows directly
    • Does not calculate heat loss

    Thermal rule
    ------------
    • construction_id points to ConstructionV1
    • U-value is resolved from ConstructionV1
    • U-value is never stored here directly
    """

    opening_type: str          # WINDOW / DOOR
    profile_id: str            # SMALL_WINDOW / STANDARD_WINDOW / EXTERNAL_DOOR
    profile_name: str

    width_m: float
    height_m: float
    quantity: int = 1

    construction_id: str = ""

    @property
    def area_each_m2(self) -> float:
        return float(self.width_m) * float(self.height_m)

    @property
    def total_area_m2(self) -> float:
        return self.area_each_m2 * int(self.quantity)


# ======================================================================
# RoomOpeningScheduleV1
# ======================================================================

@dataclass(slots=True)
class RoomOpeningScheduleV1:
    """
    Room-level opening schedule.

    V1 simplification
    -----------------
    • External windows/doors are scheduled at room level
    • They are not placed on individual walls yet
    • Any external wall click may open this room-level schedule
    """

    room_id: str
    openings: list[OpeningScheduleItemV1] = field(default_factory=list)

    @property
    def total_opening_area_m2(self) -> float:
        return sum(item.total_area_m2 for item in self.openings)

    @property
    def total_window_area_m2(self) -> float:
        return sum(
            item.total_area_m2
            for item in self.openings
            if item.opening_type == "WINDOW"
        )

    @property
    def total_door_area_m2(self) -> float:
        return sum(
            item.total_area_m2
            for item in self.openings
            if item.opening_type == "DOOR"
        )

    def remove_matching_items(
        self,
        *,
        profile_id: str,
        width_m: float,
        height_m: float,
    ) -> None:
        """
        Remove all schedule items matching a grouped preview row.

        F1-C rule
        ---------
        The Wall Wizard table groups identical opening schedule items.
        Removing a grouped row removes all underlying matching items.
        """
        self.openings = [
            item
            for item in self.openings
            if not (
                item.profile_id == profile_id
                and float(item.width_m) == float(width_m)
                and float(item.height_m) == float(height_m)
            )
        ]

    def add_item(self, item: OpeningScheduleItemV1) -> None:
        """
        Add a schedule item.

        Kept intentionally simple for F1-A.
        Grouping/merging can be done later in controller logic.
        """
        if item.quantity <= 0:
            return

        self.openings.append(item)

    def clear(self) -> None:
        self.openings.clear()