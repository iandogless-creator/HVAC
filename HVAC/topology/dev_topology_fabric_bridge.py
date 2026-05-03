# ======================================================================
# HVAC/topology/dev_topology_fabric_bridge.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.topology.adjacency_delta_t_resolver import AdjacencyDeltaTResolver



DEFAULT_EXTERNAL_CONSTRUCTION_ID = "DEV-EXT-WALL"
DEFAULT_INTERNAL_CONSTRUCTION_ID = "DEV-INT-WALL"
DEFAULT_FLOOR_CONSTRUCTION_ID = "DEV-FLOOR"
DEFAULT_ROOF_CONSTRUCTION_ID = "DEV-ROOF"


@dataclass(slots=True)
class DevFabricRow:
    element_id: str
    room_id: str
    surface_class: str
    area_m2: float
    length_m: float
    height_m: float
    geometry_ref: str

    construction_id: str | None = None
    u_value_W_m2K: float | None = None

    boundary_kind: str | None = None
    adjacent_room_id: str | None = None
    delta_t_K: float | None = None

    # Canonical link back to BoundarySegmentV1 for GUI row identity/editing.
    _segment: Any | None = None


def generate_fabric_from_topology(project_state: Any, room: Any) -> list[DevFabricRow]:
    rows: list[DevFabricRow] = []

    room_id = getattr(room, "room_id", None) or getattr(room, "id", None)
    if not room_id:
        return rows

    geometry = getattr(room, "geometry", None)
    if geometry is None:
        return rows

    height_m = getattr(geometry, "height_m", None)
    if height_m is None and project_state.environment is not None:
        height_m = getattr(project_state.environment, "default_room_height_m", 0.0)

    height_m = float(height_m or 0.0)

    floor_area_m2 = getattr(geometry, "floor_area_m2", None)
    if callable(floor_area_m2):
        floor_area_m2 = floor_area_m2()
    else:
        length_m = float(getattr(geometry, "length_m", 0.0) or 0.0)
        width_m = float(getattr(geometry, "width_m", 0.0) or 0.0)
        floor_area_m2 = length_m * width_m

    floor_area_m2 = float(floor_area_m2 or 0.0)

    # Authoritative topology segments for this room.
    segments = [
        seg for seg in project_state.boundary_segments.values()
        if seg.owner_room_id == room_id
    ]

    for seg in segments:
        surface_class, area_m2, construction_id = _classify_segment(
            seg=seg,
            height_m=height_m,
            floor_area_m2=floor_area_m2,
        )

        u_value = _resolve_u_value(project_state, construction_id)

        delta_t_K = AdjacencyDeltaTResolver.resolve_delta_t_K(
            project_state=project_state,
            owner_room=room,
            boundary_kind=seg.boundary_kind,
            adjacent_room_id=seg.adjacent_room_id,
        )

        row = DevFabricRow(
            element_id=seg.segment_id,
            room_id=room_id,
            surface_class=surface_class,
            area_m2=area_m2,
            length_m=float(getattr(seg, "length_m", 0.0) or 0.0),
            height_m=height_m,
            geometry_ref=str(getattr(seg, "geometry_ref", "") or ""),
            construction_id=construction_id,
            u_value_W_m2K=u_value,
            boundary_kind=seg.boundary_kind,
            adjacent_room_id=seg.adjacent_room_id,
            delta_t_K=delta_t_K,
            _segment=seg,
        )

        rows.append(row)

    return rows


def _normalise_geometry_ref(seg: Any) -> str:
    geom = str(getattr(seg, "geometry_ref", "") or "").lower()

    if geom in {"floor", "ceiling", "roof", "wall"}:
        return geom

    if "floor" in geom:
        return "floor"

    if "ceil" in geom or "roof" in geom:
        return "ceiling"

    if "edge" in geom or "wall" in geom:
        return "wall"

    return "wall"


def _classify_segment(*, seg: Any, height_m: float, floor_area_m2: float):
    """
    Geometry-first classification.

    Critical rule:
    vertical adjacency remains floor/ceiling. It must not be downgraded
    to internal_partition just because boundary_kind == INTER_ROOM.
    """

    geom = _normalise_geometry_ref(seg)
    boundary_kind = str(getattr(seg, "boundary_kind", "") or "").upper()

    if geom == "floor":
        return "floor", floor_area_m2, DEFAULT_FLOOR_CONSTRUCTION_ID

    if geom == "ceiling":
        return "ceiling", floor_area_m2, DEFAULT_ROOF_CONSTRUCTION_ID

    if geom == "roof":
        return "roof", floor_area_m2, DEFAULT_ROOF_CONSTRUCTION_ID

    area_m2 = float(getattr(seg, "length_m", 0.0) or 0.0) * float(height_m or 0.0)

    if boundary_kind == "EXTERNAL":
        return "external_wall", area_m2, DEFAULT_EXTERNAL_CONSTRUCTION_ID

    if boundary_kind == "INTER_ROOM":
        return "internal_partition", area_m2, DEFAULT_INTERNAL_CONSTRUCTION_ID

    if boundary_kind == "ADIABATIC":
        return "adiabatic_wall", area_m2, DEFAULT_INTERNAL_CONSTRUCTION_ID

    return "unknown_wall", area_m2, DEFAULT_INTERNAL_CONSTRUCTION_ID


def _resolve_u_value(project_state: Any, construction_id: str | None) -> float | None:
    if not construction_id:
        return None

    construction = project_state.constructions.get(construction_id)
    if construction is None:
        raise RuntimeError(
            f"Construction '{construction_id}' not found in project_state.constructions"
        )

    return construction.u_value_W_m2K