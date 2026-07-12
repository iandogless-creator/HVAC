from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _clean_proportioned_section_row_has_engineering_values_v1" in source
    assert "def _clean_proportioned_prefer_engineering_section_rows_v1" in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    endpoint_only = {
        "route": "Leg 1A Common subleg",
        "section": "—",
        "from": "Boiler / Heat Source",
        "to": "R1 L1A-R01",
        "flow_kg_s": "—",
        "pipe_dn": "—",
        "dp_per_m": "—",
        "length": "—",
        "k": "—",
        "section_dp": "—",
        "iter": "—",
        "status": "—",
    }

    engineering = {
        "route": "Leg 1A Common subleg",
        "section": "1",
        "from": "Common main / leg entry",
        "to": "L1A-R01",
        "flow_kg_s": "0.1699 kg/s",
        "pipe_dn": "22 mm",
        "dp_per_m": "222.4",
        "length": "5.00 m",
        "k": "3.80",
        "section_dp": "1668.6 Pa",
        "iter": "5",
        "status": "Branch-aware carried-flow basis",
    }

    assert not panel._clean_proportioned_section_row_has_engineering_values_v1(
        endpoint_only
    )
    assert panel._clean_proportioned_section_row_has_engineering_values_v1(
        engineering
    )

    filtered = panel._clean_proportioned_prefer_engineering_section_rows_v1(
        [
            endpoint_only,
            engineering,
        ]
    )

    assert filtered == [engineering]

    fallback = panel._clean_proportioned_prefer_engineering_section_rows_v1(
        [
            endpoint_only,
        ]
    )

    assert fallback == [endpoint_only]

    print("OK — H-S33-M3 focused section endpoint filtering passed.")


if __name__ == "__main__":
    main()
