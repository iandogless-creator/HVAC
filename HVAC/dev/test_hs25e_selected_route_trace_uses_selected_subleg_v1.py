# ======================================================================
# HVAC/dev/test_hs25e_selected_route_trace_uses_selected_subleg_v1.py
# H-S25-E — Selected route trace uses controlling/selected subleg authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.proportioning_schematic_projection_v1 import (
    build_proportioning_schematic_v1,
)
from HVAC.hydronics.proportioning.proportioning_schematic_dto_v1 import (
    NODE_ROLE_SELECTED_INDEX_ROUTE,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.project.project_state import ProjectState


@dataclass(frozen=True, slots=True)
class _DummyRoutePressureRow:
    route_id: str
    route_label: str
    leg_id: str
    subleg_id: str
    is_controlling_candidate: bool


@dataclass(frozen=True, slots=True)
class _DummyRoutePressureProjection:
    rows: tuple[_DummyRoutePressureRow, ...]


def _build_project() -> ProjectState:
    project = ProjectState(
        project_id="dev-hs25e-selected-route-trace",
        name="DEV H-S25-E Selected Route Trace",
    )

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="boiler-room",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=["room-l1a-001", "room-l1a-002"],
                index_room_id="room-l1a-002",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id="leg-001-primary-subleg",
                        label="Leg 1A Common subleg",
                        origin_room_id="boiler-room",
                        route_room_ids=["room-l1a-001", "room-l1a-002"],
                        index_room_id="room-l1a-002",
                    ),
                    HydronicSublegV1(
                        subleg_id="leg-001-subleg-b",
                        label="Leg 1B Branch subleg",
                        origin_room_id="room-l1a-001",
                        route_room_ids=[
                            "room-l1b-001",
                            "room-l1b-002",
                            "room-l1b-003",
                        ],
                        index_room_id="room-l1b-003",
                    ),
                ],
            )
        ],
    )

    return project


def main() -> None:
    project = _build_project()

    route_pressure = _DummyRoutePressureProjection(
        rows=(
            _DummyRoutePressureRow(
                route_id="leg-001:leg-001-primary-subleg",
                route_label="Heating Leg 1 / Leg 1A Common subleg",
                leg_id="leg-001",
                subleg_id="leg-001-primary-subleg",
                is_controlling_candidate=False,
            ),
            _DummyRoutePressureRow(
                route_id="leg-001:leg-001-subleg-b",
                route_label="Heating Leg 1 / Leg 1B Branch subleg",
                leg_id="leg-001",
                subleg_id="leg-001-subleg-b",
                is_controlling_candidate=True,
            ),
        )
    )

    target = (
        HydronicsSchematicPanelAdapter
        ._selected_route_trace_target_from_route_pressure_projection(
            route_pressure
        )
    )

    schematic = build_proportioning_schematic_v1(
        project,
        selected_leg_id=target.get("leg_id"),
        selected_subleg_id=target.get("subleg_id"),
        selected_route_label=target.get("route_label"),
    )

    route_labels = [
        node.label
        for node in schematic.nodes
        if node.role == NODE_ROLE_SELECTED_INDEX_ROUTE
    ]

    index_labels = [
        node.label
        for node in schematic.nodes
        if node.role == NODE_ROLE_SELECTED_INDEX_ROUTE
        and node.is_index_node
    ]

    print()
    print("H-S25-E — Selected route trace uses selected/controlling subleg")
    print("==============================================================")
    print("target:", target)
    print("route labels:", route_labels)
    print("index labels:", index_labels)
    print("basis:", schematic.basis)

    assert target["subleg_id"] == "leg-001-subleg-b"
    assert route_labels == [
        "room-l1b-001",
        "room-l1b-002",
        "room-l1b-003",
    ]
    assert "room-l1a-001" not in route_labels
    assert "room-l1a-002" not in route_labels
    assert index_labels == ["room-l1b-003"]
    assert "Leg 1B Branch subleg" in schematic.basis

    print()
    print("OK — selected route trace follows controlling subleg authority.")


if __name__ == "__main__":
    main()
