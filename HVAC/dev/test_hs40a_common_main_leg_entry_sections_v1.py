from __future__ import annotations

from types import SimpleNamespace

from HVAC.hydronics.proportioning.common_main_leg_entry_sections_v1 import (
    COMMON_MAIN_SECTION_KIND,
    LEG_ENTRY_SECTION_KIND,
    build_common_main_leg_entry_sections_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.project.project_state import ProjectState


def _primary(leg_id: str, label: str, room_ids: list[str]) -> HydronicSublegV1:
    return HydronicSublegV1(
        subleg_id=f"{leg_id}-primary-subleg",
        label=label,
        origin_room_id="heat-source",
        route_room_ids=list(room_ids),
        index_room_id=room_ids[-1],
    )


def _leg(leg_id: str, label: str, room_ids: list[str]) -> HydronicLegV1:
    return HydronicLegV1(
        leg_id=leg_id,
        label=label,
        route_room_ids=list(room_ids),
        index_room_id=room_ids[-1],
        sublegs=[_primary(leg_id, f"{label} common subleg", room_ids)],
    )


def _project() -> ProjectState:
    project = ProjectState(project_id="hs40a", name="H-S40-A")
    project.environment = SimpleNamespace(
        design_flow_temp_c=75.0,
        design_return_temp_c=65.0,
    )
    project.rooms = {
        "heat-source": SimpleNamespace(name="Boiler / Heat Source"),
        "room-1": SimpleNamespace(name="Leg 1 Room"),
        "room-2": SimpleNamespace(name="Leg 2 Room"),
    }
    project.emitters = {
        "emitter-1": SimpleNamespace(
            room_id="room-1",
            design_output_W=1000.0,
            flow_temp_C=75.0,
            return_temp_C=65.0,
        ),
        "emitter-2": SimpleNamespace(
            room_id="room-2",
            design_output_W=700.0,
            flow_temp_C=75.0,
            return_temp_C=65.0,
        ),
    }
    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="heat-source",
        legs=[
            _leg("leg-001", "Heating Leg 1", ["room-1"]),
            _leg("leg-002", "Heating Leg 2", ["room-2"]),
        ],
    )
    return project


def main() -> None:
    project = _project()
    projection = build_common_main_leg_entry_sections_v1(project)

    assert projection.ready is True, projection.blockers
    assert len(projection.common_main_sections) == 2
    assert len(projection.leg_entry_sections) == 2
    assert len(projection.sections) == 4

    main_1, main_2 = projection.common_main_sections
    entry_1, entry_2 = projection.leg_entry_sections

    assert main_1.section_id == "common-main-to-leg-001-section-001"
    assert main_2.section_id == "common-main-to-leg-002-section-001"
    assert main_1.section_kind == COMMON_MAIN_SECTION_KIND
    assert main_1.takeoff_leg_id == "leg-001"
    assert main_2.takeoff_leg_id == "leg-002"
    assert main_1.carried_leg_ids == ("leg-001", "leg-002")
    assert main_2.carried_leg_ids == ("leg-002",)
    assert main_1.carried_room_ids == ("room-1", "room-2")
    assert main_2.carried_room_ids == ("room-2",)
    assert main_1.carried_heat_W == 1700.0
    assert main_2.carried_heat_W == 700.0
    assert main_1.carried_flow_kg_s is not None
    assert main_2.carried_flow_kg_s is not None
    assert main_1.carried_flow_kg_s > main_2.carried_flow_kg_s

    assert entry_1.section_id == "leg-001-entry-section-001"
    assert entry_2.section_id == "leg-002-entry-section-001"
    assert entry_1.section_kind == LEG_ENTRY_SECTION_KIND
    assert entry_1.carried_leg_ids == ("leg-001",)
    assert entry_2.carried_leg_ids == ("leg-002",)

    persisted = project.hydronic_topology.to_dict()
    restored = HydronicTopologyV1.from_dict(persisted)
    assert [leg.leg_id for leg in restored.legs] == ["leg-001", "leg-002"]

    project.hydronic_topology.legs.reverse()
    reversed_projection = build_common_main_leg_entry_sections_v1(project)
    assert reversed_projection.ready is True
    assert [
        row.takeoff_leg_id for row in reversed_projection.common_main_sections
    ] == ["leg-002", "leg-001"]
    assert [
        row.section_id for row in reversed_projection.common_main_sections
    ] == [
        "common-main-to-leg-002-section-001",
        "common-main-to-leg-001-section-001",
    ]
    assert {
        row.section_id for row in reversed_projection.common_main_sections
    } == {
        main_1.section_id,
        main_2.section_id,
    }
    assert {
        row.section_id for row in reversed_projection.leg_entry_sections
    } == {
        "leg-001-entry-section-001",
        "leg-002-entry-section-001",
    }

    print("OK — H-S40-A stable common-main and leg-entry sections passed.")


if __name__ == "__main__":
    main()
