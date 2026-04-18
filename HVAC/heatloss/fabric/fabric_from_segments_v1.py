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

        # --------------------------------------------------
        # Resolve height
        # --------------------------------------------------
        height_m = g.height_m
        if height_m is None and project.environment is not None:
            height_m = project.environment.default_room_height_m

        if not height_m or height_m <= 0.0:
            return rows

        # ==============================================================
        # WALLS (topology-driven)
        # ==============================================================

        for seg in project.get_boundary_segments_for_room(room.room_id):

            gross_area = float(seg.length_m) * float(height_m)

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

            assigned_cid = ConstructionWizard.get_surface_construction(
                project,
                seg.segment_id,
            )

            cid = assigned_cid or base_cid
            u_value = project.construction_library.get(cid)

            # --------------------------------------------------
            # OPENINGS
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

                # openings always external for now
                odt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                    project_state=project,
                    owner_room=room,
                    boundary_kind="EXTERNAL",
                    adjacent_room_id=None,
                )

                oqf = (
                    float(ou) * float(area_o) * float(odt)
                    if ou and odt and area_o > 0.0
                    else None
                )

                row_o = FabricSurfaceRowV1(
                    surface_id=getattr(o, "opening_id", f"{seg.segment_id}-opening"),
                    room_id=room.room_id,
                    element=getattr(o, "kind", "window").lower(),
                    area_m2=area_o,
                    u_value_W_m2K=ou,
                    delta_t_K=odt,
                    qf_W=oqf,
                    construction_id=ocid,
                    _segment=seg,  # 🔥 CRITICAL
                )

                setattr(row_o, "parent_surface_id", seg.segment_id)
                opening_rows.append(row_o)

            # --------------------------------------------------
            # NET WALL
            # --------------------------------------------------

            net_area = max(gross_area - opening_area_total, 0.0)

            delta_t = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=project,
                owner_room=room,
                boundary_kind=seg.boundary_kind,
                adjacent_room_id=seg.adjacent_room_id,
            )

            qf = (
                float(u_value) * float(net_area) * float(delta_t)
                if u_value and delta_t and net_area > 0.0
                else None
            )

            row_wall = FabricSurfaceRowV1(
                surface_id=seg.segment_id,
                room_id=room.room_id,
                element=element,
                area_m2=net_area,
                u_value_W_m2K=u_value,
                delta_t_K=delta_t,
                qf_W=qf,
                construction_id=cid,
                _segment=seg,  # 🔥 CRITICAL (was missing)
            )

            setattr(row_wall, "parent_surface_id", None)

            rows.append(row_wall)
            rows.extend(opening_rows)

        # ==============================================================
        # FLOOR + ROOF
        # ==============================================================

        if g.length_m and g.width_m:

            area = float(g.length_m) * float(g.width_m)

            cid = "DEV-ROOF"
            u = project.construction_library.get(cid)

            dt = AdjacencyDeltaTResolver.resolve_delta_t_K(
                project_state=project,
                owner_room=room,
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )

            qf = float(u) * float(area) * float(dt) if u and dt else None

            rows.append(
                FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-floor",
                    room_id=room.room_id,
                    element="floor",
                    area_m2=area,
                    u_value_W_m2K=u,
                    delta_t_K=dt,
                    qf_W=qf,
                    construction_id=cid,
                    _segment=None,  # no adjacency
                )
            )

            rows.append(
                FabricSurfaceRowV1(
                    surface_id=f"{room.room_id}-roof",
                    room_id=room.room_id,
                    element="roof",
                    area_m2=area,
                    u_value_W_m2K=u,
                    delta_t_K=dt,
                    qf_W=qf,
                    construction_id=cid,
                    _segment=None,
                )
            )

        return rows