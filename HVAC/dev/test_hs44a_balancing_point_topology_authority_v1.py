from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    build_balancing_point_topology_authority_v1,
    leg_balancing_point_id_v1,
    main_balancing_point_id_v1,
    subleg_balancing_point_id_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)


def _subleg(
    subleg_id: str,
    label: str,
    rooms: list[str],
    *,
    origin: str = "",
    children: list[HydronicSublegV1] | None = None,
) -> HydronicSublegV1:
    return HydronicSublegV1(
        subleg_id=subleg_id,
        label=label,
        origin_room_id=origin,
        route_room_ids=list(rooms),
        index_room_id=rooms[-1] if rooms else None,
        sublegs=list(children or []),
    )


def _point(projection, point_id: str):
    return next(
        row for row in projection.points if row.balancing_point_id == point_id
    )


def main() -> None:
    branch_c = _subleg(
        "leg-001-subleg-c",
        "Subleg 1C",
        ["room-005"],
        origin="room-003",
    )
    branch_b = _subleg(
        "leg-001-subleg-b",
        "Subleg 1B",
        ["room-003", "room-004"],
        origin="room-002",
        children=[branch_c],
    )
    primary_1 = _subleg(
        "leg-001-primary-subleg",
        "Subleg 1A",
        ["room-001", "room-002"],
        children=[branch_b],
    )
    primary_2 = _subleg(
        "leg-002-primary-subleg",
        "Subleg 2A",
        ["room-006", "room-007"],
    )

    topology = HydronicTopologyV1(
        heat_source_room_id="boiler-room",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=list(primary_1.route_room_ids),
                index_room_id="room-005",
                sublegs=[primary_1],
            ),
            HydronicLegV1(
                leg_id="leg-002",
                label="Heating Leg 2",
                route_room_ids=list(primary_2.route_room_ids),
                index_room_id="room-007",
                sublegs=[primary_2],
            ),
        ],
    )
    before = deepcopy(topology.to_dict())
    project = SimpleNamespace(hydronic_topology=topology)

    projection = build_balancing_point_topology_authority_v1(project)

    assert projection.ready is True
    assert projection.blockers == ()
    assert len(projection.main_points) == 2
    assert len(projection.leg_points) == 2
    assert len(projection.subleg_points) == 4
    assert topology.to_dict() == before

    main_1 = _point(projection, main_balancing_point_id_v1("leg-001"))
    main_2 = _point(projection, main_balancing_point_id_v1("leg-002"))
    assert main_1.anchor_section_id == "common-main-to-leg-001-section-001"
    assert main_1.parent_balancing_point_id == ""
    assert main_1.downstream_route_ids == (
        "leg-001-primary-subleg",
        "leg-001-subleg-b",
        "leg-001-subleg-c",
        "leg-002-primary-subleg",
    )
    assert main_1.is_shared is True
    assert main_1.is_route_exclusive is False
    assert main_2.parent_balancing_point_id == main_1.balancing_point_id
    assert main_2.downstream_route_ids == ("leg-002-primary-subleg",)
    assert main_2.is_route_exclusive is True

    leg_1 = _point(projection, leg_balancing_point_id_v1("leg-001"))
    assert leg_1.parent_balancing_point_id == main_1.balancing_point_id
    assert leg_1.anchor_section_id == "leg-001-entry-section-001"
    assert leg_1.downstream_route_ids == (
        "leg-001-primary-subleg",
        "leg-001-subleg-b",
        "leg-001-subleg-c",
    )
    assert leg_1.is_shared is True

    primary = _point(
        projection,
        subleg_balancing_point_id_v1("leg-001-primary-subleg"),
    )
    branch = _point(
        projection,
        subleg_balancing_point_id_v1("leg-001-subleg-b"),
    )
    leaf = _point(
        projection,
        subleg_balancing_point_id_v1("leg-001-subleg-c"),
    )
    assert primary.parent_balancing_point_id == leg_1.balancing_point_id
    assert primary.point_role == "common"
    assert primary.downstream_route_ids == (
        "leg-001-primary-subleg",
        "leg-001-subleg-b",
        "leg-001-subleg-c",
    )
    assert branch.parent_balancing_point_id == primary.balancing_point_id
    assert branch.origin_room_id == "room-002"
    assert branch.downstream_route_ids == (
        "leg-001-subleg-b",
        "leg-001-subleg-c",
    )
    assert leaf.parent_balancing_point_id == branch.balancing_point_id
    assert leaf.anchor_section_id == "leg-001-subleg-c-section-001"
    assert leaf.is_shared is False
    assert leaf.is_route_exclusive is True

    invalid = SimpleNamespace(
        hydronic_topology=HydronicTopologyV1(
            heat_source_room_id="boiler-room",
            legs=[
                HydronicLegV1(
                    leg_id="leg-bad",
                    label="Bad Leg",
                    sublegs=[
                        _subleg(
                            "leg-bad-primary-subleg",
                            "Bad primary",
                            ["room-a"],
                            children=[
                                _subleg(
                                    "leg-bad-subleg-b",
                                    "Bad branch",
                                    ["room-b"],
                                    origin="missing-parent-room",
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    )
    blocked = build_balancing_point_topology_authority_v1(invalid)
    assert blocked.ready is False
    assert blocked.points == ()
    assert any("origin_room_id" in blocker for blocker in blocked.blockers)

    print("OK — H-S44-A main / leg / subleg balancing-point topology authority passed.")


if __name__ == "__main__":
    main()
