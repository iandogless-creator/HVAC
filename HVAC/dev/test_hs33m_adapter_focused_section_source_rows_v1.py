from __future__ import annotations

import inspect

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


class _FakePanel:
    def __init__(self) -> None:
        self.rows = None

    def set_clean_proportioned_focused_section_source_rows_v1(
            self,
            rows: list[dict],
    ) -> None:
        self.rows = rows


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    source_objects = [
        {
            "snapshot": {
                "section_rows": [
                    {
                        "Route": "Leg 1A Common subleg",
                        "Order": "3",
                        "From": "Boiler / Heat Source",
                        "To": "Kitchen",
                        "Flow kg/s": "0.16990 kg/s",
                        "Pipe DN": "15",
                        "Δp/m": "245.0",
                        "Length": "4.2",
                        "K": "1.5",
                        "Section Δp": "1029.0 Pa",
                        "Status": "Existing adapter section evidence",
                    },
                    {
                        "route_label": "Leg 2B Branch subleg",
                        "section_id": "4",
                        "from_label": "Hall",
                        "to_label": "Bedroom",
                        "flow_kg_s": "0.08370 kg/s",
                        "status": "Existing adapter section evidence",
                    },
                ]
            }
        }
    ]

    rows = adapter._build_clean_proportioned_focused_section_source_rows_v1(
        source_objects=source_objects
    )

    assert len(rows) == 2

    assert rows[0]["route"] == "Leg 1A Common subleg"
    assert rows[0]["section"] == "3"
    assert rows[0]["from"] == "Boiler / Heat Source"
    assert rows[0]["to"] == "Kitchen"
    assert rows[0]["flow_kg_s"] == "0.16990 kg/s"
    assert rows[0]["pipe_dn"] == "15"
    assert rows[0]["dp_per_m"] == "245.0"
    assert rows[0]["length"] == "4.2"
    assert rows[0]["k"] == "1.5"
    assert rows[0]["section_dp"] == "1029.0 Pa"
    assert rows[0]["status"] == "Existing adapter section evidence"

    assert rows[1]["route"] == "Leg 2B Branch subleg"
    assert rows[1]["section"] == "4"
    assert rows[1]["from"] == "Hall"
    assert rows[1]["to"] == "Bedroom"
    assert rows[1]["flow_kg_s"] == "0.08370 kg/s"

    # Route-level rows without From/To must not be treated as pipe sections.
    non_section_rows = adapter._build_clean_proportioned_focused_section_source_rows_v1(
        source_objects=[
            [
                {
                    "route": "Leg 1A Common subleg",
                    "basis": "F+R",
                    "chosen_dp": "17928.4 Pa",
                }
            ]
        ]
    )

    assert non_section_rows == []

    panel = _FakePanel()
    adapter._panel = panel
    adapter._hs33m_section_source = source_objects

    pushed_rows = adapter._build_clean_proportioned_focused_section_source_rows_v1(
        source_objects=adapter._clean_proportioned_adapter_section_source_objects_v1()
    )

    assert pushed_rows == rows

    adapter._push_clean_proportioned_focused_section_source_rows_v1()

    assert panel.rows == rows

    source = inspect.getsource(HydronicsSchematicPanelAdapter)

    assert "_build_clean_proportioned_focused_section_source_rows_v1" in source
    assert "_push_clean_proportioned_focused_section_source_rows_v1" in source
    assert "set_clean_proportioned_focused_section_source_rows_v1" in source
    assert "self._push_clean_proportioned_focused_section_source_rows_v1()" in source

    print("OK — H-S33-M adapter focused section source rows passed.")


if __name__ == "__main__":
    main()
