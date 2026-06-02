# ======================================================================
# HVAC/dev/bootstrap_hydronic_20_room_multileg.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1, RoomGeometryV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicTopologyV1,
    HydronicLegV1,
    HydronicSublegV1,
)
from HVAC.hydronics.local_losses.local_k_intent_v1 import (
    LocalKIntentV1,
    LocalKSectionIntentV1,
)

def build_hydronic_20_room_multileg_project_v1() -> ProjectState:
    """
    DEV fixture:
    20 downstream rooms, 2 hydronic legs, 4 room-carrying sublegs.

    Purpose:
    - test multi-leg / multi-subleg topology
    - test future route Δp accumulation across multiple routes
    - no balancing
    - no pump selection
    - no final proportioning
    """
    project = ProjectState(
        project_id="DEV-HYDRONIC-20-ROOM-MULTILEG",
        name="DEV Hydronic 20 Room Multi-leg",
    )

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
    )

    _install_rooms(project)
    _install_emitters(project)
    _install_topology(project)
    _install_local_k_intent(project)
    project.hydronics_valid = False
    return project


def _install_rooms(project: ProjectState) -> None:
    specs = [("room-boiler", "Boiler / Heat Source")]

    for prefix, count in (
        ("l1a", 6),
        ("l1b", 4),
        ("l2a", 5),
        ("l2b", 5),
    ):
        label_prefix = prefix.upper()
        for index in range(1, count + 1):
            specs.append(
                (
                    f"room-{prefix}-{index:03d}",
                    f"{label_prefix}-R{index:02d}",
                )
            )

    for room_id, name in specs:
        project.rooms[room_id] = RoomStateV1(
            room_id=room_id,
            name=name,
            geometry=RoomGeometryV1(
                length_m=4.0,
                width_m=3.0,
                height_m=2.4,
            ),
        )


def _install_emitters(project: ProjectState) -> None:
    loads_by_route = {
        "l1a": [900, 800, 700, 600, 500, 400],
        "l1b": [1100, 900, 700, 500],
        "l2a": [1200, 1000, 800, 600, 400],
        "l2b": [1000, 850, 700, 550, 400],
    }

    for prefix, loads in loads_by_route.items():
        for index, load_W in enumerate(loads, start=1):
            room_id = f"room-{prefix}-{index:03d}"
            emitter_id = f"emitter-{prefix}-{index:03d}"

            project.emitters[emitter_id] = EmitterV1(
                emitter_id=emitter_id,
                room_id=room_id,
                name=f"Emitter {prefix.upper()}-{index:02d}",
                emitter_type="radiator",
                design_output_W=float(load_W),
                flow_temp_C=75.0,
                return_temp_C=55.0,
                room_temp_C=21.0,
                notes="DEV 20-room multi-leg fixture",
            )


def _route(prefix: str, count: int) -> list[str]:
    return [f"room-{prefix}-{index:03d}" for index in range(1, count + 1)]


def _install_topology(project: ProjectState) -> None:
    l1a_rooms = _route("l1a", 6)
    l1b_rooms = _route("l1b", 4)
    l2a_rooms = _route("l2a", 5)
    l2b_rooms = _route("l2b", 5)

    leg_001 = HydronicLegV1(
        leg_id="leg-001",
        label="Heating Leg 1",
        # Transitional mirror: primary/common subleg rooms only.
        route_room_ids=list(l1a_rooms),
        index_room_id=l1a_rooms[-1],
        sublegs=[
            HydronicSublegV1(
                subleg_id="leg-001-primary-subleg",
                label="Leg 1A Common subleg",
                origin_room_id="common-main",
                route_room_ids=list(l1a_rooms),
                index_room_id=l1a_rooms[-1],
                sublegs=[],
            ),
            HydronicSublegV1(
                subleg_id="leg-001-subleg-b",
                label="Leg 1B Branch subleg",
                origin_room_id=l1a_rooms[1],
                route_room_ids=list(l1b_rooms),
                index_room_id=l1b_rooms[-1],
                sublegs=[],
            ),
        ],
    )

    leg_002 = HydronicLegV1(
        leg_id="leg-002",
        label="Heating Leg 2",
        # Transitional mirror: primary/common subleg rooms only.
        route_room_ids=list(l2a_rooms),
        index_room_id=l2a_rooms[-1],
        sublegs=[
            HydronicSublegV1(
                subleg_id="leg-002-primary-subleg",
                label="Leg 2A Common subleg",
                origin_room_id="common-main",
                route_room_ids=list(l2a_rooms),
                index_room_id=l2a_rooms[-1],
                sublegs=[],
            ),
            HydronicSublegV1(
                subleg_id="leg-002-subleg-b",
                label="Leg 2B Branch subleg",
                origin_room_id=l2a_rooms[1],
                route_room_ids=list(l2b_rooms),
                index_room_id=l2b_rooms[-1],
                sublegs=[],
            ),
        ],
    )

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-boiler",
        legs=[leg_001, leg_002],
    )
def _install_local_k_intent(project: ProjectState) -> None:
    """
    H-S17-B:
    Deterministic Local K / section length intent for the 20-room fixture.

    Purpose:
    - complete all route Δp previews
    - make route ranking deterministic
    - no balancing
    - no pump selection
    """
    intent = LocalKIntentV1()

    # section_id, length_m, bend_90, bend_45, tee_through, tee_branch, misc_k
    section_specs = [
        # Leg 1A common subleg — 6 sections
        ("leg-001-primary-subleg-section-001", 5.0, 2, 0, 1, 1, 0.0),
        ("leg-001-primary-subleg-section-002", 4.0, 1, 1, 1, 1, 0.0),
        ("leg-001-primary-subleg-section-003", 4.5, 2, 0, 1, 0, 0.0),
        ("leg-001-primary-subleg-section-004", 3.5, 1, 1, 1, 0, 0.0),
        ("leg-001-primary-subleg-section-005", 3.0, 1, 0, 1, 0, 0.0),
        ("leg-001-primary-subleg-section-006", 2.5, 1, 0, 0, 0, 0.0),

        # Leg 1B branch subleg — deliberately longer/fittier
        ("leg-001-subleg-b-section-001", 6.0, 3, 1, 1, 1, 0.0),
        ("leg-001-subleg-b-section-002", 5.5, 2, 1, 1, 0, 0.0),
        ("leg-001-subleg-b-section-003", 5.0, 2, 0, 1, 0, 0.0),
        ("leg-001-subleg-b-section-004", 4.5, 1, 1, 0, 0, 0.0),

        # Leg 2A common subleg — heavier load, moderate lengths
        ("leg-002-primary-subleg-section-001", 5.0, 2, 0, 1, 1, 0.0),
        ("leg-002-primary-subleg-section-002", 4.5, 2, 1, 1, 1, 0.0),
        ("leg-002-primary-subleg-section-003", 4.0, 1, 1, 1, 0, 0.0),
        ("leg-002-primary-subleg-section-004", 3.5, 1, 0, 1, 0, 0.0),
        ("leg-002-primary-subleg-section-005", 3.0, 1, 0, 0, 0, 0.0),

        # Leg 2B branch subleg — intended strong controlling candidate
        ("leg-002-subleg-b-section-001", 7.0, 3, 1, 1, 1, 0.0),
        ("leg-002-subleg-b-section-002", 6.0, 3, 1, 1, 0, 0.0),
        ("leg-002-subleg-b-section-003", 5.5, 2, 1, 1, 0, 0.0),
        ("leg-002-subleg-b-section-004", 5.0, 2, 0, 1, 0, 0.0),
        ("leg-002-subleg-b-section-005", 4.5, 1, 1, 0, 0, 0.0),
    ]

    for (
        section_id,
        length_m,
        bend_90_count,
        bend_45_count,
        tee_through_count,
        tee_branch_count,
        misc_k,
    ) in section_specs:
        intent.sections[section_id] = LocalKSectionIntentV1(
            section_id=section_id,
            bend_90_count=bend_90_count,
            bend_45_count=bend_45_count,
            tee_through_count=tee_through_count,
            tee_branch_count=tee_branch_count,
            isolation_valve_count=0,
            trv_count=0,
            lockshield_count=0,
            misc_k=float(misc_k),
            length_m=float(length_m),
        )

    project.hydronic_local_k_intent = intent

if __name__ == "__main__":
    ps = build_hydronic_20_room_multileg_project_v1()
    print(ps.name)
    print("Rooms:", len(ps.rooms))
    print("Emitters:", len(ps.emitters))
    print("Heat source:", ps.hydronic_topology.heat_source_room_id)