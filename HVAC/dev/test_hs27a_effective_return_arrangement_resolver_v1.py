from dataclasses import dataclass, field

from HVAC.hydronics.proportioning.effective_return_arrangement_resolver_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    resolve_effective_return_arrangements_v1,
)


@dataclass
class FakeSubleg:
    subleg_id: str
    label: str
    sublegs: list = field(default_factory=list)


@dataclass
class FakeLeg:
    leg_id: str
    label: str
    sublegs: list[FakeSubleg]


@dataclass
class FakeTopology:
    legs: list[FakeLeg]


@dataclass
class FakeProjectState:
    hydronic_topology: FakeTopology
    hydronic_return_arrangement_intent: dict


def row_by_scope_and_id(resolution, scope, item_id):
    for row in resolution.rows:
        if row.scope == scope and (
                row.leg_id == item_id
                or row.subleg_id == item_id
        ):
            return row

    raise AssertionError(f"Missing row {scope} {item_id}")


def main():
    topology = FakeTopology(
        legs=[
            FakeLeg(
                leg_id="leg-001",
                label="Heating Leg 1",
                sublegs=[
                    FakeSubleg(
                        subleg_id="leg-001-primary-subleg",
                        label="Leg 1A Common subleg",
                    ),
                    FakeSubleg(
                        subleg_id="leg-001-subleg-b",
                        label="Leg 1B Branch subleg",
                    ),
                ],
            ),
            FakeLeg(
                leg_id="leg-002",
                label="Heating Leg 2",
                sublegs=[
                    FakeSubleg(
                        subleg_id="leg-002-primary-subleg",
                        label="Leg 2A Common subleg",
                    ),
                    FakeSubleg(
                        subleg_id="leg-002-subleg-b",
                        label="Leg 2B Branch subleg",
                    ),
                ],
            ),
        ]
    )

    intent = {
        "schema": "return_arrangement_intent_v1",
        "system_arrangement": "REVERSE_RETURN",
        "leg_arrangements": {
            "leg-001": "DIRECT_RETURN",
        },
        "subleg_arrangements": {
            "leg-002-subleg-b": "DIRECT_RETURN",
        },
    }

    project = FakeProjectState(
        hydronic_topology=topology,
        hydronic_return_arrangement_intent=intent,
    )

    resolution = resolve_effective_return_arrangements_v1(project)

    assert resolution.schema == "effective_return_arrangement_resolution_v1"
    assert resolution.complete is True
    assert resolution.system_basis == REVERSE_RETURN

    leg_1 = row_by_scope_and_id(resolution, "LEG", "leg-001")
    assert leg_1.effective_basis == DIRECT_RETURN
    assert leg_1.source == "leg override"

    leg_2 = row_by_scope_and_id(resolution, "LEG", "leg-002")
    assert leg_2.effective_basis == REVERSE_RETURN
    assert leg_2.source == "inherit system"

    subleg_1a = row_by_scope_and_id(
        resolution,
        "COMMON_SUBLEG",
        "leg-001-primary-subleg",
    )
    assert subleg_1a.effective_basis == DIRECT_RETURN
    assert subleg_1a.source == "inherit leg"

    subleg_1b = row_by_scope_and_id(
        resolution,
        "BRANCH_SUBLEG",
        "leg-001-subleg-b",
    )
    assert subleg_1b.effective_basis == DIRECT_RETURN
    assert subleg_1b.source == "inherit parent subleg"
    assert subleg_1b.parent_subleg_id == "leg-001-primary-subleg"

    subleg_2a = row_by_scope_and_id(
        resolution,
        "COMMON_SUBLEG",
        "leg-002-primary-subleg",
    )
    assert subleg_2a.effective_basis == REVERSE_RETURN
    assert subleg_2a.source == "inherit leg"

    subleg_2b = row_by_scope_and_id(
        resolution,
        "BRANCH_SUBLEG",
        "leg-002-subleg-b",
    )
    assert subleg_2b.effective_basis == DIRECT_RETURN
    assert subleg_2b.source == "subleg override"

    print("OK — H-S27-A effective return arrangement resolver passed.")


if __name__ == "__main__":
    main()
