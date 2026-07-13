from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def main() -> None:
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _clean_proportioned_iter_display_value_v1" in panel_source
    assert "Iter means Colebrook iteration count only" in panel_source
    assert '"colebrook" not in evidence_text' in panel_source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    haaland_row = panel._normalise_clean_proportioned_section_source_row_v1(
        {
            "Route": "Leg 1B Branch subleg",
            "From": "L1B-R01",
            "To": "L1B-R02",
            "colebrook_iter": "6",
            "Status": (
                "Branch-aware carried-flow basis / "
                "First-pass Haaland estimate"
            ),
        }
    )

    assert haaland_row["iter"] == "—"

    unknown_row = panel._normalise_clean_proportioned_section_source_row_v1(
        {
            "Route": "Leg 1B Branch subleg",
            "From": "L1B-R01",
            "To": "L1B-R02",
            "iteration_count": "5",
            "Status": "Existing section evidence",
        }
    )

    assert unknown_row["iter"] == "—"

    colebrook_row = panel._normalise_clean_proportioned_section_source_row_v1(
        {
            "Route": "Leg 1B Branch subleg",
            "From": "L1B-R01",
            "To": "L1B-R02",
            "colebrook_iter": "7",
            "Status": "Colebrook friction solve converged",
        }
    )

    assert colebrook_row["iter"] == "7"

    method_row = panel._normalise_clean_proportioned_section_source_row_v1(
        {
            "Route": "Leg 1B Branch subleg",
            "From": "L1B-R01",
            "To": "L1B-R02",
            "iteration_count": "4",
            "friction_method": "Colebrook",
        }
    )

    assert method_row["iter"] == "4"

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    if hasattr(
        adapter,
        "_normalise_clean_proportioned_adapter_section_row_v1",
    ):
        adapter_haaland = adapter._normalise_clean_proportioned_adapter_section_row_v1(
            {
                "Route": "Leg 1B Branch subleg",
                "From": "L1B-R01",
                "To": "L1B-R02",
                "colebrook_iter": "6",
                "Status": "First-pass Haaland estimate",
            }
        )

        assert adapter_haaland["iter"] == "—"

        adapter_colebrook = adapter._normalise_clean_proportioned_adapter_section_row_v1(
            {
                "Route": "Leg 1B Branch subleg",
                "From": "L1B-R01",
                "To": "L1B-R02",
                "colebrook_iter": "6",
                "Status": "Colebrook friction solve converged",
            }
        )

        assert adapter_colebrook["iter"] == "6"

    print("OK — H-S33-M5 Iter requires Colebrook evidence passed.")


if __name__ == "__main__":
    main()
