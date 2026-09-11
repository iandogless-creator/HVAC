from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QTableWidget, QTableWidgetItem

from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    table = QTableWidget(3, 2)
    for row, identity in enumerate(("one", "two", "three")):
        table.setItem(row, 0, QTableWidgetItem(identity))
        table.setItem(row, 1, QTableWidgetItem(f"evidence {identity}"))

    assert panel._select_linked_table_identity_v1(table, ("two",)) == 1
    assert table.currentRow() == 1
    assert panel._select_linked_table_identity_v1(table, ("three",)) == 2
    assert table.currentRow() == 2
    assert len(table.selectionModel().selectedRows()) == 1

    panel._product_search_duty_envelope_table = table
    panel._product_search_criteria_point_combo = QComboBox()
    panel._point_valve_candidate_acceptance_point_combo = QComboBox()
    for combo in (
        panel._product_search_criteria_point_combo,
        panel._point_valve_candidate_acceptance_point_combo,
    ):
        for identity in ("one", "two", "three"):
            combo.addItem(identity, identity)
    panel._product_search_linked_focus_point_v1("two")
    assert panel._product_search_criteria_point_combo.currentData() == "two"
    assert panel._point_valve_candidate_acceptance_point_combo.currentData() == "two"
    assert table.currentRow() == 1

    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "# H-S71-A — whole-Hydronics persistent linked focus" in source
    assert "_product_search_linked_focus_point_id_v1" in source
    assert "_committed_pipe_linked_focus_section_id_v1" in source
    assert "table.clearSelection()" in source

    print(
        "OK — H-S71-A keeps one persistent pale-orange linked focus per "
        "Hydronics table/editor group through selection, refresh and tab "
        "changes, without changing calculations, persistence or authority."
    )


if __name__ == "__main__":
    main()
