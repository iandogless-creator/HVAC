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

    burden_rows = [
        {
            "route": "Leg 1B Branch subleg",
            "basis": "F+RR",
            "flow_kg_s": "0.0766",
            "chosen_dp": "28743.7 Pa",
            "required_added_dp": "0.0 Pa",
            "status": "Preview only — chosen-basis controlling route",
        },
        {
            "route": "Leg 2B Branch subleg",
            "basis": "F+RR",
            "flow_kg_s": "0.0837",
            "chosen_dp": "22056.5 Pa",
            "required_added_dp": "6687.2 Pa",
            "status": "Preview only — below controlling route",
        },
        {
            "route": "Leg 1A Common subleg",
            "basis": "F+RR",
            "flow_kg_s": "0.1699",
            "chosen_dp": "12918.7 Pa",
            "required_added_dp": "15825.0 Pa",
            "status": "Preview only — below controlling route",
        },
    ]

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
        ],
    )

    rows = adapter._build_clean_proportioned_route_output_rows_v1(
        provisional_burden_rows=burden_rows,
        valve_authority_preview=preview,
    )

    assert len(rows) == 3

    controlling = rows[0]
    low_authority = rows[1]
    acceptable = rows[2]

    assert controlling["route"] == "Leg 1B Branch subleg"
    assert controlling["basis"] == "F+RR"
    assert controlling["flow_kg_s"] == "0.0766"
    assert controlling["route_dp"] == "28743.7 Pa"
    assert controlling["added_dp"] == "0.0 Pa"
    assert controlling["authority"] == "—"
    assert "No valve authority required" in controlling["status"]

    assert low_authority["route"] == "Leg 2B Branch subleg"
    assert low_authority["route_dp"] == "22056.5 Pa"
    assert low_authority["added_dp"] == "6687.2 Pa"
    assert low_authority["authority"] == "0.233"
    assert "Too low authority preview" in low_authority["status"]

    assert acceptable["route"] == "Leg 1A Common subleg"
    assert acceptable["route_dp"] == "12918.7 Pa"
    assert acceptable["added_dp"] == "15825.0 Pa"
    assert acceptable["authority"] == "0.551"
    assert "Acceptable authority preview" in acceptable["status"]

    empty = adapter._build_clean_proportioned_route_output_rows_v1(
        provisional_burden_rows=[],
        valve_authority_preview=preview,
    )

    assert empty == []

    source = inspect.getsource(HydronicsSchematicPanelAdapter)

    assert "_build_clean_proportioned_route_output_rows_v1" in source
    assert "set_clean_proportioned_route_output_rows(" in source
    assert "_valve_authority_preview" in source

    print("OK — H-S33-D clean Proportioned route rows passed.")


if __name__ == "__main__":
    main()
