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
        geometry_ref: str = "",
        _segment: BoundarySegmentV1 | None = None,
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

        # Projection metadata for HLP / adapters.
        # This is not physics authority; BoundarySegmentV1 remains authority.
        self.geometry_ref = geometry_ref
        self._segment = _segment


# ======================================================================
# Helpers
# ======================================================================

def _resolve_internal_temp(project: ProjectState, room: RoomStateV1) -> float:
    if hasattr(room, "internal_temp_C") and room.internal_temp_C is not None:
        return float(room.internal_temp_C)

    return float(project.environment.default_internal_temp_C)


def _resolve_external_temp(project: ProjectState) -> float:
    return float(project.environment.external_design_temp_C)


def _resolve_delta_t(
    project: ProjectState,
    room: RoomStateV1,
    seg: BoundarySegmentV1 | None,
) -> float:
    ti = _resolve_internal_temp(project, room)
    te = _resolve_external_temp(project)

    if seg is None:
        # Synthetic fallback surfaces are external by definition.
        return ti - te

    if seg.boundary_kind == "EXTERNAL":
        return ti - te

    if seg.boundary_kind == "INTER_ROOM":
        other = project.rooms.get(seg.adjacent_room_id)
        if other is not None:
            ti_other = _resolve_internal_temp(project, other)
            return ti - ti_other

    return 0.0


def _normalise_geometry_ref(seg: BoundarySegmentV1 | None, fallback: str = "") -> str:
    """
    Normalise v1 geometry references into broad surface classes.

    Examples:
    • "floor"              -> "floor"
    • "ceiling"            -> "ceiling"
    • "roof"               -> "roof"
    • "wall"               -> "wall"
    • "room-001-edge-1"    -> "wall"
    """

    if seg is None:
        return fallback

    geom = str(getattr(seg, "geometry_ref", "") or "").lower()

    if geom in {"floor", "ceiling", "roof", "wall"}:
        return geom

    if "floor" in geom:
        return "floor"

    if "ceil" in geom or "roof" in geom:
        return "ceiling"

    if "edge" in geom or "wall" in geom:
        return "wall"

    return fallback or "wall"


def _resolve_area(
    room: RoomStateV1,
    surface_class: str,
    seg: BoundarySegmentV1 | None = None,
) -> float:
    g = room.geometry

    if g is None:
        return 0.0

    if surface_class in {"floor", "ceiling", "roof"}:
        return float(g.length_m) * float(g.width_m)

    # Wall-like surfaces use segment length when available.
    # This is required for topology-driven internal/external wall rows.
    if seg is not None:
        length_m = float(getattr(seg, "length_m", 0.0) or 0.0)
        return length_m * float(g.height_m)

    # Fallback only.
    return float(g.length_m) * float(g.height_m)


def _surface_class_for_segment(seg: BoundarySegmentV1) -> str:
    """
    Geometry-first classification.

    Critical rule:
    vertical adjacency remains floor/ceiling.
    It must not become wall/internal_partition just because it is INTER_ROOM.
    """

    geom = _normalise_geometry_ref(seg)

    if geom == "floor":
        return "floor"

    if geom == "ceiling":
        return "ceiling"

    if geom == "roof":
        return "roof"

    return "wall"


def _resolve_construction_id(
    project: ProjectState,
    surface_id: str,
    surface_class: str,
    boundary_kind: str,
) -> str:
    # 1. User override / assignment authority.
    mapping = getattr(project, "surface_construction_map", {}) or {}
    if surface_id in mapping:
        return mapping[surface_id]

    # 2. Canonical fallback.
    if surface_class == "floor":
        return "DEV-FLOOR"

    if surface_class in {"ceiling", "roof"}:
        return "DEV-ROOF"

    if surface_class == "wall":
        if boundary_kind == "INTER_ROOM":
            return "DEV-INT-WALL"
        return "DEV-EXT-WALL"

    return "DEV-EXT-WALL"


def _make_row(
    *,
    project: ProjectState,
    room: RoomStateV1,
    surface_id: str,
    surface_class: str,
    boundary_kind: str,
    adjacent_room_id: str | None,
    geometry_ref: str,
    seg: BoundarySegmentV1 | None,
) -> DevFabricRow:
    area = _resolve_area(room, surface_class, seg)

    cid = _resolve_construction_id(
        project,
        surface_id,
        surface_class,
        boundary_kind,
    )

    construction = project.constructions[cid]

    dt = _resolve_delta_t(project, room, seg)

    return DevFabricRow(
        surface_id=surface_id,
        room_id=room.room_id,
        surface_class=surface_class,
        area_m2=area,
        construction_id=cid,
        u_value_W_m2K=construction.u_value_W_m2K,
        boundary_kind=boundary_kind,
        adjacent_room_id=adjacent_room_id,
        delta_t_K=dt,
        geometry_ref=geometry_ref,
        _segment=seg,
    )


# ======================================================================
# Main
# ======================================================================

def generate_fabric_from_topology(
    project: ProjectState,
    room: RoomStateV1,
) -> List[DevFabricRow]:
    """
    Build fabric rows from ProjectState topology.

    Rules
    -----
    • BoundarySegmentV1 is the topology authority.
    • geometry_ref decides whether a segment is wall/floor/ceiling/roof.
    • INTER_ROOM does not automatically mean wall.
    • Synthetic fallback floor/roof rows are added only when no explicit
      floor/ceiling topology segment exists for the room.
    """

    rows: List[DevFabricRow] = []

    explicit_floor = False
    explicit_ceiling = False

    # --------------------------------------------------
    # Topology-driven surfaces
    # --------------------------------------------------

    for seg in project.boundary_segments.values():
        if seg.owner_room_id != room.room_id:
            continue

        surface_id = seg.segment_id
        geometry_ref = _normalise_geometry_ref(seg)
        surface_class = _surface_class_for_segment(seg)

        if surface_class == "floor":
            explicit_floor = True

        if surface_class in {"ceiling", "roof"}:
            explicit_ceiling = True

        rows.append(
            _make_row(
                project=project,
                room=room,
                surface_id=surface_id,
                surface_class=surface_class,
                boundary_kind=seg.boundary_kind,
                adjacent_room_id=seg.adjacent_room_id,
                geometry_ref=geometry_ref,
                seg=seg,
            )
        )

    # --------------------------------------------------
    # Synthetic fallback floor
    # --------------------------------------------------
    # Simple rectangular DEV modes may only define wall edges.
    # Do not add this when topology already supplies a floor segment.
    # --------------------------------------------------

    if not explicit_floor:
        rows.append(
            _make_row(
                project=project,
                room=room,
                surface_id=f"{room.room_id}-floor",
                surface_class="floor",
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
                geometry_ref="floor",
                seg=None,
            )
        )

    # --------------------------------------------------
    # Synthetic fallback roof / external ceiling
    # --------------------------------------------------
    # Do not add this when topology already supplies a ceiling/roof segment.
    # --------------------------------------------------

    if not explicit_ceiling:
        rows.append(
            _make_row(
                project=project,
                room=room,
                surface_id=f"{room.room_id}-roof",
                surface_class="roof",
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
                geometry_ref="roof",
                seg=None,
            )
        )

    return rows