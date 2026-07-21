from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    build_chosen_basis_balancing_resistance_basis_v1,
)


@dataclass(frozen=True)
class _Chosen:
    route_id: str
    route: str
    chosen_dp_pa: float
    is_controlling: bool
    dp_below_controlling_pa: float


def main() -> None:
    adapter = object.__new__(HydronicsSchematicPanelAdapter)
    received = [
        {
            "route_id": "leg-001-primary-subleg",
            "subleg_id": "leg-001-primary-subleg",
            "route": "Heating Leg 1 / Leg 1A Common subleg",
            "flow_kg_s": "0.16990 kg/s",
        },
        {
            "route_id": "leg-001-primary-subleg",
            "subleg_id": "leg-001-primary-subleg",
            "route": "Heating Leg 1 / Leg 1A Common subleg",
            "flow_kg_s": "0.14830 kg/s",
        },
        {
            "route_id": "leg-001-subleg-b",
            "subleg_id": "leg-001-subleg-b",
            "route": "Heating Leg 1 / Leg 1B Branch subleg",
            "flow_kg_s": "0.07660 kg/s",
        },
    ]

    flow_basis = adapter._build_received_basic_ps_route_flow_basis_v1(received)
    assert flow_basis.ready is True
    assert len(flow_basis.rows) == 2
    by_id = {row.route_id: row for row in flow_basis.rows}
    assert by_id["leg-001-primary-subleg"].flow_kg_s == "0.16990 kg/s"
    assert by_id["leg-001-primary-subleg"].sections == "2"

    chosen = [
        _Chosen(
            route_id="leg-001:leg-001-primary-subleg",
            route="Leg 1A Common subleg",
            chosen_dp_pa=15497.6,
            is_controlling=False,
            dp_below_controlling_pa=1968.3,
        ),
        _Chosen(
            route_id="leg-001:leg-001-subleg-b",
            route="Leg 1B Branch subleg",
            chosen_dp_pa=17465.9,
            is_controlling=True,
            dp_below_controlling_pa=0.0,
        ),
    ]
    resistance = build_chosen_basis_balancing_resistance_basis_v1(
        chosen_controlling_rows=chosen,
        flow_basis=flow_basis,
    )
    assert resistance.ready is True
    assert not resistance.blockers
    resistance_by_id = {row.route_id: row for row in resistance.rows}
    common = resistance_by_id["leg-001:leg-001-primary-subleg"]
    branch = resistance_by_id["leg-001:leg-001-subleg-b"]
    assert common.flow_kg_s == "0.16990 kg/s"
    assert common.resistance_pa_per_kg_s2 != "—"
    assert branch.flow_kg_s == "0.07660 kg/s"
    assert branch.resistance_pa_per_kg_s2 == "0.0 Pa/(kg/s)²"

    source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "_received_basic_ps_route_flow_basis_v1" in source
    assert "received_basic_ps_rows" in source

    print(
        "OK — H-S43-B1 stable received Basic PS route-flow delivery passed."
    )


if __name__ == "__main__":
    main()
