from __future__ import annotations

import math
from dataclasses import dataclass

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.chosen_basis_controlling_route_preview_v1 import (
    build_chosen_basis_controlling_route_preview_v1,
)


@dataclass(frozen=True)
class _ChosenRoute:
    scope: str
    route_id: str
    route: str
    basis: str
    chosen_dp_pa: float
    source: str
    common_main_dp_pa: float
    leg_entry_dp_pa: float
    physical_main_entry_dp_pa: float


def main() -> None:
    # Route A has the smaller route-only burden (800 Pa versus 1300 Pa),
    # but its physical main/entry contribution makes its canonical chosen
    # total controlling. H-S43-A must consume that total without rebuilding it.
    route_a = _ChosenRoute(
        scope="Common",
        route_id="leg-001-primary-subleg",
        route="Leg 1A Common subleg",
        basis="F&R",
        chosen_dp_pa=1500.0,
        source="test",
        common_main_dp_pa=500.0,
        leg_entry_dp_pa=200.0,
        physical_main_entry_dp_pa=700.0,
    )
    route_b = _ChosenRoute(
        scope="Branch",
        route_id="leg-002-subleg-b",
        route="Leg 2B Branch subleg",
        basis="F+RR",
        chosen_dp_pa=1400.0,
        source="test",
        common_main_dp_pa=75.0,
        leg_entry_dp_pa=25.0,
        physical_main_entry_dp_pa=100.0,
    )

    preview = build_chosen_basis_controlling_route_preview_v1(
        [route_a, route_b]
    )
    assert len(preview) == 2

    a = next(row for row in preview if row.route_id == route_a.route_id)
    b = next(row for row in preview if row.route_id == route_b.route_id)

    assert a.is_controlling is True
    assert b.is_controlling is False
    assert a.chosen_dp_pa == 1500.0
    assert a.dp_below_controlling_pa == 0.0
    assert b.chosen_dp_pa == 1400.0
    assert b.dp_below_controlling_pa == 100.0

    assert a.common_main_dp_pa == 500.0
    assert a.leg_entry_dp_pa == 200.0
    assert a.physical_main_entry_dp_pa == 700.0
    assert b.physical_main_entry_dp_pa == 100.0
    assert math.isclose(
        (a.chosen_dp_pa or 0.0) - (b.chosen_dp_pa or 0.0),
        b.dp_below_controlling_pa or 0.0,
    )
    assert "includes physical main/entry evidence once" in a.status
    assert "mains-inclusive chosen totals" in b.status

    # The existing provisional burden mapper must preserve the evidence and
    # use the same shortfall. It remains preview-only and selects no valve.
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    burden = adapter._build_provisional_proportioning_burden_rows_v1(preview)
    burden_by_route = {row["route"]: row for row in burden}
    burden_a = burden_by_route[route_a.route]
    burden_b = burden_by_route[route_b.route]

    assert burden_a["controlling"] == "Yes"
    assert burden_a["required_added_dp"] == "0.0 Pa"
    assert burden_a["common_main_dp"] == "500.0 Pa"
    assert burden_a["leg_entry_dp"] == "200.0 Pa"
    assert burden_a["physical_main_entry_dp"] == "700.0 Pa"

    assert burden_b["controlling"] == "No"
    assert burden_b["required_added_dp"] == "100.0 Pa"
    assert burden_b["physical_main_entry_dp"] == "100.0 Pa"
    assert "no balancing valve selected" in burden_b["status"]

    print(
        "OK — H-S43-A mains-aware chosen controlling route and "
        "shortfall evidence passed."
    )


if __name__ == "__main__":
    main()
