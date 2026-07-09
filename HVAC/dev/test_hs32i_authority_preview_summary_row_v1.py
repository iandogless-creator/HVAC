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

    assert adapter._build_valve_authority_preview_summary_status_v1(
        None
    ) == "Waiting for valve authority preview evidence"

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
            {
                "route": "Leg 1A Common subleg",
                "controlling": "No",
                "required_added_dp": "15825.0 Pa",
                "flow_kg_s": "0.1699",
                "resistance_pa_per_kg_s2": "294522.9",
            },
            {
                "route": "Leg 2A Common subleg",
                "controlling": "No",
                "required_added_dp": "19790.9 Pa",
                "flow_kg_s": "0.1794",
                "resistance_pa_per_kg_s2": "340963.7",
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
            {
                "route": "Leg 1A Common subleg",
                "chosen_dp": "12918.7 Pa",
            },
            {
                "route": "Leg 2A Common subleg",
                "chosen_dp": "8952.8 Pa",
            },
        ],
    )

    summary = adapter._build_valve_authority_preview_summary_status_v1(
        preview
    )

    assert summary.startswith("Ready with warnings")
    assert "3 calculated" in summary
    assert "2 acceptable" in summary
    assert "1 not required" in summary
    assert "1 low-authority warning" in summary

    source = inspect.getsource(HydronicsSchematicPanelAdapter)

    assert "_build_valve_authority_preview_summary_status_v1" in source
    assert "Valve authority preview" in source
    assert "_valve_authority_preview" in source

    print("OK — H-S32-I authority preview summary row passed.")


if __name__ == "__main__":
    main()
