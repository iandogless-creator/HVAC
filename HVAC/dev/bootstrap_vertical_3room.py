# ======================================================================
# HVAC/dev/bootstrap_vertical_3room.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.core.construction_v1 import ConstructionV1
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ----------------------------------------------------------------------
# helper
# ----------------------------------------------------------------------

def seg(seg_id, owner, geom, kind, adj):
    return BoundarySegmentV1(
        segment_id=seg_id,
        owner_room_id=owner,
        geometry_ref=geom,
        length_m=0.0,          # not used for floor/roof
        boundary_kind=kind,
        adjacent_room_id=adj,
    )


# ----------------------------------------------------------------------
# bootstrap
# ----------------------------------------------------------------------

def build_vertical_stack_project_state() -> ProjectState:

    ps = ProjectState(
        project_id="DEV-VERTICAL-001",
        name="Vertical Stack DEV",
    )
    ps.project_dir = None
    # --------------------------------------------------
    # Environment
    # --------------------------------------------------

    ps.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
    )

    # --------------------------------------------------
    # Constructions (canonical)
    # --------------------------------------------------

    from HVAC.dev.dev_constructions import ensure_dev_constructions
    # --------------------------------------------------
    # Constructions (canonical)
    # --------------------------------------------------

    ps.constructions = {}
    ensure_dev_constructions(ps)
    # --------------------------------------------------
    # Rooms
    # --------------------------------------------------

    def make_room(rid, name):
        r = RoomStateV1(room_id=rid, name=name)
        r.geometry = RoomGeometryV1(
            length_m=4.0,
            width_m=3.0,
            height_m=2.4,
        )
        return r

    r1 = make_room("room-001", "Ground")
    r2 = make_room("room-002", "Middle")
    r3 = make_room("room-003", "Top")

    ps.rooms = {
        r1.room_id: r1,
        r2.room_id: r2,
        r3.room_id: r3,
    }
    r4 = make_room("room-004", "Ground Adj")
    r5 = make_room("room-005", "Middle Adj")
    r6 = make_room("room-006", "Top Adj")

    ps.rooms.update({
        r4.room_id: r4,
        r5.room_id: r5,
        r6.room_id: r6,
    })
    # --------------------------------------------------
    # Temperature field (multi-zone test)
    # --------------------------------------------------

    ps.rooms["room-001"].internal_temp_C = 21.0  # reference
    ps.rooms["room-002"].internal_temp_C = 20.0  # slight drop
    ps.rooms["room-003"].internal_temp_C = 23.0  # warmer top

    ps.rooms["room-004"].internal_temp_C = 18.0  # cold adjacent
    ps.rooms["room-005"].internal_temp_C = 22.0  # slightly warm adjacent
    ps.rooms["room-006"].internal_temp_C = 25.0  # hot adjacent
    # --------------------------------------------------
    # Topology (VERTICAL ADJACENCY)
    # --------------------------------------------------

    ps.boundary_segments = {}

    def add(s):
        ps.boundary_segments[s.segment_id] = s

    # -----------------------------
    # room-001 (bottom)
    # -----------------------------
    add(seg("r1-floor", "room-001", "floor", "EXTERNAL", None))
    add(seg("r1-ceil",  "room-001", "ceiling", "INTER_ROOM", "room-002"))
    add(seg("r1-wall-e", "room-001", "wall", "INTER_ROOM", "room-004"))
    add(seg("r4-wall-w", "room-004", "wall", "INTER_ROOM", "room-001"))
    # -----------------------------
    # room-002 (middle)
    # -----------------------------
    add(seg("r2-floor", "room-002", "floor", "INTER_ROOM", "room-001"))
    add(seg("r2-ceil",  "room-002", "ceiling", "INTER_ROOM", "room-003"))
    add(seg("r2-wall-e", "room-002", "wall", "INTER_ROOM", "room-005"))
    add(seg("r5-wall-w", "room-005", "wall", "INTER_ROOM", "room-002"))
    # -----------------------------
    # room-003 (top)
    # -----------------------------
    add(seg("r3-floor", "room-003", "floor", "INTER_ROOM", "room-002"))
    add(seg("r3-ceil",  "room-003", "ceiling", "EXTERNAL", None))
    add(seg("r3-wall-e", "room-003", "wall", "INTER_ROOM", "room-006"))
    add(seg("r6-wall-w", "room-006", "wall", "INTER_ROOM", "room-003"))
    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    ps.mark_heatloss_dirty()

    return ps