from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


class _FakeItem:
    def __init__(self, value: str) -> None:
        self._value = value

    def text(self) -> str:
        return self._value


class _FakeRouteTable:
    def __init__(self) -> None:
        self._items = {
            (0, 0): _FakeItem("Leg 1A Common subleg"),
            (1, 0): _FakeItem("Leg 1B Branch subleg"),
            (2, 0): _FakeItem("Leg 2A Common subleg"),
            (3, 0): _FakeItem("Leg 2B Branch subleg"),
        }

    def rowCount(self) -> int:
        return 4

    def item(self, row: int, column: int):
        return self._items.get((row, column))


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _clean_proportioned_route_labels_from_output_table_v1" in source
    assert "def _clean_proportioned_route_token_from_text_v1" in source
    assert "def _infer_clean_proportioned_route_label_for_section_row_v1" in source
    assert "def _enrich_clean_proportioned_section_route_labels_v1" in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)
    panel._clean_proportioned_route_output_table = _FakeRouteTable()

    assert panel._clean_proportioned_route_token_from_text_v1(
        "R1 L1A-R01"
    ) == "1A"

    assert panel._clean_proportioned_route_token_from_text_v1(
        "Leg 2B Branch subleg"
    ) == "2B"

    row = {
        "route": "—",
        "section": "—",
        "from": "Boiler / Heat Source",
        "to": "R2 L1A-R02",
        "flow_kg_s": "—",
    }

    assert panel._infer_clean_proportioned_route_label_for_section_row_v1(
        row
    ) == "Leg 1A Common subleg"

    enriched = panel._enrich_clean_proportioned_section_route_labels_v1(
        [
            {
                "route": "—",
                "from": "Boiler / Heat Source",
                "to": "R1 L2B-R01",
            },
            {
                "route": "Leg 1B Branch subleg",
                "from": "Boiler / Heat Source",
                "to": "R1 L1B-R01",
            },
        ]
    )

    assert enriched[0]["route"] == "Leg 2B Branch subleg"
    assert enriched[1]["route"] == "Leg 1B Branch subleg"

    selected = panel._clean_proportioned_section_rows_for_view_v1(
        mode="Selected route only",
        route_label="Leg 2B Branch subleg",
        source_rows=enriched,
    )

    assert len(selected) == 1
    assert selected[0]["route"] == "Leg 2B Branch subleg"

    print("OK — H-S33-M1 focused section route inference passed.")


if __name__ == "__main__":
    main()
