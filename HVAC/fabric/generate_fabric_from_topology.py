# ======================================================================
# HVAC/fabric/generate_fabric_from_topology.py
# ======================================================================

from __future__ import annotations

from typing import List

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ======================================================================
# Row DTO (keep aligned with your existing structure)
# ======================================================================

class DevFabricRow:
    def __init__(
        self,
        *,
        surface_id: str,
        room_id: str,
        surface_class: str,
        area_m2: float,
        construction_id: str,
        u_value_W_m2K: float,
        boundary_kind: str,
        adjacent_room_id: str | None,
        delta_t_K: float,
    ):
        self.surface_id = surface_id
        self.room_id = room_id
        self.surface_class = surface_class
        self.area_m2 = area_m2
        self.construction_id = construction_id
        self.u_value_W_m2K = u_value_W_m2K
        self.boundary_kind = boundary_kind
        self.adjacent_room_id = adjacent_room_id
        self.delta_t_K = delta_t_K


# ======================================================================
# Helpers
# ======================================================================

def _resolve_internal_temp(project: ProjectState, room: RoomStateV1) -> float:
    if hasattr(room, "internal_temp_C") and room.internal_temp_C is not None:
        return float(room.internal_temp_C)
    return float(project.environment.default_internal_temp_C)


def _resolve_external_temp(project: ProjectState) -> float:
    return float(project.environment.external_design_temp_C)


def _resolve_delta_t(project: ProjectState, room: RoomStateV1, seg: BoundarySegmentV1 | None) -> float:
    Ti = _resolve_internal_temp(project, room)
    Te = _resolve_external_temp(project)

    if seg is None:
        # synthetic surfaces → external for now
        return Ti - Te

    if seg.boundary_kind == "EXTERNAL":
        return Ti - Te

    if seg.boundary_kind == "INTER_ROOM":
        other = project.rooms.get(seg.adjacent_room_id)
        if other:
            Ti_other = _resolve_internal_temp(project, other)
            return Ti - Ti_other

    return 0.0


def _resolve_area(room: RoomStateV1, surface_class: str) -> float:
    g = room.geometry

    if surface_class in {"floor", "roof"}:
        return float(g.length_m) * float(g.width_m)

    # v1 wall approximation (no segment geometry yet)
    return float(g.length_m) * float(g.height_m)


def _resolve_construction_id(
    project: ProjectState,
    surface_id: str,
    surface_class: str,
) -> str:

    # 1️⃣ user override (authoritative)
    mapping = getattr(project, "surface_construction_map", {}) or {}
    if surface_id in mapping:
        return mapping[surface_id]

    # 2️⃣ canonical fallback
    if surface_class == "wall":
        return "DEV-EXT-WALL"
    if surface_class == "floor":
        return "DEV-FLOOR"
    if surface_class == "roof":
        return "DEV-ROOF"

    return "DEV-EXT-WALL"


# ======================================================================
# Main
# ======================================================================

def generate_fabric_from_topology(
    project: ProjectState,
    room: RoomStateV1,
) -> List[DevFabricRow]:

    rows: List[DevFabricRow] = []

    # --------------------------------------------------
    # WALLS (from topology segments)
    # --------------------------------------------------

    for seg in project.boundary_segments.values():

        if seg.owner_room_id != room.room_id:
            continue

        surface_id = seg.segment_id
        surface_class = "wall"

        area = _resolve_area(room, surface_class)

        cid = _resolve_construction_id(project, surface_id, surface_class)
        construction = project.constructions[cid]

        dt = _resolve_delta_t(project, room, seg)

        rows.append(
            DevFabricRow(
                surface_id=surface_id,
                room_id=room.room_id,
                surface_class=surface_class,
                area_m2=area,
                construction_id=cid,
                u_value_W_m2K=construction.u_value_W_m2K,
                boundary_kind=seg.boundary_kind,
                adjacent_room_id=seg.adjacent_room_id,
                delta_t_K=dt,
            )
        )

    # --------------------------------------------------
    # FLOOR (synthetic)
    # --------------------------------------------------

    surface_id = f"{room.room_id}-floor"
    surface_class = "floor"

    area = _resolve_area(room, surface_class)

    cid = _resolve_construction_id(project, surface_id, surface_class)
    construction = project.constructions[cid]

    dt = _resolve_delta_t(project, room, None)

    rows.append(
        DevFabricRow(
            surface_id=surface_id,
            room_id=room.room_id,
            surface_class=surface_class,
            area_m2=area,
            construction_id=cid,
            u_value_W_m2K=construction.u_value_W_m2K,
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
            delta_t_K=dt,
        )
    )

    # --------------------------------------------------
    # ROOF (synthetic)
    # --------------------------------------------------

    surface_id = f"{room.room_id}-roof"
    surface_class = "roof"

    area = _resolve_area(room, surface_class)

    cid = _resolve_construction_id(project, surface_id, surface_class)
    construction = project.constructions[cid]

    dt = _resolve_delta_t(project, room, None)

    rows.append(
        DevFabricRow(
            surface_id=surface_id,
            room_id=room.room_id,
            surface_class=surface_class,
            area_m2=area,
            construction_id=cid,
            u_value_W_m2K=construction.u_value_W_m2K,
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
            delta_t_K=dt,
        )
    )

    return rows