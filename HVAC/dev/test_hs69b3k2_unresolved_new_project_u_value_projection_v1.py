from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters import heat_loss_panel_adapter as adapter_module
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3


def _fabric_row(*, u_value_W_m2K):
    return SimpleNamespace(
        surface_id="room-001-wall-1",
        element_id="room-001-wall-1",
        segment_id="room-001-wall-1",
        element="External Wall",
        surface_class="external_wall",
        area_m2=12.0,
        u_value_W_m2K=u_value_W_m2K,
        delta_t_K=24.0,
        construction_id="UNRESOLVED-WALL",
        geometry_ref="wall",
        boundary_kind="EXTERNAL",
        adjacent_room_id=None,
        _segment=None,
    )


def main() -> None:
    adapter = object.__new__(HeatLossPanelAdapter)

    unresolved = _fabric_row(u_value_W_m2K=None)
    assert adapter._compute_qf(unresolved) is None

    resolved = _fabric_row(u_value_W_m2K=0.25)
    assert adapter._compute_qf(resolved) == 72.0

    original_builder = adapter_module.build_room_fabric_rows_with_openings_v1
    adapter_module.build_room_fabric_rows_with_openings_v1 = (
        lambda _project, _room: [unresolved]
    )
    try:
        rows, metas = adapter._build_topology_rows_with_meta(
            SimpleNamespace(rooms={}),
            SimpleNamespace(room_id="room-001"),
        )
    finally:
        adapter_module.build_room_fabric_rows_with_openings_v1 = original_builder

    assert len(rows) == 1
    assert len(metas) == 1
    assert rows[0]["A"] == 12.0
    assert rows[0]["U"] is None
    assert rows[0]["dT"] == 24.0
    assert rows[0]["Qf"] is None

    app = QApplication.instance() or QApplication([])
    panel = HeatLossPanelV3()
    panel.set_rows(rows, metas)
    assert panel._table.item(0, 2).text() == "—"
    assert panel._table.item(0, 4).text() == "—"
    panel.close()
    app.processEvents()

    source = Path(
        "HVAC/gui_v3/adapters/heat_loss_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert '"U": float(src.u_value_W_m2K)' not in source
    assert "u_value is None" in source
    assert "ProjectState" not in source[source.index(
        "    def _compute_qf"
    ):source.index("    def _format_element")]

    print(
        "OK — H-S69-B3K2 preserves unresolved New Project U-value and Qf "
        "evidence as em dashes without inventing defaults, mutating "
        "ProjectState or changing Heat-Loss authority."
    )


if __name__ == "__main__":
    main()
