from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    ReturnArrangementIntentV1,
)

from HVAC.hydronics.proportioning.return_arrangement_basis_acceptance_summary_v1 import (
    build_return_arrangement_basis_acceptance_summary_v1,
)


ROUTE_SPECS = [
    ("leg-001", "leg-001-primary-subleg"),
    ("leg-001", "leg-001-subleg-b"),
]


def _print_rows(title, rows):
    print()
    print(title)
    print("=" * len(title))
    for row in rows:
        print(
            row.scope,
            row.target,
            row.effective_return_basis,
            row.acceptance_source,
            row.ready,
            row.status,
        )


def _subleg_rows(rows):
    return [row for row in rows if row.scope.lower() == "subleg"]


def _leg_rows(rows):
    return [row for row in rows if row.scope.lower() == "leg"]


def _system_rows(rows):
    return [row for row in rows if row.scope.lower() == "system"]


def test_default_undecided_blocks_return_basis_readiness():
    intent = ReturnArrangementIntentV1()

    rows = build_return_arrangement_basis_acceptance_summary_v1(
        intent=intent,
        route_specs=ROUTE_SPECS,
    )

    assert rows

    system_rows = _system_rows(rows)
    subleg_rows = _subleg_rows(rows)

    assert system_rows
    assert system_rows[0].effective_return_basis == UNDECIDED
    assert system_rows[0].ready is False

    assert subleg_rows
    assert all(row.effective_return_basis == UNDECIDED for row in subleg_rows)
    assert all(row.ready is False for row in subleg_rows)

    _print_rows("default undecided blocks return basis readiness", rows)


def test_user_accepts_system_direct_return_basis():
    intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
    )

    rows = build_return_arrangement_basis_acceptance_summary_v1(
        intent=intent,
        route_specs=ROUTE_SPECS,
    )

    subleg_rows = _subleg_rows(rows)

    assert subleg_rows
    assert all(row.effective_return_basis == DIRECT_RETURN for row in subleg_rows)
    assert all(row.ready is True for row in subleg_rows)

    _print_rows("user accepts system direct return basis", rows)


def test_user_accepts_system_reverse_return_basis():
    intent = ReturnArrangementIntentV1(
        system_arrangement=REVERSE_RETURN,
    )

    rows = build_return_arrangement_basis_acceptance_summary_v1(
        intent=intent,
        route_specs=ROUTE_SPECS,
    )

    subleg_rows = _subleg_rows(rows)

    assert subleg_rows
    assert all(row.effective_return_basis == REVERSE_RETURN for row in subleg_rows)
    assert all(row.ready is True for row in subleg_rows)

    _print_rows("user accepts system reverse return basis", rows)


def test_leg_override_becomes_effective_basis():
    intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
        leg_arrangements={
            "leg-001": REVERSE_RETURN,
        },
    )

    rows = build_return_arrangement_basis_acceptance_summary_v1(
        intent=intent,
        route_specs=ROUTE_SPECS,
    )

    leg_rows = _leg_rows(rows)
    subleg_rows = _subleg_rows(rows)

    assert leg_rows
    assert leg_rows[0].effective_return_basis == REVERSE_RETURN
    assert leg_rows[0].ready is True

    assert subleg_rows
    assert all(row.effective_return_basis == REVERSE_RETURN for row in subleg_rows)
    assert all(row.ready is True for row in subleg_rows)

    _print_rows("leg override becomes effective basis", rows)


def test_subleg_override_becomes_effective_basis():
    intent = ReturnArrangementIntentV1(
        system_arrangement=DIRECT_RETURN,
        leg_arrangements={
            "leg-001": REVERSE_RETURN,
        },
        subleg_arrangements={
            "leg-001-primary-subleg": DIRECT_RETURN,
        },
    )

    rows = build_return_arrangement_basis_acceptance_summary_v1(
        intent=intent,
        route_specs=ROUTE_SPECS,
    )

    primary_rows = [
        row
        for row in rows
        if row.scope.lower() == "subleg"
        and row.subleg_id == "leg-001-primary-subleg"
    ]

    assert primary_rows
    assert primary_rows[0].effective_return_basis == DIRECT_RETURN
    assert primary_rows[0].ready is True

    _print_rows("subleg override becomes effective basis", rows)


if __name__ == "__main__":
    test_default_undecided_blocks_return_basis_readiness()
    test_user_accepts_system_direct_return_basis()
    test_user_accepts_system_reverse_return_basis()
    test_leg_override_becomes_effective_basis()
    test_subleg_override_becomes_effective_basis()

    print()
    print("OK — H-S26-B return arrangement basis acceptance summary is ready.")
