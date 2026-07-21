from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    COMMON_ROUTE_DOWNSTREAM_ROLE,
    build_balancing_point_topology_authority_v1,
    common_subleg_downstream_balancing_point_id_v1,
    subleg_balancing_point_id_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)


def _point(projection, point_id: str):
    return next(
        row for row in projection.points
        if row.balancing_point_id == point_id
    )


def main() -> None:
    branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-b",
        label="Subleg 1B",
        origin_room_id="room-002",
        route_room_ids=["room-003", "room-004"],
        index_room_id="room-004",
    )
    common = HydronicSublegV1(
        subleg_id="leg-001-primary-subleg",
        label="Subleg 1A",
        origin_room_id="",
        route_room_ids=["room-001", "room-002"],
        index_room_id="room-002",
        sublegs=[branch],
    )
    topology = HydronicTopologyV1(
        heat_source_room_id="boiler-room",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=list(common.route_room_ids),
                index_room_id="room-004",
                sublegs=[common],
            )
        ],
    )
    before = deepcopy(topology.to_dict())
    projection = build_balancing_point_topology_authority_v1(
        SimpleNamespace(hydronic_topology=topology)
    )

    assert projection.ready is True
    assert topology.to_dict() == before
    assert len(projection.subleg_points) == 2
    assert len(projection.route_exclusive_points) == 1
    assert len({row.balancing_point_id for row in projection.points}) == len(
        projection.points
    )

    common_entry_id = subleg_balancing_point_id_v1(common.subleg_id)
    common_entry = _point(projection, common_entry_id)
    assert common_entry.point_role == "common"
    assert common_entry.anchor_section_id == (
        "leg-001-primary-subleg-section-001"
    )
    assert common_entry.downstream_route_ids == (
        "leg-001-primary-subleg",
        "leg-001-subleg-b",
    )
    assert common_entry.is_shared is True
    assert common_entry.is_route_exclusive is False

    downstream_id = common_subleg_downstream_balancing_point_id_v1(
        common.subleg_id
    )
    downstream = _point(projection, downstream_id)
    assert downstream.point_scope == "subleg"
    assert downstream.point_role == COMMON_ROUTE_DOWNSTREAM_ROLE
    assert downstream.parent_balancing_point_id == common_entry_id
    assert downstream.subleg_id == common.subleg_id
    assert downstream.downstream_route_ids == (common.subleg_id,)
    assert downstream.is_shared is False
    assert downstream.is_route_exclusive is True
    assert downstream.anchor_section_id == ""
    assert downstream.origin_room_id == ""
    assert "physical placement TBA" in downstream.status

    branch_entry = _point(
        projection,
        subleg_balancing_point_id_v1(branch.subleg_id),
    )
    assert branch_entry.parent_balancing_point_id == common_entry_id
    assert branch_entry.anchor_section_id == "leg-001-subleg-b-section-001"

    target = HydronicsSchematicPanelAdapter._balancing_point_target_id_v1(
        downstream_id,
        "subleg",
    )
    assert target == common.subleg_id

    no_branch_common = HydronicSublegV1(
        subleg_id="leg-002-primary-subleg",
        label="Subleg 2A",
        origin_room_id="",
        route_room_ids=["room-010"],
        index_room_id="room-010",
    )
    no_branch_projection = build_balancing_point_topology_authority_v1(
        SimpleNamespace(
            hydronic_topology=HydronicTopologyV1(
                heat_source_room_id="boiler-room",
                legs=[
                    HydronicLegV1(
                        leg_id="leg-002",
                        label="Heating Leg 2",
                        route_room_ids=["room-010"],
                        index_room_id="room-010",
                        sublegs=[no_branch_common],
                    )
                ],
            )
        )
    )
    assert no_branch_projection.ready is True
    assert no_branch_projection.route_exclusive_points == ()
    only_entry = _point(
        no_branch_projection,
        subleg_balancing_point_id_v1(no_branch_common.subleg_id),
    )
    assert only_entry.is_route_exclusive is True

    print(
        "OK — H-S44-A2 explicit common-route downstream balancing points "
        "preserve shared entry authority."
    )


if __name__ == "__main__":
    main()
