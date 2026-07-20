from __future__ import annotations

import math
from dataclasses import dataclass

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    PreliminaryBalancingResistanceRowV1,
    build_chosen_basis_balancing_resistance_basis_v1,
)


@dataclass(frozen=True)
class _Chosen:
    route_id: str
    route: str
    basis: str
    chosen_dp_pa: float
    is_controlling: bool
    dp_below_controlling_pa: float
    common_main_dp_pa: float
    leg_entry_dp_pa: float
    physical_main_entry_dp_pa: float


def _legacy_flow_basis() -> PreliminaryBalancingResistanceBasisV1:
    # The legacy Δp and R values are deliberately wrong. H-S43-B may consume
    # these rows for route flow only and must recalculate from chosen shortfall.
    return PreliminaryBalancingResistanceBasisV1(
        ready=True,
        rows=[
            PreliminaryBalancingResistanceRowV1(
                route_id="route-a",
                route_label="Route A",
                sections="3",
                flow_kg_s="0.20000 kg/s",
                required_added_dp="999.0 Pa",
                resistance_pa_per_kg_s2="999999.0 Pa/(kg/s)²",
            ),
            PreliminaryBalancingResistanceRowV1(
                route_id="route-b",
                route_label="Route B",
                sections="4",
                flow_kg_s="0.10000 kg/s",
                required_added_dp="888.0 Pa",
                resistance_pa_per_kg_s2="888888.0 Pa/(kg/s)²",
            ),
        ],
    )


def main() -> None:
    chosen = [
        _Chosen(
            route_id="route-a",
            route="Route A",
            basis="F&R",
            chosen_dp_pa=1500.0,
            is_controlling=True,
            dp_below_controlling_pa=0.0,
            common_main_dp_pa=500.0,
            leg_entry_dp_pa=200.0,
            physical_main_entry_dp_pa=700.0,
        ),
        _Chosen(
            route_id="route-b",
            route="Route B",
            basis="F+RR",
            chosen_dp_pa=1400.0,
            is_controlling=False,
            dp_below_controlling_pa=100.0,
            common_main_dp_pa=75.0,
            leg_entry_dp_pa=25.0,
            physical_main_entry_dp_pa=100.0,
        ),
    ]

    basis = build_chosen_basis_balancing_resistance_basis_v1(
        chosen_controlling_rows=chosen,
        flow_basis=_legacy_flow_basis(),
    )
    assert basis.ready is True
    assert not basis.blockers
    by_id = {row.route_id: row for row in basis.rows}
    route_a = by_id["route-a"]
    route_b = by_id["route-b"]

    assert route_a.required_added_dp == "0.0 Pa"
    assert route_a.resistance_pa_per_kg_s2 == "0.0 Pa/(kg/s)²"
    assert route_a.controlling == "Yes"

    expected_b = 100.0 / (0.1 ** 2)
    assert route_b.required_added_dp == "100.0 Pa"
    assert route_b.flow_kg_s == "0.10000 kg/s"
    assert route_b.resistance_pa_per_kg_s2 == "10000.0 Pa/(kg/s)²"
    assert math.isclose(expected_b, 10000.0)
    assert "888888" not in route_b.resistance_pa_per_kg_s2

    # Existing adapter composition must now expose the recalculated resistance
    # while retaining H-S43-A main/entry evidence without summing it again.
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    burden = adapter._build_provisional_proportioning_burden_rows_v1(
        chosen,
        resistance_basis=basis,
    )
    burden_by_route = {row["route"]: row for row in burden}
    assert burden_by_route["Route A"]["resistance_pa_per_kg_s2"].startswith(
        "0.0"
    )
    assert burden_by_route["Route B"]["required_added_dp"] == "100.0 Pa"
    assert burden_by_route["Route B"]["resistance_pa_per_kg_s2"].startswith(
        "10000.0"
    )
    assert burden_by_route["Route B"]["physical_main_entry_dp"] == "100.0 Pa"

    # Positive shortfall with no positive flow fails closed.
    missing_flow = build_chosen_basis_balancing_resistance_basis_v1(
        chosen_controlling_rows=[chosen[1]],
        flow_basis=PreliminaryBalancingResistanceBasisV1(ready=False),
    )
    assert missing_flow.ready is False
    assert missing_flow.blockers
    assert missing_flow.rows[0].resistance_pa_per_kg_s2 == "—"

    print(
        "OK — H-S43-B mains-aware provisional balancing resistance "
        "consumption passed."
    )


if __name__ == "__main__":
    main()
