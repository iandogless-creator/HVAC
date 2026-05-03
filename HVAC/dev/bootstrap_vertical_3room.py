# ======================================================================
# HVAC/dev/bootstrap_vertical_3room.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

ROOM_LENGTH_M = 4.0
ROOM_WIDTH_M = 3.0
ROOM_HEIGHT_M = 2.4

# Wall segment length chosen to produce:
# 4.0 m × 2.4 m = 9.60 m²
WALL_LENGTH_M = ROOM_LENGTH_M


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def seg(
    seg_id: str,
    owner: str,
    geom: str,
    kind: str,
    adj: str | None,
    *,
    length_m: float = 0.0,
) -> BoundarySegmentV1:
    """
    DEV boundary segment helper.

    Notes
    -----
    • wall segments must carry length_m because wall area is derived as
      segment.length_m × room height.
    • floor/ceiling segments keep length_m=0.0 because their area is
      derived from room length × width.
    """

    return BoundarySegmentV1(
        segment_id=seg_id,
        owner_room_id=owner,
        geometry_ref=geom,
        length_m=length_m,
        boundary_kind=kind,
        adjacent_room_id=adj,
    )


# ----------------------------------------------------------------------
# Bootstrap
# ----------------------------------------------------------------------

def build_vertical_stack_project_state() -> ProjectState:
    """
    DEV vertical-stack project.

    v1 naming convention
    --------------------
    • Boiler Room
    • First Floor
    • Second Floor
    • Gnd Adj
    • 1st Adj
    • 2nd Adj

    Topology intent
    ---------------
    • vertical adjacency uses floor/ceiling geometry
    • same-storey adjacency uses wall geometry
    • room_id remains canonical; names are display labels
    """

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
        default_room_height_m=ROOM_HEIGHT_M,
        default_ach=0.5,
    )

    # --------------------------------------------------
    # Constructions
    # --------------------------------------------------

    from HVAC.dev.dev_constructions import ensure_dev_constructions

    ps.constructions = {}
    ensure_dev_constructions(ps)

    # --------------------------------------------------
    # Rooms
    # --------------------------------------------------

    def make_room(rid: str, name: str) -> RoomStateV1:
        room = RoomStateV1(room_id=rid, name=name)
        room.geometry = RoomGeometryV1(
            length_m=ROOM_LENGTH_M,
            width_m=ROOM_WIDTH_M,
            height_m=ROOM_HEIGHT_M,
        )
        return room

    r1 = make_room("room-001", "Boiler Room")
    r2 = make_room("room-002", "First Floor")
    r3 = make_room("room-003", "Second Floor")
    r4 = make_room("room-004", "Gnd Adj")
    r5 = make_room("room-005", "1st Adj")
    r6 = make_room("room-006", "2nd Adj")

    ps.rooms = {
        r1.room_id: r1,
        r2.room_id: r2,
        r3.room_id: r3,
        r4.room_id: r4,
        r5.room_id: r5,
        r6.room_id: r6,
    }

    # --------------------------------------------------
    # Temperature field
    # --------------------------------------------------
    # Deliberately varied to prove ΔT resolution:
    #
    # Boiler Room → First Floor:
    #   21 - 20 = +1 K
    #
    # First Floor → Boiler Room:
    #   20 - 21 = -1 K
    #
    # First Floor → Second Floor:
    #   20 - 23 = -3 K
    #
    # Same-storey adjacencies:
    #   Boiler Room → Gnd Adj = 21 - 18 = +3 K
    #   First Floor → 1st Adj = 20 - 22 = -2 K
    #   Second Floor → 2nd Adj = 23 - 25 = -2 K
    # --------------------------------------------------

    ps.rooms["room-001"].internal_temp_C = 21.0
    ps.rooms["room-002"].internal_temp_C = 20.0
    ps.rooms["room-003"].internal_temp_C = 23.0

    ps.rooms["room-004"].internal_temp_C = 18.0
    ps.rooms["room-005"].internal_temp_C = 22.0
    ps.rooms["room-006"].internal_temp_C = 25.0

    # --------------------------------------------------
    # Topology
    # --------------------------------------------------
    # Vertical stack:
    #
    # room-003 Second Floor
    #   floor   → room-002
    #   ceiling → external roof
    #
    # room-002 First Floor
    #   floor   → room-001
    #   ceiling → room-003
    #
    # room-001 Boiler Room
    #   floor   → external
    #   ceiling → room-002
    #
    # Side adjacencies are same-storey wall adjacencies:
    #   room-001 wall → room-004
    #   room-002 wall → room-005
    #   room-003 wall → room-006
    # --------------------------------------------------

    ps.boundary_segments = {}

    def add(segment: BoundarySegmentV1) -> None:
        ps.boundary_segments[segment.segment_id] = segment

    # -----------------------------
    # room-001 — Boiler Room
    # -----------------------------

    add(seg("r1-floor", "room-001", "floor", "EXTERNAL", None))
    add(seg("r1-ceil", "room-001", "ceiling", "INTER_ROOM", "room-002"))
    add(seg("r1-wall-e", "room-001", "wall", "INTER_ROOM", "room-004", length_m=WALL_LENGTH_M))
    add(seg("r4-wall-w", "room-004", "wall", "INTER_ROOM", "room-001", length_m=WALL_LENGTH_M))

    # -----------------------------
    # room-002 — First Floor
    # -----------------------------

    add(seg("r2-floor", "room-002", "floor", "INTER_ROOM", "room-001"))
    add(seg("r2-ceil", "room-002", "ceiling", "INTER_ROOM", "room-003"))
    add(seg("r2-wall-e", "room-002", "wall", "INTER_ROOM", "room-005", length_m=WALL_LENGTH_M))
    add(seg("r5-wall-w", "room-005", "wall", "INTER_ROOM", "room-002", length_m=WALL_LENGTH_M))

    # -----------------------------
    # room-003 — Second Floor
    # -----------------------------

    add(seg("r3-floor", "room-003", "floor", "INTER_ROOM", "room-002"))
    add(seg("r3-ceil", "room-003", "ceiling", "EXTERNAL", None))
    add(seg("r3-wall-e", "room-003", "wall", "INTER_ROOM", "room-006", length_m=WALL_LENGTH_M))
    add(seg("r6-wall-w", "room-006", "wall", "INTER_ROOM", "room-003", length_m=WALL_LENGTH_M))

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    ps.mark_heatloss_dirty()

    return ps