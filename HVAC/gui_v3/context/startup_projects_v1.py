"""Beta 1 startup reuses existing GUI project preparation, with no saved writes."""
from pathlib import Path
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.project_factory_v3 import ProjectFactoryV3
from HVAC.project_v3.persistence.loader import load as load_project


def create_default_room_v1(project: ProjectState) -> str:
    room_id = "room-001"

    from HVAC.core.room_state import RoomStateV1, RoomGeometryV1

    room = RoomStateV1(
        room_id=room_id,
        name="Room 1",
        geometry=RoomGeometryV1(
            length_m=4.0,
            width_m=3.0,
            height_m=2.4,
            external_wall_length_m=14.0,
        ),
    )

    # ❌ REMOVE THIS (legacy)
    # room.fabric_elements = []

    project.rooms[room_id] = room
    return room_id


def create_new_project_v1() -> ProjectState:
    project_state = ProjectFactoryV3.create_default()

    # --------------------------------------------------
    # Create default room
    # --------------------------------------------------
    room_id = create_default_room_v1(project_state)

    # --------------------------------------------------
    # Build topology (canonical)
    # --------------------------------------------------
    from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
    from HVAC.topology.topology_symmetry_enforcer_v1 import TopologySymmetryEnforcerV1

    TopologyResolverV1.resolve_project(project_state)
    TopologySymmetryEnforcerV1.enforce(project_state)

    # 🔒 Safety check
    if not project_state.boundary_segments:
        raise RuntimeError("Topology creation failed")

    print(f"[TOPOLOGY] created: {len(project_state.boundary_segments)} segments")

    return project_state


def open_project_v1(project_dir: Path) -> ProjectState:
    ps = load_project(project_dir)

    # --------------------------------------------------
    # 🔥 DROP LEGACY TOPOLOGY
    # --------------------------------------------------
    ps.boundary_segments = {}

    # --------------------------------------------------
    # Ensure constructions (Phase V-A)
    # --------------------------------------------------
    from HVAC.core.construction_v1 import ConstructionV1

    def _ensure_construction(ps, cid, name, u):
        if cid not in ps.constructions:
            ps.constructions[cid] = ConstructionV1(cid, name, u)

    _ensure_construction(ps, "DEV-EXT-WALL", "External Wall", 0.26)
    _ensure_construction(ps, "DEV-ROOF", "Roof / Ceiling", 0.16)
    _ensure_construction(ps, "DEV-WINDOW", "Window / Door", 1.60)
    _ensure_construction(ps, "DEV-INT-WALL", "Internal Wall", 1.50)
    _ensure_construction(ps, "DEV-FLOOR", "Floor", 0.18)


    # --------------------------------------------------
    # Normalise environment
    # --------------------------------------------------
    env = ps.environment

    if env.default_internal_temp_C is None:
        env.default_internal_temp_C = 21.0

    if env.default_room_height_m is None:
        env.default_room_height_m = 2.4

    if env.default_ach is None:
        env.default_ach = 0.5

    # --------------------------------------------------
    # Rebuild topology (canonical)
    # --------------------------------------------------
    from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
    from HVAC.topology.topology_symmetry_enforcer_v1 import TopologySymmetryEnforcerV1

    TopologyResolverV1.resolve_project(ps)
    TopologySymmetryEnforcerV1.enforce(ps)

    print(f"[TOPOLOGY] rebuilt: {len(ps.boundary_segments)} segments")

    return ps
