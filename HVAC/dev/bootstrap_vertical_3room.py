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

# v1 rectangular wall lengths.
# These are not CAD coordinates; they are heat-loss segment lengths.
WALL_LONG_M = ROOM_LENGTH_M      # 4.0 m wall
WALL_SHORT_M = ROOM_WIDTH_M      # 3.0 m wall


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

    Rules
    -----
    • wall segments carry length_m because wall area = length × height
    • floor/ceiling segments keep length_m=0.0 because area = L × W
    • adjacency is held by BoundarySegmentV1
    """

    return BoundarySegmentV1(
        segment_id=seg_id,
        owner_room_id=owner,
        geometry_ref=geom,
        length_m=length_m,
        boundary_kind=kind,
        adjacent_room_id=adj,
    )


def add_wall_set(
    *,
    add,
    room_id: str,
    prefix: str,
    inter_side: str | None = None,
    adjacent_room_id: str | None = None,
) -> None:
    """
    Add a complete four-wall enclosure for a room.

    v1 convention
    -------------
    north/south use ROOM_LENGTH_M
    east/west use ROOM_WIDTH_M

    One side may be INTER_ROOM.
    All other walls are EXTERNAL.
    """

    wall_defs = {
        "n": WALL_LONG_M,
        "s": WALL_LONG_M,
        "e": WALL_SHORT_M,
        "w": WALL_SHORT_M,
    }

    for side, length_m in wall_defs.items():
        is_internal = side == inter_side and adjacent_room_id is not None

        add(
            seg(
                f"{prefix}-wall-{side}",
                room_id,
                "wall",
                "INTER_ROOM" if is_internal else "EXTERNAL",
                adjacent_room_id if is_internal else None,
                length_m=length_m,
            )
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
    • every room has a complete enclosure
    • non-adjacent walls are EXTERNAL
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
    # Deliberately varied to prove ΔT resolution.
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
    #
    # Main stack:
    #
    #   room-003 Second Floor
    #       floor   → room-002
    #       ceiling → external roof
    #       west wall → room-006
    #
    #   room-002 First Floor
    #       floor   → room-001
    #       ceiling → room-003
    #       west wall → room-005
    #
    #   room-001 Boiler Room
    #       floor   → external
    #       ceiling → room-002
    #       west wall → room-004
    #
    # Side stack:
    #
    #   room-006 2nd Adj
    #       floor   → room-005
    #       ceiling → external roof
    #       east wall → room-003
    #
    #   room-005 1st Adj
    #       floor   → room-004
    #       ceiling → room-006
    #       east wall → room-002
    #
    #   room-004 Gnd Adj
    #       floor   → external
    #       ceiling → room-005
    #       east wall → room-001
    #
    # All other walls are EXTERNAL.
    # --------------------------------------------------

    ps.boundary_segments = {}

    def add(segment: BoundarySegmentV1) -> None:
        ps.boundary_segments[segment.segment_id] = segment

    # -----------------------------
    # room-001 — Boiler Room
    # -----------------------------

    add(seg("r1-floor", "room-001", "floor", "EXTERNAL", None))
    add(seg("r1-ceil", "room-001", "ceiling", "INTER_ROOM", "room-002"))

    add_wall_set(
        add=add,
        room_id="room-001",
        prefix="r1",
        inter_side="w",
        adjacent_room_id="room-004",
    )

    # -----------------------------
    # room-002 — First Floor
    # -----------------------------

    add(seg("r2-floor", "room-002", "floor", "INTER_ROOM", "room-001"))
    add(seg("r2-ceil", "room-002", "ceiling", "INTER_ROOM", "room-003"))

    add_wall_set(
        add=add,
        room_id="room-002",
        prefix="r2",
        inter_side="w",
        adjacent_room_id="room-005",
    )

    # -----------------------------
    # room-003 — Second Floor
    # -----------------------------

    add(seg("r3-floor", "room-003", "floor", "INTER_ROOM", "room-002"))
    add(seg("r3-ceil", "room-003", "ceiling", "EXTERNAL", None))

    add_wall_set(
        add=add,
        room_id="room-003",
        prefix="r3",
        inter_side="w",
        adjacent_room_id="room-006",
    )

    # -----------------------------
    # room-004 — Gnd Adj
    # -----------------------------

    add(seg("r4-floor", "room-004", "floor", "EXTERNAL", None))
    add(seg("r4-ceil", "room-004", "ceiling", "INTER_ROOM", "room-005"))

    add_wall_set(
        add=add,
        room_id="room-004",
        prefix="r4",
        inter_side="e",
        adjacent_room_id="room-001",
    )

    # -----------------------------
    # room-005 — 1st Adj
    # -----------------------------

    add(seg("r5-floor", "room-005", "floor", "INTER_ROOM", "room-004"))
    add(seg("r5-ceil", "room-005", "ceiling", "INTER_ROOM", "room-006"))

    add_wall_set(
        add=add,
        room_id="room-005",
        prefix="r5",
        inter_side="e",
        adjacent_room_id="room-002",
    )

    # -----------------------------
    # room-006 — 2nd Adj
    # -----------------------------

    add(seg("r6-floor", "room-006", "floor", "INTER_ROOM", "room-005"))
    add(seg("r6-ceil", "room-006", "ceiling", "EXTERNAL", None))

    add_wall_set(
        add=add,
        room_id="room-006",
        prefix="r6",
        inter_side="e",
        adjacent_room_id="room-003",
    )

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    ps.mark_heatloss_dirty()

    return ps