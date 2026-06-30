from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.proportioning.chosen_basis_route_pressure_preview_v1 import (
    build_chosen_basis_route_pressure_preview_v1,
)


@dataclass(frozen=True)
class ResolvedBasisRow:
    scope: str
    target_id: str
    target: str
    effective_basis: str
    source: str


@dataclass(frozen=True)
class ReturnComparisonRow:
    route_id: str
    route: str
    room: str
    direct_route_dp_pa: float
    reverse_route_dp_pa: float


def main() -> None:
    resolved_rows = [
        ResolvedBasisRow(
            scope="Common",
            target_id="leg-001-primary-subleg",
            target="Heating Leg 1 / Common subleg",
            effective_basis="DIRECT_RETURN",
            source="system",
        ),
        ResolvedBasisRow(
            scope="Branch",
            target_id="leg-001-subleg-b",
            target="Heating Leg 1 / Branch B",
            effective_basis="REVERSE_RETURN",
            source="subleg override",
        ),
        ResolvedBasisRow(
            scope="Branch",
            target_id="leg-002-subleg-b",
            target="Heating Leg 2 / Branch B",
            effective_basis="DIRECT_RETURN",
            source="leg override",
        ),
    ]

    comparison_rows = [
        # Common route has two room rows.
        # Backend must use max direct and max reverse evidence for the route.
        ReturnComparisonRow(
            route_id="leg-001-primary-subleg",
            route="Heating Leg 1 / Common subleg",
            room="Hall",
            direct_route_dp_pa=1000.0,
            reverse_route_dp_pa=1300.0,
        ),
        ReturnComparisonRow(
            route_id="leg-001-primary-subleg",
            route="Heating Leg 1 / Common subleg",
            room="Kitchen",
            direct_route_dp_pa=1150.0,
            reverse_route_dp_pa=1250.0,
        ),

        # Branch route selected as reverse return.
        ReturnComparisonRow(
            route_id="leg-001-subleg-b",
            route="Heating Leg 1 / Branch B",
            room="Bedroom 1",
            direct_route_dp_pa=2400.0,
            reverse_route_dp_pa=1800.0,
        ),
        ReturnComparisonRow(
            route_id="leg-001-subleg-b",
            route="Heating Leg 1 / Branch B",
            room="Bathroom",
            direct_route_dp_pa=2200.0,
            reverse_route_dp_pa=1900.0,
        ),

        # Direct basis is accepted here, but alternative reverse is lower.
        ReturnComparisonRow(
            route_id="leg-002-subleg-b",
            route="Heating Leg 2 / Branch B",
            room="Bedroom 2",
            direct_route_dp_pa=1500.0,
            reverse_route_dp_pa=1200.0,
        ),
    ]

    rows = build_chosen_basis_route_pressure_preview_v1(
        resolved_basis_rows=resolved_rows,
        return_comparison_rows=comparison_rows,
    )

    assert len(rows) == 3

    common = rows[0]
    assert common.scope == "Common"
    assert common.route_id == "leg-001-primary-subleg"
    assert common.basis == "F&R"
    assert common.chosen_dp_pa == 1150.0
    assert common.alternative_dp_pa == 1300.0
    assert common.difference_pa == -150.0
    assert common.source == "system"
    assert "lower" in common.status

    branch_rr = rows[1]
    assert branch_rr.scope == "Branch"
    assert branch_rr.route_id == "leg-001-subleg-b"
    assert branch_rr.basis == "F+RR"
    assert branch_rr.chosen_dp_pa == 1900.0
    assert branch_rr.alternative_dp_pa == 2400.0
    assert branch_rr.difference_pa == -500.0
    assert branch_rr.source == "subleg override"
    assert "lower" in branch_rr.status

    branch_direct_higher = rows[2]
    assert branch_direct_higher.scope == "Branch"
    assert branch_direct_higher.route_id == "leg-002-subleg-b"
    assert branch_direct_higher.basis == "F&R"
    assert branch_direct_higher.chosen_dp_pa == 1500.0
    assert branch_direct_higher.alternative_dp_pa == 1200.0
    assert branch_direct_higher.difference_pa == 300.0
    assert branch_direct_higher.source == "leg override"
    assert "higher" in branch_direct_higher.status

    print("OK — H-S27-C chosen-basis route Δp preview passed.")


if __name__ == "__main__":
    main()