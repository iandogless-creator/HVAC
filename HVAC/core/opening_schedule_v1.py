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

    def to_dict(self) -> dict:
        return {
            "opening_type": self.opening_type,
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "width_m": self.width_m,
            "height_m": self.height_m,
            "quantity": self.quantity,
            "construction_id": self.construction_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OpeningScheduleItemV1":
        if not isinstance(data, dict):
            raise ValueError("Opening schedule item must be a dictionary")
        return cls(
            opening_type=str(data.get("opening_type") or ""),
            profile_id=str(data.get("profile_id") or ""),
            profile_name=str(data.get("profile_name") or ""),
            width_m=float(data.get("width_m", 0.0)),
            height_m=float(data.get("height_m", 0.0)),
            quantity=int(data.get("quantity", 1)),
            construction_id=str(data.get("construction_id") or ""),
        )


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

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "openings": [item.to_dict() for item in self.openings],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
        *,
        expected_room_id: str | None = None,
    ) -> "RoomOpeningScheduleV1":
        if not isinstance(data, dict):
            raise ValueError("Room opening schedule must be a dictionary")

        stored_room_id = str(data.get("room_id") or "")
        if (
            expected_room_id
            and stored_room_id
            and stored_room_id != expected_room_id
        ):
            raise ValueError(
                "Room opening schedule identity mismatch: "
                f"expected {expected_room_id!r}, found {stored_room_id!r}"
            )

        room_id = str(expected_room_id or stored_room_id)
        if not room_id:
            raise ValueError("Room opening schedule is missing room_id")

        raw_openings = data.get("openings", []) or []
        if not isinstance(raw_openings, list):
            raise ValueError("Room opening schedule openings must be a list")

        return cls(
            room_id=room_id,
            openings=[
                OpeningScheduleItemV1.from_dict(item)
                for item in raw_openings
            ],
        )

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
        construction_id: str | None = None,
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
                and (
                    construction_id is None
                    or item.construction_id == construction_id
                )
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