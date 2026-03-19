# ======================================================================
# HVAC/heatloss/fabric/fabric_from_segments_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from HVAC.topology.adjacency_delta_t_resolver import AdjacencyDeltaTResolver
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from HVAC.project.project_state import ProjectState
    from HVAC.core.room_state import RoomStateV1

# ======================================================================
# FabricSurfaceRowV1
# ======================================================================

@dataclass(slots=True)
class FabricSurfaceRowV1:
    surface_id: str
    room_id: str
    element: str
    area_m2: float
    u_value_W_m2K: Optional[float]
    delta_t_K: Optional[float]
    qf_W: Optional[float]
    construction_id: Optional[str]


# ======================================================================
# FabricFromSegmentsV1
# ======================================================================

class FabricFromSegmentsV1:
    """
    Project topology -> fabric worksheet rows

    Phase IV-A rules
    ----------------
    • Boundary segments are authoritative for wall-like elements
    • Geometry remains authoritative for floor area / height
    • No GUI logic
    • No mutation of ProjectState
    """

    @staticmethod
    def build_rows_for_room(project, room) -> List[FabricSurfaceRowV1]:

        rows: List[FabricSurfaceRowV1] = []

        g = room.geometry
        if g is None:
            return rows

        height_m = g.height_m
        if height_m is None and project.environment is not None:
            height_m = project.environment.default_room_height_m

        if height_m is None or height_m <= 0.0:
            return rows

        # --------------------------------------------------
        # Wall-like rows from topology
        # --------------------------------------------------

        for seg in project.get_boundary_segments_for_room(room.room_id):
            area_m2 = float(seg.length_m) * float(height_m)

            if seg.boundary_kind == "EXTERNAL":
                element = "external_wall"
                construction_id = "DEV-WALL"
            elif seg.boundary_kind == "INTER_ROOM":
                element = "internal_partition"
                construction_id = "DEV-WALL"
            else:
                element = "adiabatic_wall"
                construction_id = "DEV-WALL"

            u_value = project.construction_library.get(construction_id)

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
                and area_m2 > 0.0
            ):
                qf = float(u_value) * float(area_m2) * float(delta_t)

            rows.append(
                FabricSurfaceRowV1(
                    surface_id=seg.segment_id,
                    room_id=room.room_id,
                    element=element,
                    area_m2=area_m2,
                    u_value_W_m2K=u_value,
                    delta_t_K=delta_t,
                    qf_W=qf,
                    construction_id=construction_id,
                )
            )

        # --------------------------------------------------
        # Floor
        # --------------------------------------------------

        floor_area = g.floor_area_m2()
        if floor_area is not None and floor_area > 0.0:
            floor_cid = "DEV-ROOF"
            floor_u = project.construction_library.get(floor_cid)
            floor_dt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=project,
                owner_room=room,
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )

            floor_qf = None
            if floor_u is not None and floor_dt is not None:
                floor_qf = float(floor_u) * float(floor_area) * float(floor_dt)

            rows.append(
                FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-floor",
                    room_id=room.room_id,
                    element="floor",
                    area_m2=float(floor_area),
                    u_value_W_m2K=floor_u,
                    delta_t_K=floor_dt,
                    qf_W=floor_qf,
                    construction_id=floor_cid,
                )
            )

            # --------------------------------------------------
            # Roof
            # --------------------------------------------------

            roof_cid = "DEV-ROOF"
            roof_u = project.construction_library.get(roof_cid)
            roof_dt = floor_dt

            roof_qf = None
            if roof_u is not None and roof_dt is not None:
                roof_qf = float(roof_u) * float(floor_area) * float(roof_dt)

            rows.append(
                FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-roof",
                    room_id=room.room_id,
                    element="roof",
                    area_m2=float(floor_area),
                    u_value_W_m2K=roof_u,
                    delta_t_K=roof_dt,
                    qf_W=roof_qf,
                    construction_id=roof_cid,
                )
            )

        return rows