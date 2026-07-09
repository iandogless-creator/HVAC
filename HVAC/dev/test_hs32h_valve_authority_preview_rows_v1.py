from __future__ import annotations

import inspect

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.valve_authority_input_mapping_v1 import (
    build_valve_authority_input_mapping_v1,
)


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    balancing_mapping = build_balancing_method_candidate_mapping_v1(
        [
            {
                "route": "Leg 1B Branch subleg",
                "controlling": "Yes",
                "required_added_dp": "0.0 Pa",
                "flow_kg_s": "0.0766",
                "resistance_pa_per_kg_s2": "0.0",
            },
            {
                "route": "Leg 2B Branch subleg",
                "controlling": "No",
                "required_added_dp": "6687.2 Pa",
                "flow_kg_s": "0.0837",
                "resistance_pa_per_kg_s2": "305223.3",
            },
        ]
    )

    input_mapping = build_valve_authority_input_mapping_v1(
        balancing_mapping
    )

    preview = adapter._build_valve_authority_preview_v1(
        valve_authority_input_mapping=input_mapping,
        route_pressure_rows=[
            {
                "route": "Leg 2B Branch subleg",
                "chosen_dp": "22056.5 Pa",
            },
        ],
    )

    rows = adapter._build_valve_authority_preview_rows_v1(preview)

    assert len(rows) == 2

    controlling = rows[0]
    authority = rows[1]

    assert controlling["route"] == "Leg 1B Branch subleg"
    assert controlling["authority_state"] == "No valve authority required"
    assert controlling["controlled_circuit_dp"] == "—"
    assert controlling["authority"] == "—"

    assert authority["route"] == "Leg 2B Branch subleg"
    assert authority["authority_state"] == "Too low authority preview"
    assert authority["design_valve_dp"] == "6687.2 Pa"
    assert authority["controlled_circuit_dp"] == "22056.5 Pa"
    assert authority["authority"] == "0.233"
    assert authority["ready"] == "Yes"
    assert authority["blockers"] == "—"

    waiting_rows = adapter._build_valve_authority_preview_rows_v1(None)

    assert len(waiting_rows) == 1
    assert waiting_rows[0]["authority_state"] == (
        "Waiting for authority preview"
    )

    source = inspect.getsource(HydronicsSchematicPanelAdapter)

    assert "_build_valve_authority_preview_rows_v1" in source
    assert "self._valve_authority_preview" in source
    assert "_build_valve_authority_preview_rows_v1(" in source

    print("OK — H-S32-H valve authority preview rows passed.")


if __name__ == "__main__":
    main()
