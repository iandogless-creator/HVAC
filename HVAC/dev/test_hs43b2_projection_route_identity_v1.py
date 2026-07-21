from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

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
    projection = SimpleNamespace(
        sections_projection=SimpleNamespace(
            leg_id="leg-002",
            subleg_id="leg-002-subleg-b",
        )
    )

    # Reproduces the live fault: sizing result carries no route identity.
    leg_id, subleg_id = adapter._received_basic_ps_route_identity_v1(
        SimpleNamespace(),
        projection,
    )
    assert leg_id == "leg-002"
    assert subleg_id == "leg-002-subleg-b"

    # Explicit result identity remains compatible and wins when supplied.
    explicit = SimpleNamespace(
        leg_id="leg-explicit",
        subleg_id="subleg-explicit",
    )
    assert adapter._received_basic_ps_route_identity_v1(
        explicit,
        projection,
    ) == ("leg-explicit", "subleg-explicit")

    received_rows = [
        {
            "leg_id": leg_id,
            "subleg_id": subleg_id,
            "route_id": subleg_id,
            "route": "Heating Leg 2 / Leg 2B Branch subleg",
            "flow_kg_s": "0.08370 kg/s",
        },
        {
            "leg_id": leg_id,
            "subleg_id": subleg_id,
            "route_id": subleg_id,
            "route": "Heating Leg 2 / Leg 2B Branch subleg",
            "flow_kg_s": "0.05980 kg/s",
        },
    ]
    flow_basis = adapter._build_received_basic_ps_route_flow_basis_v1(
        received_rows
    )
    assert flow_basis.ready is True
    assert len(flow_basis.rows) == 1
    assert flow_basis.rows[0].route_id == "leg-002-subleg-b"
    assert flow_basis.rows[0].flow_kg_s == "0.08370 kg/s"

    chosen = [
        _Chosen(
            route_id="leg-002:leg-002-subleg-b",
            route="Leg 2B Branch subleg",
            chosen_dp_pa=15327.6,
            is_controlling=False,
            dp_below_controlling_pa=2138.3,
        )
    ]
    resistance = build_chosen_basis_balancing_resistance_basis_v1(
        chosen_controlling_rows=chosen,
        flow_basis=flow_basis,
    )
    assert resistance.ready is True
    assert resistance.rows[0].flow_kg_s == "0.08370 kg/s"
    assert resistance.rows[0].resistance_pa_per_kg_s2 != "—"

    print(
        "OK — H-S43-B2 projection-authoritative received route identity "
        "and live flow delivery passed."
    )


if __name__ == "__main__":
    main()
