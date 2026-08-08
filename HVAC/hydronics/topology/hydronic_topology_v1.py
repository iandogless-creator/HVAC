# ======================================================================
# HVAC/hydronics/topology/hydronic_topology_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ======================================================================
# HydronicSublegV1
# ======================================================================

@dataclass(slots=True)
class HydronicSublegV1:
    """
    Hydronic subleg route authority.

    Canonical recursive position supplies its terminology:
    - directly beneath a leg: principal subleg
    - beneath another subleg: branch subleg

    ``sublegs`` contains child branch sublegs. A subleg with no children is
    a leaf. Kind and leaf status are derived and are not persisted fields.

    This DTO is authority for route/order only.
    It does not calculate pipe size, pressure drop, or proportioning.
    """

    subleg_id: str
    label: str
    origin_room_id: str
    route_room_ids: list[str] = field(default_factory=list)
    index_room_id: str | None = None
    sublegs: list["HydronicSublegV1"] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        """True when this subleg currently has no child branch sublegs."""

        return not self.sublegs

    def to_dict(self) -> dict[str, Any]:
        return {
            "subleg_id": self.subleg_id,
            "label": self.label,
            "origin_room_id": self.origin_room_id,
            "route_room_ids": list(self.route_room_ids),
            "index_room_id": self.index_room_id,
            "sublegs": [subleg.to_dict() for subleg in self.sublegs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HydronicSublegV1":
        return cls(
            subleg_id=str(data.get("subleg_id", "")),
            label=str(data.get("label", "")),
            origin_room_id=str(data.get("origin_room_id", "")),
            route_room_ids=[
                str(room_id)
                for room_id in (data.get("route_room_ids", []) or [])
            ],
            index_room_id=data.get("index_room_id"),
            sublegs=[
                cls.from_dict(subleg_data)
                for subleg_data in (data.get("sublegs", []) or [])
                if isinstance(subleg_data, dict)
            ],
        )


# ======================================================================
# HydronicLegV1
# ======================================================================

@dataclass(slots=True)
class HydronicLegV1:
    """
    Hydronic leg route authority.

    A leg leaves the common main and canonically owns no rooms directly.
    Its top-level ``sublegs`` are principal sublegs; there may be any number.

    ``route_room_ids`` and ``index_room_id`` remain transitional compatibility
    mirrors until H-S67-C migrates accepted legacy topology.
    """

    leg_id: str
    label: str
    route_room_ids: list[str] = field(default_factory=list)
    index_room_id: str | None = None
    sublegs: list[HydronicSublegV1] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "leg_id": self.leg_id,
            "label": self.label,
            "route_room_ids": list(self.route_room_ids),
            "index_room_id": self.index_room_id,
            "sublegs": [subleg.to_dict() for subleg in self.sublegs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HydronicLegV1":
        return cls(
            leg_id=str(data.get("leg_id", "")),
            label=str(data.get("label", "")),
            route_room_ids=[
                str(room_id)
                for room_id in (data.get("route_room_ids", []) or [])
            ],
            index_room_id=data.get("index_room_id"),
            sublegs=[
                HydronicSublegV1.from_dict(subleg_data)
                for subleg_data in (data.get("sublegs", []) or [])
                if isinstance(subleg_data, dict)
            ],
        )


# ======================================================================
# HydronicTopologyV1
# ======================================================================

@dataclass(slots=True)
class HydronicTopologyV1:
    """
    Hydronic topology route authority.

    This is the explicit authority for hydronic route/order before Basic PS.

    Important:
    - ProjectState.rooms remains stable room/spatial identity.
    - HydronicTopologyV1 owns hydronic route ordering.
    - The persisted legs list is physical common-main take-off order,
      starting at the heat source and proceeding outwards.
    - Reordering legs changes that physical take-off order; the first leg is
      the nearest take-off and the last leg is the furthest take-off.
    - Basic PS should eventually consume this object.
    - Proportioning schematic should eventually consume this object.
    - This object does not perform physics.
    """

    heat_source_room_id: str
    legs: list[HydronicLegV1] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "heat_source_room_id": self.heat_source_room_id,
            "legs": [leg.to_dict() for leg in self.legs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HydronicTopologyV1":
        return cls(
            heat_source_room_id=str(data.get("heat_source_room_id", "")),
            legs=[
                HydronicLegV1.from_dict(leg_data)
                for leg_data in (data.get("legs", []) or [])
                if isinstance(leg_data, dict)
            ],
        )

    def all_route_room_ids(self) -> list[str]:
        """
        Return all room ids used by the hydronic routes.

        The heat-source room is not included unless it also appears explicitly
        in a leg/subleg route_room_ids list.
        """

        room_ids: list[str] = []

        def add_unique(value: str) -> None:
            if value and value not in room_ids:
                room_ids.append(value)

        def walk_subleg(subleg: HydronicSublegV1) -> None:
            for room_id in subleg.route_room_ids:
                add_unique(room_id)

            for child_subleg in subleg.sublegs:
                walk_subleg(child_subleg)

        for leg in self.legs:
            for room_id in leg.route_room_ids:
                add_unique(room_id)

            for subleg in leg.sublegs:
                walk_subleg(subleg)

        return room_ids

    def contains_room_id(self, room_id: str) -> bool:
        """
        True if the room is referenced anywhere in the hydronic topology.
        """

        if room_id == self.heat_source_room_id:
            return True

        return room_id in self.all_route_room_ids()