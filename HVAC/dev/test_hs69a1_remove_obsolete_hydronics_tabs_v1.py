from __future__ import annotations

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()

    tab_names = [
        panel._tabs.tabText(index)
        for index in range(panel._tabs.count())
    ]

    assert tab_names == [
        "Proportioning",
        "Proportioning Data",
        "Proportioned",
        "Pipe Resizing",
    ]

    from pathlib import Path

    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")

    assert 'self._make_tab("Basic Overview")' not in panel_source
    assert 'self._make_tab("Authority")' not in panel_source
    assert "class _IndexRouteStripWidget" not in panel_source

    for obsolete_call in (
        "set_emitter_demand_rows(",
        "set_hydronic_skeleton_rows(",
        "set_pipe_run_intent_rows(",
        "set_pipe_authority_summary_rows(",
        "set_leg_subleg_topology_rows(",
        "set_index_route_accumulator_rows(",
        "set_pipe_size_suggestion_rows(",
        "set_index_route_trace(",
        "set_basic_hydronics_worksheet_rows(",
        "._set_schematic(",
    ):
        assert obsolete_call not in adapter_source

    panel.close()
    app.processEvents()

    print(
        "OK — H-S69-A1 removes obsolete Basic Overview and Authority "
        "runtime projections while retaining downstream Hydronics tabs."
    )


if __name__ == "__main__":
    main()
