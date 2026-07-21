from __future__ import annotations

import math
from types import SimpleNamespace

from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    build_balancing_point_resistance_allocation_v1,
)
from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    build_balancing_point_topology_authority_v1,
    main_balancing_point_id_v1,
    subleg_balancing_point_id_v1,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    PreliminaryBalancingResistanceRowV1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)


def _subleg(subleg_id, label, rooms, *, origin="", children=None):
    return HydronicSublegV1(
        subleg_id=subleg_id,
        label=label,
        origin_room_id=origin,
        route_room_ids=list(rooms),
        index_room_id=rooms[-1],
        sublegs=list(children or []),
    )


def _topology_projection():
    leaf = _subleg(
        "leg-001-subleg-c", "Subleg 1C", ["room-005"], origin="room-003"
    )
    branch = _subleg(
        "leg-001-subleg-b",
        "Subleg 1B",
        ["room-003", "room-004"],
        origin="room-002",
        children=[leaf],
    )
    primary_1 = _subleg(
        "leg-001-primary-subleg",
        "Subleg 1A",
        ["room-001", "room-002"],
        children=[branch],
    )
    primary_2 = _subleg(
        "leg-002-primary-subleg", "Subleg 2A", ["room-006", "room-007"]
    )
    project = SimpleNamespace(
        hydronic_topology=HydronicTopologyV1(
            heat_source_room_id="boiler-room",
            legs=[
                HydronicLegV1(
                    leg_id="leg-001",
                    label="Heating Leg 1",
                    sublegs=[primary_1],
                ),
                HydronicLegV1(
                    leg_id="leg-002",
                    label="Heating Leg 2",
                    sublegs=[primary_2],
                ),
            ],
        )
    )
    projection = build_balancing_point_topology_authority_v1(project)
    assert projection.ready is True
    return projection


def _basis(requirements):
    flows = {
        "leg-001-primary-subleg": 0.20,
        "leg-001-subleg-b": 0.10,
        "leg-001-subleg-c": 0.05,
        "leg-002-primary-subleg": 0.08,
    }
    return PreliminaryBalancingResistanceBasisV1(
        ready=True,
        status="Mains-aware chosen-basis balancing resistance ready",
        rows=[
            PreliminaryBalancingResistanceRowV1(
                route_id=route_id,
                route_label=route_id,
                flow_kg_s=f"{flows[route_id]:.5f} kg/s",
                required_added_dp=f"{added_dp:.1f} Pa",
                resistance_pa_per_kg_s2=(
                    f"{added_dp / (flows[route_id] ** 2):.1f} Pa/(kg/s)²"
                ),
                controlling="Yes" if added_dp == 0.0 else "No",
            )
            for route_id, added_dp in requirements.items()
        ],
    )


def main() -> None:
    topology = _topology_projection()
    allocation = build_balancing_point_resistance_allocation_v1(
        topology=topology,
        resistance_basis=_basis(
            {
                "leg-001-primary-subleg": 0.0,
                "leg-001-subleg-b": 100.0,
                "leg-001-subleg-c": 150.0,
                "leg-002-primary-subleg": 50.0,
            }
        ),
    )
    assert allocation.ready is True
    assert allocation.blockers == ()
    assert all(row.conserved for row in allocation.route_conservation)

    by_point = {row.balancing_point_id: row for row in allocation.rows}
    main_1 = by_point[main_balancing_point_id_v1("leg-001")]
    main_2 = by_point[main_balancing_point_id_v1("leg-002")]
    branch = by_point[subleg_balancing_point_id_v1("leg-001-subleg-b")]
    leaf = by_point[subleg_balancing_point_id_v1("leg-001-subleg-c")]

    assert math.isclose(main_1.point_flow_kg_s or 0.0, 0.28)
    assert main_1.allocated_added_dp_pa == 0.0
    assert math.isclose(main_2.point_flow_kg_s or 0.0, 0.08)
    assert main_2.allocated_added_dp_pa == 50.0
    assert math.isclose(
        main_2.allocated_resistance_pa_per_kg_s2 or 0.0,
        50.0 / (0.08 ** 2),
    )

    assert branch.is_shared is True
    assert branch.allocated_added_dp_pa == 100.0
    assert math.isclose(
        branch.allocated_resistance_pa_per_kg_s2 or 0.0,
        100.0 / (0.10 ** 2),
    )
    assert leaf.is_route_exclusive is True
    assert leaf.allocated_added_dp_pa == 50.0

    conservation = {row.route_id: row for row in allocation.route_conservation}
    assert conservation["leg-001-primary-subleg"].allocated_path_dp_pa == 0.0
    assert conservation["leg-001-subleg-b"].allocated_path_dp_pa == 100.0
    assert conservation["leg-001-subleg-c"].allocated_path_dp_pa == 150.0
    assert conservation["leg-002-primary-subleg"].allocated_path_dp_pa == 50.0
    assert conservation["leg-001-subleg-c"].contributing_balancing_point_ids == (
        subleg_balancing_point_id_v1("leg-001-subleg-b"),
        subleg_balancing_point_id_v1("leg-001-subleg-c"),
    )

    # A parent route requiring more burden than its descendants cannot be
    # represented by entry points without overloading the child routes. Keep
    # this fail-closed regression on an explicit pre-A2 entry-only projection;
    # the authoritative A2 projection now contains a downstream-exclusive
    # common-route point which correctly makes this burden representable.
    legacy_entry_only_topology = type(topology)(
        ready=topology.ready,
        points=tuple(
            point for point in topology.points
            if point not in topology.route_exclusive_points
        ),
        main_points=topology.main_points,
        leg_points=topology.leg_points,
        subleg_points=topology.subleg_points,
        route_exclusive_points=(),
        blockers=topology.blockers,
        status=topology.status,
    )
    impossible = build_balancing_point_resistance_allocation_v1(
        topology=legacy_entry_only_topology,
        resistance_basis=_basis(
            {
                "leg-001-primary-subleg": 120.0,
                "leg-001-subleg-b": 20.0,
                "leg-001-subleg-c": 20.0,
                "leg-002-primary-subleg": 0.0,
            }
        ),
    )
    assert impossible.ready is False
    assert any("unallocated residual" in item for item in impossible.blockers)
    impossible_check = next(
        row
        for row in impossible.route_conservation
        if row.route_id == "leg-001-primary-subleg"
    )
    assert impossible_check.conserved is False
    assert impossible_check.difference_pa > 0.0

    missing = _basis(
        {
            "leg-001-primary-subleg": 0.0,
            "leg-001-subleg-b": 100.0,
            "leg-001-subleg-c": 150.0,
            "leg-002-primary-subleg": 50.0,
        }
    )
    missing.rows.pop()
    blocked = build_balancing_point_resistance_allocation_v1(
        topology=topology,
        resistance_basis=missing,
    )
    assert blocked.ready is False
    assert blocked.rows == ()
    assert any("missing for" in item for item in blocked.blockers)

    print(
        "OK — H-S44-B balancing-point provisional resistance allocation "
        "and no-double-counting evidence passed."
    )


if __name__ == "__main__":
    main()
