# ======================================================================
# HVAC/project/guarded_room_deletion_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class GuardedRoomDeletionPlanV1:
    room_id: str
    blockers: tuple[str, ...]
    owned_surface_ids: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.blockers


def _stored_route_room_ids_v1(topology: Any) -> set[str]:
    if topology is None:
        return set()

    reader = getattr(topology, "all_route_room_ids", None)
    if callable(reader):
        return {str(value) for value in (reader() or ()) if value}

    result: set[str] = set()

    def walk(node: Any) -> None:
        for value in getattr(node, "route_room_ids", ()) or ():
            if value:
                result.add(str(value))
        for child in getattr(node, "sublegs", ()) or ():
            walk(child)

    for leg in getattr(topology, "legs", ()) or ():
        walk(leg)
    return result


def build_guarded_room_deletion_plan_v1(
    project_state: Any,
    room_id: object,
) -> GuardedRoomDeletionPlanV1:
    stable_room_id = str(room_id or "").strip()
    rooms = getattr(project_state, "rooms", {}) or {}
    segments = getattr(project_state, "boundary_segments", {}) or {}

    owned_surface_ids = tuple(
        str(surface_id)
        for surface_id, segment in segments.items()
        if str(getattr(segment, "owner_room_id", "") or "")
        == stable_room_id
    )

    blockers: list[str] = []
    if not stable_room_id or stable_room_id not in rooms:
        blockers.append("The selected room no longer exists.")
        return GuardedRoomDeletionPlanV1(
            room_id=stable_room_id,
            blockers=tuple(blockers),
            owned_surface_ids=owned_surface_ids,
        )

    if len(rooms) <= 1:
        blockers.append("The final project room cannot be removed.")

    topology = getattr(project_state, "hydronic_topology", None)
    if (
        str(getattr(topology, "heat_source_room_id", "") or "")
        == stable_room_id
    ):
        blockers.append("It is the active Heat Source room.")

    if stable_room_id in _stored_route_room_ids_v1(topology):
        blockers.append("It is part of a served hydronic route.")

    emitter_count = sum(
        1
        for emitter in (getattr(project_state, "emitters", {}) or {}).values()
        if str(getattr(emitter, "room_id", "") or "") == stable_room_id
    )
    if emitter_count:
        blockers.append(
            f"It has {emitter_count} assigned hydronic emitter"
            f"{'s' if emitter_count != 1 else ''}."
        )

    inbound_adjacencies = [
        str(surface_id)
        for surface_id, segment in segments.items()
        if str(getattr(segment, "owner_room_id", "") or "")
        != stable_room_id
        and str(getattr(segment, "adjacent_room_id", "") or "")
        == stable_room_id
    ]
    if inbound_adjacencies:
        blockers.append(
            f"It is referenced by {len(inbound_adjacencies)} adjacent-room "
            f"surface{'s' if len(inbound_adjacencies) != 1 else ''}."
        )

    return GuardedRoomDeletionPlanV1(
        room_id=stable_room_id,
        blockers=tuple(blockers),
        owned_surface_ids=owned_surface_ids,
    )


def delete_room_guarded_v1(
    project_state: Any,
    room_id: object,
) -> GuardedRoomDeletionPlanV1:
    plan = build_guarded_room_deletion_plan_v1(project_state, room_id)
    if not plan.ready:
        raise ValueError("Room deletion blocked: " + " ".join(plan.blockers))

    for surface_id in plan.owned_surface_ids:
        project_state.boundary_segments.pop(surface_id, None)
        (getattr(project_state, "surface_construction_map", {}) or {}).pop(
            surface_id, None
        )
        (getattr(project_state, "openings_by_surface", {}) or {}).pop(
            surface_id, None
        )

    (getattr(project_state, "room_opening_schedules", {}) or {}).pop(
        plan.room_id, None
    )

    pipe_intent = getattr(
        project_state,
        "hydronic_room_paired_pipe_length_intent",
        None,
    )
    lengths_by_room_id = getattr(pipe_intent, "lengths_by_room_id", None)
    if isinstance(lengths_by_room_id, dict):
        lengths_by_room_id.pop(plan.room_id, None)

    project_state.rooms.pop(plan.room_id)

    mark_heatloss_dirty = getattr(project_state, "mark_heatloss_dirty", None)
    if callable(mark_heatloss_dirty):
        mark_heatloss_dirty()
    else:
        project_state.heatloss_valid = False
    project_state.hydronics_valid = False

    return plan
