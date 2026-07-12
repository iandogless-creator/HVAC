from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert '"Iter"' in panel_source
    assert '"iter"' in panel_source
    assert '"colebrook_iter"' in panel_source
    assert '"colebrook_iterations"' in panel_source
    assert '"iteration_count"' in panel_source
    assert '"friction_iterations"' in panel_source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    row = panel._normalise_clean_proportioned_section_source_row_v1(
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
            "colebrook_iter": "7",
            "Status": "Existing section evidence",
        }
    )

    assert row["iter"] == "7"

    row = panel._normalise_clean_proportioned_section_source_row_v1(
        {
            "Route": "Leg 1A Common subleg",
            "From": "Boiler / Heat Source",
            "To": "Kitchen",
            "iteration_count": 5,
        }
    )

    assert row["iter"] == "5"

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()

    if "_normalise_clean_proportioned_adapter_section_row_v1" in adapter_source:
        assert '"iter"' in adapter_source
        assert '"colebrook_iter"' in adapter_source
        assert '"friction_iterations"' in adapter_source

    print("OK — H-S33-M2 focused section Iter column passed.")


if __name__ == "__main__":
    main()
