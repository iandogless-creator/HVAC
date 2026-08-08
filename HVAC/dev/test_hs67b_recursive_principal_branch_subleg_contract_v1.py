from __future__ import annotations

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    BRANCH_SUBLEG_KIND,
    PRINCIPAL_SUBLEG_KIND,
    build_recursive_subleg_positions_v1,
)


def _subleg(
    subleg_id: str,
    *,
    origin: str,
    rooms: list[str],
    children: list[HydronicSublegV1] | None = None,
) -> HydronicSublegV1:
    return HydronicSublegV1(
        subleg_id=subleg_id,
        label=subleg_id,
        origin_room_id=origin,
        route_room_ids=rooms,
        index_room_id=rooms[-1] if rooms else None,
        sublegs=list(children or ()),
    )


def main() -> None:
    nested_leaf = _subleg(
        "branch-a-1", origin="room-branch-a", rooms=["room-nested"]
    )
    branch_a = _subleg(
        "branch-a",
        origin="room-principal-a",
        rooms=["room-branch-a"],
        children=[nested_leaf],
    )
    principal_a = _subleg(
        "principal-a",
        origin="common-main",
        rooms=["room-principal-a"],
        children=[branch_a],
    )
    principal_b = _subleg(
        "principal-b", origin="common-main", rooms=["room-principal-b"]
    )
    topology = HydronicTopologyV1(
        heat_source_room_id="room-boiler",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Leg 1",
                sublegs=[principal_a, principal_b],
            )
        ],
    )

    positions = build_recursive_subleg_positions_v1(topology)
    assert [row.subleg_id for row in positions] == [
        "principal-a", "branch-a", "branch-a-1", "principal-b"
    ]
    assert [row.kind for row in positions] == [
        PRINCIPAL_SUBLEG_KIND,
        BRANCH_SUBLEG_KIND,
        BRANCH_SUBLEG_KIND,
        PRINCIPAL_SUBLEG_KIND,
    ]
    assert [row.parent_subleg_id for row in positions] == [
        None, "principal-a", "branch-a", None
    ]
    assert [row.depth for row in positions] == [0, 1, 2, 0]
    assert positions[2].ancestor_subleg_ids == ("principal-a", "branch-a")
    assert [row.is_leaf for row in positions] == [False, False, True, True]

    assert principal_b.is_leaf
    principal_b.sublegs.append(
        _subleg(
            "branch-b",
            origin="room-principal-b",
            rooms=["room-branch-b"],
        )
    )
    assert not principal_b.is_leaf

    encoded = topology.to_dict()
    encoded_subleg = encoded["legs"][0]["sublegs"][0]
    assert "kind" not in encoded_subleg
    assert "is_leaf" not in encoded_subleg
    assert "parent_subleg_id" not in encoded_subleg

    restored = HydronicTopologyV1.from_dict(encoded)
    restored_positions = build_recursive_subleg_positions_v1(restored)
    assert [row.kind for row in restored_positions] == [
        PRINCIPAL_SUBLEG_KIND,
        BRANCH_SUBLEG_KIND,
        BRANCH_SUBLEG_KIND,
        PRINCIPAL_SUBLEG_KIND,
        BRANCH_SUBLEG_KIND,
    ]
    assert restored_positions[-1].is_leaf

    nested_leaf.sublegs.append(principal_a)
    try:
        build_recursive_subleg_positions_v1(topology)
    except ValueError as exc:
        assert "cycle" in str(exc).lower()
    else:
        raise AssertionError("Recursive subleg cycle must fail closed")
    finally:
        nested_leaf.sublegs.clear()

    print(
        "OK — H-S67-B canonical Leg → Principal → recursive Branch "
        "contract and derived leaf status passed."
    )


if __name__ == "__main__":
    main()
