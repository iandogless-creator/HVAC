from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "def _clean_proportioned_section_display_row_v1" in source
    assert "display_row = self._clean_proportioned_section_display_row_v1(row)" in source
    assert "Iter means Colebrook iteration count only" in source

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    haaland_display = panel._clean_proportioned_section_display_row_v1(
        {
            "route": "Leg 1B Branch subleg",
            "section": "1",
            "from": "Common main / leg entry",
            "to": "L1B-R01",
            "flow_kg_s": "0.0766 kg/s",
            "pipe_dn": "10 mm",
            "dp_per_m": "1490.9",
            "length": "6.00 m",
            "k": "4.90",
            "section_dp": "11277.8 Pa",
            "iter": "5",
            "status": (
                "Branch-aware carried-flow basis / Carried-flow basis ready / "
                "First-pass Haaland estimate"
            ),
        }
    )

    assert haaland_display["iter"] == "—"

    colebrook_display = panel._clean_proportioned_section_display_row_v1(
        {
            "route": "Leg 1B Branch subleg",
            "section": "1",
            "from": "Common main / leg entry",
            "to": "L1B-R01",
            "flow_kg_s": "0.0766 kg/s",
            "pipe_dn": "10 mm",
            "dp_per_m": "1490.9",
            "length": "6.00 m",
            "k": "4.90",
            "section_dp": "11277.8 Pa",
            "iter": "5",
            "status": "Colebrook friction solve converged",
        }
    )

    assert colebrook_display["iter"] == "5"

    print("OK — H-S33-M5A Iter final display guard passed.")


if __name__ == "__main__":
    main()
