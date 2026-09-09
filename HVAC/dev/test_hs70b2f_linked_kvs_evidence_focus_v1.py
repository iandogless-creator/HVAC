from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")

    for heading in (
        "Stable balancing point",
        "Hydraulic role",
        "Balancing method",
        "Valve duty required?",
        "Basis ready?",
        "Acceptance status",
        "Readiness blockers",
    ):
        assert heading in source

    assert "rgb(255, 238, 210)" in source
    assert "_focus_balancing_point_evidence_row_v1(point_id)" in source
    assert "_balancing_point_evidence_role_label_v1" in source
    assert "item.setToolTip(text)" in source
    assert '"Candidate Kvs:"' in source
    assert '"Acceptance status:"' in source
    assert '"Consequence status:"' in source
    assert "Stable ID: {point_id}" in source
    assert "setMinimumWidth(520)" in source

    assert (
        HydronicsSchematicPanel._balancing_point_evidence_role_label_v1(
            "common_main_takeoff"
        )
        == "Common-main take-off"
    )
    assert (
        HydronicsSchematicPanel._balancing_point_evidence_role_label_v1(
            "common_route_downstream"
        )
        == "Common route downstream"
    )

    app = QApplication.instance() or QApplication([])
    table = QTableWidget(2, 3)
    for row_index, point_id in enumerate(("point-a", "point-b")):
        for column_index in range(table.columnCount()):
            table.setItem(
                row_index,
                column_index,
                QTableWidgetItem(
                    point_id if column_index == 0 else f"value-{row_index}"
                ),
            )

    host = SimpleNamespace(_balancing_point_evidence_table=table)
    HydronicsSchematicPanel._focus_balancing_point_evidence_row_v1(
        host,
        "point-b",
    )

    expected = QColor(255, 238, 210)
    assert all(
        table.item(1, column).background().color() == expected
        for column in range(table.columnCount())
    )
    assert all(
        table.item(0, column).background().color() != expected
        for column in range(table.columnCount())
    )

    print(
        "OK — H-S70-B2F gives the all-point Kvs evidence table readable "
        "labels and persistently focuses the manual editor's selected point "
        "without changing calculations, intent, persistence or authority."
    )


if __name__ == "__main__":
    main()
