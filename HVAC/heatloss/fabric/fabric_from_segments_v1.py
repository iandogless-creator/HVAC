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


DEFAULT_INTERNAL_CONSTRUCTION_ID = "DEV-INTERNAL-WALL"


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

        height_m = g.height_m
        if height_m is None and project.environment is not None:
            height_m = project.environment.default_room_height_m

        if height_m is None or height_m <= 0.0:
            return rows

        # ==============================================================
        # WALLS (with openings)
        # ==============================================================

        for seg in project.get_boundary_segments_for_room(room.room_id):

            gross_area_m2 = float(seg.length_m) * float(height_m)

            # --------------------------------------------------
            # Element + construction
            # --------------------------------------------------

            if seg.boundary_kind == "EXTERNAL":
                element = "external_wall"
                base_cid = "DEV-WALL"

            elif seg.boundary_kind == "INTER_ROOM":
                element = "internal_partition"
                base_cid = DEFAULT_INTERNAL_CONSTRUCTION_ID

            else:
                element = "adiabatic_wall"
                base_cid = "DEV-WALL"

            assigned = ConstructionWizard.get_surface_construction(
                project,
                seg.segment_id,
            )

            cid = assigned or base_cid
            u_value = project.construction_library.get(cid)

            # --------------------------------------------------
            # OPENINGS (children)
            # --------------------------------------------------

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

                ocid = getattr(o, "construction_id", None)
                ou = project.construction_library.get(ocid)

                odt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                    project_state=project,
                    owner_room=room,
                    boundary_kind="EXTERNAL",
                    adjacent_room_id=None,
                )

                oqf = None
                if ou is not None and odt is not None and area_o > 0.0:
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
                )

                # attach parent dynamically (DTO untouched)
                setattr(row_o, "parent_surface_id", seg.segment_id)

                opening_rows.append(row_o)

            # --------------------------------------------------
            # NET WALL AREA
            # --------------------------------------------------

            net_area_m2 = max(gross_area_m2 - opening_area_total, 0.0)

            delta_t = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=project,
                owner_room=room,
                boundary_kind=seg.boundary_kind,
                adjacent_room_id=seg.adjacent_room_id,
            )

            qf = None
            if u_value is not None and delta_t is not None and net_area_m2 > 0.0:
                qf = float(u_value) * float(net_area_m2) * float(delta_t)

            # --------------------------------------------------
            # WALL ROW (parent)
            # --------------------------------------------------

            row_wall = FabricSurfaceRowV1(
                surface_id=seg.segment_id,
                room_id=room.room_id,
                element=element,
                area_m2=net_area_m2,
                u_value_W_m2K=u_value,
                delta_t_K=delta_t,
                qf_W=qf,
                construction_id=cid,
            )

            setattr(row_wall, "parent_surface_id", None)

            rows.append(row_wall)
            rows.extend(opening_rows)

        # ==============================================================
        # FLOOR + ROOF
        # ==============================================================

        floor_area = g.floor_area_m2

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

            rows.append(
                FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-roof",
                    room_id=room.room_id,
                    element="roof",
                    area_m2=float(floor_area),
                    u_value_W_m2K=floor_u,
                    delta_t_K=floor_dt,
                    qf_W=floor_qf,
                    construction_id=floor_cid,
                )
            )

        return rows