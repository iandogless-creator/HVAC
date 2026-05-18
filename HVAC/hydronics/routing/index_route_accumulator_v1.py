# ======================================================================
# HVAC/hydronics/routing/index_route_accumulator_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.project.project_state import ProjectState
from HVAC.core.room_identity import room_short_label
from HVAC.hydronics.worksheets.basic_hydronics_worksheet_v1 import (
    build_basic_hydronics_worksheet_v1,
)


# ======================================================================
# Constants
# ======================================================================

ROUTE_BASIS_ASSUMED_REVERSE_ROOM_ORDER = "ASSUMED_REVERSE_ROOM_ORDER"


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class IndexRouteSectionV1:
    """
    One section on the assumed index route back to plant.

    Authority
    ---------
    • Read-only projection
    • Does not mutate ProjectState
    • Does not size pipe
    • Does not calculate pressure loss
    """

    section_index: int

    from_room_id: str
    from_room_label: str

    to_room_id: str
    to_room_label: str

    included_room_ids: tuple[str, ...]
    included_room_labels: tuple[str, ...]

    accumulated_mass_flow_kg_s: Optional[float]


@dataclass(frozen=True, slots=True)
class IndexRouteAccumulatorV1:
    """
    H-N7a assumed index route accumulator.

    This is the modern equivalent of the old BASIC running AcFr trace:

        AcFr = AcFr + Fr

    but without pipe sizing yet.
    """

    route_basis: str

    plant_room_id: Optional[str]
    plant_room_label: Optional[str]

    index_room_id: Optional[str]
    index_room_label: Optional[str]

    sections: list[IndexRouteSectionV1]

    excluded_room_ids: tuple[str, ...]
    excluded_room_labels: tuple[str, ...]


# ======================================================================
# Builder
# ======================================================================

def build_index_route_accumulator_v1(
    project: ProjectState,
) -> IndexRouteAccumulatorV1:
    """
    Build an assumed index route back to plant.

    Current H-N7a assumption
    ------------------------
    • plant room is first room in ProjectState.rooms order
    • index room is basic_hydronic_sizing_intent.index_room_id
    • route is reverse room order from index back to plant

    Example:
        room-001, room-002, room-003, room-004, room-005, room-006
        index = room-005
        plant = room-001

        route = room-005 → room-004 → room-003 → room-002 → room-001
        excluded = room-006

    Rules
    -----
    • No pipe sizing
    • No pressure calculation
    • No material selection
    • No ProjectState mutation
    """
    rooms = getattr(project, "rooms", {}) or {}

    if not rooms:
        return _empty_result(project)

    room_ids = list(rooms.keys())

    plant_room_id = room_ids[0]
    plant_room = rooms.get(plant_room_id)
    plant_room_label = (
        room_short_label(plant_room_id, plant_room)
        if plant_room is not None
        else plant_room_id
    )

    intent = getattr(project, "basic_hydronic_sizing_intent", None)
    index_room_id = getattr(intent, "index_room_id", None) if intent else None

    # --------------------------------------------------
    # H-Q/H-N fallback
    # --------------------------------------------------
    # If no explicit index room is stored yet, use the last room in
    # ProjectState.rooms order. This preserves the original v1 assumed
    # reverse-room-order route:
    #
    #     last room → ... → first room / plant
    #
    # Missing sizing intent must not exclude the whole project.
    # --------------------------------------------------
    if not index_room_id or index_room_id not in rooms:
        index_room_id = room_ids[-1]

    index_room_label = room_short_label(
        index_room_id,
        rooms[index_room_id],
    )

    route_room_ids = _assumed_reverse_route_room_ids(
        room_ids=room_ids,
        plant_room_id=plant_room_id,
        index_room_id=index_room_id,
    )

    flow_by_room_id = _room_mass_flow_map(project)

    sections: list[IndexRouteSectionV1] = []
    included_so_far: list[str] = []
    accumulated = 0.0
    has_any_flow = False

    # For route: [index, ..., plant]
    # sections are index->next, next->next, ... previous->plant.
    for section_index, (from_room_id, to_room_id) in enumerate(
        zip(route_room_ids[:-1], route_room_ids[1:]),
        start=1,
    ):
        included_so_far.append(from_room_id)

        room_flow = flow_by_room_id.get(from_room_id)

        if room_flow is not None:
            accumulated += float(room_flow)
            has_any_flow = True

        included_labels = tuple(
            room_short_label(room_id, rooms[room_id])
            for room_id in included_so_far
            if room_id in rooms
        )

        sections.append(
            IndexRouteSectionV1(
                section_index=section_index,
                from_room_id=from_room_id,
                from_room_label=room_short_label(
                    from_room_id,
                    rooms[from_room_id],
                ),
                to_room_id=to_room_id,
                to_room_label=room_short_label(
                    to_room_id,
                    rooms[to_room_id],
                ),
                included_room_ids=tuple(included_so_far),
                included_room_labels=included_labels,
                accumulated_mass_flow_kg_s=(
                    accumulated if has_any_flow else None
                ),
            )
        )

    route_set = set(route_room_ids)

    excluded_room_ids = tuple(
        room_id
        for room_id in room_ids
        if room_id not in route_set
    )

    excluded_room_labels = tuple(
        room_short_label(room_id, rooms[room_id])
        for room_id in excluded_room_ids
    )

    return IndexRouteAccumulatorV1(
        route_basis=ROUTE_BASIS_ASSUMED_REVERSE_ROOM_ORDER,
        plant_room_id=plant_room_id,
        plant_room_label=plant_room_label,
        index_room_id=index_room_id,
        index_room_label=index_room_label,
        sections=sections,
        excluded_room_ids=excluded_room_ids,
        excluded_room_labels=excluded_room_labels,
    )


# ======================================================================
# Helpers
# ======================================================================

def _empty_result(project: ProjectState) -> IndexRouteAccumulatorV1:
    return IndexRouteAccumulatorV1(
        route_basis=ROUTE_BASIS_ASSUMED_REVERSE_ROOM_ORDER,
        plant_room_id=None,
        plant_room_label=None,
        index_room_id=None,
        index_room_label=None,
        sections=[],
        excluded_room_ids=tuple(),
        excluded_room_labels=tuple(),
    )


def _assumed_reverse_route_room_ids(
    *,
    room_ids: list[str],
    plant_room_id: str,
    index_room_id: str,
) -> list[str]:
    """
    Return route from index room back to plant using reverse room order.

    If plant appears before index:
        room-001, room-002, room-003, room-004, room-005
        route = room-005, room-004, room-003, room-002, room-001

    If ordering is unusual, this still returns a deterministic route.
    """
    plant_index = room_ids.index(plant_room_id)
    index_index = room_ids.index(index_room_id)

    if plant_index <= index_index:
        return list(reversed(room_ids[plant_index:index_index + 1]))

    return room_ids[index_index:plant_index + 1]


def _room_mass_flow_map(project: ProjectState) -> dict[str, float]:
    worksheet = build_basic_hydronics_worksheet_v1(project)

    result: dict[str, float] = {}

    for row in worksheet.rows:
        value = row.mass_flow_kg_s
        if value is None:
            continue

        try:
            result[row.room_id] = float(value)
        except (TypeError, ValueError):
            continue

    return result
    return result