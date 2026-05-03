# ======================================================================
# HVAC/heatloss/fabric/fabric_from_segments_v1.py
# ======================================================================

from __future__ import annotations

from typing import List, TYPE_CHECKING

from HVAC.heatloss.dto.fabric_surface_row_v1 import FabricSurfaceRowV1
from HVAC.topology.adjacency_delta_t_resolver import AdjacencyDeltaTResolver
from HVAC.gui_v3.wizards.construction_wizard import ConstructionWizard

if TYPE_CHECKING:
    from HVAC.project.project_state import ProjectState
    from HVAC.core.room_state import RoomStateV1
    from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


DEFAULT_EXTERNAL_CONSTRUCTION_ID = "DEV-EXT-WALL"
DEFAULT_INTERNAL_CONSTRUCTION_ID = "DEV-INT-WALL"
DEFAULT_FLOOR_CONSTRUCTION_ID = "DEV-FLOOR"
DEFAULT_ROOF_CONSTRUCTION_ID = "DEV-ROOF"
DEFAULT_WINDOW_CONSTRUCTION_ID = "DEV-WINDOW"


# ======================================================================
# Helpers
# ======================================================================

def _resolve_u_value(project: ProjectState, construction_id: str | None) -> float | None:
    if not construction_id:
        return None

    construction = project.constructions.get(str(construction_id))
    if construction is None:
        return None

    return construction.u_value_W_m2K


def _room_floor_area_m2(room: RoomStateV1) -> float:
    g = room.geometry
    if g is None:
        return 0.0

    if not g.length_m or not g.width_m:
        return 0.0

    return max(float(g.length_m) * float(g.width_m), 0.0)


def _effective_height_m(project: ProjectState, room: RoomStateV1) -> float:
    g = room.geometry
    height_m = getattr(g, "height_m", None) if g is not None else None

    if height_m is None and project.environment is not None:
        height_m = project.environment.default_room_height_m

    if not height_m or height_m <= 0.0:
        return 0.0

    return float(height_m)


def _normalise_geometry_ref(seg: BoundarySegmentV1) -> str:
    """
    Convert segment geometry references into broad v1 surface classes.

    DEV examples:
    • "wall"
    • "floor"
    • "ceiling"
    • "room-001-edge-1"

    Rectangular resolver edge refs are wall-like.
    """

    geom = str(getattr(seg, "geometry_ref", "") or "").lower()

    if geom in {"floor", "ceiling", "roof", "wall"}:
        return geom

    if "floor" in geom:
        return "floor"

    if "ceil" in geom or "roof" in geom:
        return "ceiling"

    # room-001-edge-1 etc. are wall-like in rectangular v1.
    if "edge" in geom or "wall" in geom:
        return "wall"

    return "wall"


def _base_construction_id_for_segment(seg: BoundarySegmentV1) -> str:
    geom = _normalise_geometry_ref(seg)
    boundary_kind = str(getattr(seg, "boundary_kind", "") or "").upper()

    if geom == "floor":
        return DEFAULT_FLOOR_CONSTRUCTION_ID

    if geom in {"ceiling", "roof"}:
        return DEFAULT_ROOF_CONSTRUCTION_ID

    if boundary_kind == "EXTERNAL":
        return DEFAULT_EXTERNAL_CONSTRUCTION_ID

    return DEFAULT_INTERNAL_CONSTRUCTION_ID


def _element_for_segment(seg: BoundarySegmentV1) -> str:
    """
    Return the canonical element name carried by the fabric row.

    Important:
    vertical adjacency must remain floor/ceiling, not internal_partition.
    """

    geom = _normalise_geometry_ref(seg)
    boundary_kind = str(getattr(seg, "boundary_kind", "") or "").upper()

    if geom == "floor":
        return "floor"

    if geom in {"ceiling", "roof"}:
        return "ceiling"

    if boundary_kind == "EXTERNAL":
        return "external_wall"

    if boundary_kind == "INTER_ROOM":
        return "internal_partition"

    return "adiabatic_wall"


def _area_for_segment(project: ProjectState, room: RoomStateV1, seg: BoundarySegmentV1) -> float:
    geom = _normalise_geometry_ref(seg)

    if geom in {"floor", "ceiling", "roof"}:
        return _room_floor_area_m2(room)

    height_m = _effective_height_m(project, room)
    if height_m <= 0.0:
        return 0.0

    length_m = float(getattr(seg, "length_m", 0.0) or 0.0)
    return max(length_m * height_m, 0.0)


def _attach_segment_display_meta(row: FabricSurfaceRowV1, seg: BoundarySegmentV1) -> None:
    """
    No-op.

    FabricSurfaceRowV1 is slots-based, so geometry/boundary metadata
    must be read from row._segment by GUI adapters.

    The row already carries:
        _segment=seg

    That is the canonical link back to BoundarySegmentV1.
    """
    return None


# ======================================================================
# FabricFromSegmentsV1
# ======================================================================

class FabricFromSegmentsV1:

    @staticmethod
    def build_rows_for_room(
        project: ProjectState,
        room: RoomStateV1,
    ) -> List[FabricSurfaceRowV1]:

        rows: List[FabricSurfaceRowV1] = []

        g = room.geometry
        if g is None:
            return rows

        explicit_floor = False
        explicit_ceiling = False

        # ==============================================================
        # TOPOLOGY-DRIVEN SURFACES
        # ==============================================================

        for seg in project.get_boundary_segments_for_room(room.room_id):

            geom = _normalise_geometry_ref(seg)

            if geom == "floor":
                explicit_floor = True

            if geom in {"ceiling", "roof"}:
                explicit_ceiling = True

            gross_area = _area_for_segment(project, room, seg)

            # --------------------------------------------------
            # Element + construction
            # --------------------------------------------------

            element = _element_for_segment(seg)
            base_cid = _base_construction_id_for_segment(seg)

            assigned_cid = ConstructionWizard.get_surface_construction(
                project,
                seg.segment_id,
            )

            cid = assigned_cid or base_cid
            u_value = _resolve_u_value(project, cid)

            # --------------------------------------------------
            # OPENINGS
            # --------------------------------------------------
            # Openings are only meaningful on wall-like external surfaces
            # in this v1 bridge.
            # --------------------------------------------------

            openings = []
            if geom == "wall":
                openings = project.get_openings_for_surface(seg.segment_id)

            opening_rows: List[FabricSurfaceRowV1] = []
            opening_area_total = 0.0

            for o in openings:

                try:
                    w = float(getattr(o, "width_m", 0.0))
                    h = float(getattr(o, "height_m", 0.0))
                except (TypeError, ValueError):
                    continue

                area_o = max(w * h, 0.0)
                opening_area_total += area_o

                ocid = getattr(o, "construction_id", None) or DEFAULT_WINDOW_CONSTRUCTION_ID
                ou = _resolve_u_value(project, ocid)

                # openings always external for now
                odt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                    project_state=project,
                    owner_room=room,
                    boundary_kind="EXTERNAL",
                    adjacent_room_id=None,
                )

                oqf = None
                if (
                    ou is not None
                    and odt is not None
                    and area_o > 0.0
                ):
                    oqf = float(ou) * float(area_o) * float(odt)

                row_o = FabricSurfaceRowV1(
                    surface_id=getattr(o, "opening_id", f"{seg.segment_id}-opening"),
                    room_id=room.room_id,
                    element=getattr(o, "kind", "window").lower(),
                    area_m2=area_o,
                    u_value_W_m2K=ou,
                    delta_t_K=odt,
                    qf_W=oqf,
                    construction_id=ocid,
                    _segment=seg,
                )

                setattr(row_o, "parent_surface_id", seg.segment_id)
                setattr(row_o, "geometry_ref", "opening")
                setattr(row_o, "surface_class", getattr(o, "kind", "window").lower())
                setattr(row_o, "boundary_kind", "EXTERNAL")
                setattr(row_o, "adjacent_room_id", None)

                opening_rows.append(row_o)

            # --------------------------------------------------
            # NET SURFACE
            # --------------------------------------------------

            if geom == "wall":
                net_area = max(gross_area - opening_area_total, 0.0)
            else:
                net_area = gross_area

            delta_t = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=project,
                owner_room=room,
                boundary_kind=seg.boundary_kind,
                adjacent_room_id=seg.adjacent_room_id,
            )

            qf = None
            if (
                u_value is not None
                and delta_t is not None
                and net_area > 0.0
            ):
                qf = float(u_value) * float(net_area) * float(delta_t)

            row = FabricSurfaceRowV1(
                surface_id=seg.segment_id,
                room_id=room.room_id,
                element=element,
                area_m2=net_area,
                u_value_W_m2K=u_value,
                delta_t_K=delta_t,
                qf_W=qf,
                construction_id=cid,
                _segment=seg,
            )

            setattr(row, "parent_surface_id", None)
            _attach_segment_display_meta(row, seg)

            rows.append(row)
            rows.extend(opening_rows)

        # ==============================================================
        # FALLBACK FLOOR + ROOF
        # ==============================================================
        # Older/simple DEV modes only generate wall topology.
        # If floor/ceiling have not been explicitly supplied as topology
        # segments, add default external floor/roof rows.
        #
        # In vertical_stack, explicit floor/ceiling segments are supplied,
        # so this will not add false roof/floor rows to intermediate rooms.
        # ==============================================================

        area = _room_floor_area_m2(room)

        if area > 0.0:

            dt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=project,
                owner_room=room,
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )

            if not explicit_floor:
                floor_cid = DEFAULT_FLOOR_CONSTRUCTION_ID
                floor_u = _resolve_u_value(project, floor_cid)
                floor_qf = None
                if floor_u is not None and dt is not None:
                    floor_qf = float(floor_u) * float(area) * float(dt)

                row_floor = FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-floor",
                    room_id=room.room_id,
                    element="floor",
                    area_m2=area,
                    u_value_W_m2K=floor_u,
                    delta_t_K=dt,
                    qf_W=floor_qf,
                    construction_id=floor_cid,
                    _segment=None,
                )

                rows.append(row_floor)

            if not explicit_ceiling:
                roof_cid = DEFAULT_ROOF_CONSTRUCTION_ID
                roof_u = _resolve_u_value(project, roof_cid)
                roof_qf = None
                if roof_u is not None and dt is not None:
                    roof_qf = float(roof_u) * float(area) * float(dt)

                row_roof = FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-roof",
                    room_id=room.room_id,
                    element="roof",
                    area_m2=area,
                    u_value_W_m2K=roof_u,
                    delta_t_K=dt,
                    qf_W=roof_qf,
                    construction_id=roof_cid,
                    _segment=None,
                )

                rows.append(row_roof)

        return rows