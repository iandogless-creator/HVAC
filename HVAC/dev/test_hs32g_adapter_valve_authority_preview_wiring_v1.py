from __future__ import annotations

import inspect

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    ACCEPTABLE_AUTHORITY_PREVIEW,
    VALVE_AUTHORITY_NONE_REQUIRED,
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
                "route": "leg-001:primary-subleg",
                "controlling": "Yes",
                "required_added_dp": "0.0 Pa",
                "flow_kg_s": "0.0300",
                "resistance_pa_per_kg_s2": "0.0",
            },
            {
                "route": "leg-002:subleg-b",
                "controlling": "No",
                "required_added_dp": "2559.3 Pa",
                "flow_kg_s": "0.0227",
                "resistance_pa_per_kg_s2": "4965000.0",
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
                "route": "leg-002:subleg-b",
                "chosen_dp": "7654.1 Pa",
            },
        ],
    )

    assert preview.ready is True
    assert len(preview.rows) == 2

    none_row = preview.rows[0]
    authority_row = preview.rows[1]

    assert none_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED
    assert none_row.authority is None

    assert authority_row.ready is True
    assert authority_row.design_valve_dp_pa == 2559.3
    assert authority_row.controlled_circuit_dp_pa == 7654.1
    assert round(authority_row.authority or 0.0, 3) == 0.251
    assert authority_row.authority_band_id == ACCEPTABLE_AUTHORITY_PREVIEW

    source = inspect.getsource(HydronicsSchematicPanelAdapter)

    assert "build_valve_authority_preview_v1" in source
    assert "_build_valve_authority_preview_v1" in source
    assert "self._valve_authority_preview = (" in source
    assert "self._valve_authority_input_mapping_preview" in source

    print("OK — H-S32-G adapter valve authority preview wiring passed.")


if __name__ == "__main__":
    main()
