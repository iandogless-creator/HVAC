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

    assert adapter._build_clean_proportioned_route_status_v1(
        burden_row={
            "required_added_dp": "0.0 Pa",
            "status": "Preview only — chosen-basis controlling route",
        },
        authority_label="No valve authority required",
        authority_status="No valve authority preview required",
    ) == "Controlling route — no added Δp; no authority required"

    assert adapter._build_clean_proportioned_route_status_v1(
        burden_row={
            "required_added_dp": "6687.2 Pa",
            "status": "Preview only — below controlling route",
        },
        authority_label="Too low authority preview",
        authority_status="Warning — valve authority below preview minimum",
    ) == "Added Δp preview — low authority warning"

    assert adapter._build_clean_proportioned_route_status_v1(
        burden_row={
            "required_added_dp": "15825.0 Pa",
            "status": "Preview only — below controlling route",
        },
        authority_label="Acceptable authority preview",
        authority_status="Ready — acceptable authority preview",
    ) == "Added Δp preview — authority acceptable"

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
        provisional_burden_rows=[
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
        ],
        valve_authority_preview=preview,
    )

    assert rows[0]["status"] == (
        "Controlling route — no added Δp; no authority required"
    )
    assert rows[1]["status"] == (
        "Added Δp preview — low authority warning"
    )
    assert rows[2]["status"] == (
        "Added Δp preview — authority acceptable"
    )

    for row in rows:
        assert " | " not in row["status"]
        assert "no balancing valve selected" not in row["status"]

    source = inspect.getsource(HydronicsSchematicPanelAdapter)

    assert "_build_clean_proportioned_route_status_v1" in source
    assert "_build_clean_proportioned_route_output_rows_v1" in source
    assert "clean_status" in source

    print("OK — H-S33-F clean route status wording passed.")


if __name__ == "__main__":
    main()
