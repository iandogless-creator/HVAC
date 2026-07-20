from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.dev.test_hs40b_common_main_leg_entry_pipe_sizing_v1 import (
    COMMON_1_ID,
    COMMON_2_ID,
    ENTRY_1_ID,
    ENTRY_2_ID,
    _project,
)
from HVAC.gui_v3.adapters.local_k_panel_adapter import LocalKPanelAdapter
from HVAC.gui_v3.panels.local_k_panel import LocalKPanel
from HVAC.hydronics.local_losses.local_k_section_projection_v1 import (
    build_local_k_section_projection_v1,
)
from HVAC.hydronics.proportioning.common_main_leg_entry_pressure_authority_v1 import (
    build_common_main_leg_entry_pressure_authority_v1,
)


MAIN_IDS = (COMMON_1_ID, COMMON_2_ID, ENTRY_1_ID, ENTRY_2_ID)


class _Signal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self, *args) -> None:
        for callback in tuple(self.callbacks):
            callback(*args)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    project = _project()

    projection = build_local_k_section_projection_v1(project, leg_id="leg-001")
    rows_by_id = {row.section_id: row for row in projection.rows}
    for section_id in MAIN_IDS:
        assert section_id in rows_by_id

    assert rows_by_id[COMMON_1_ID].section_scope == "Common main"
    assert rows_by_id[COMMON_2_ID].section_scope == "Common main"
    assert rows_by_id[ENTRY_1_ID].section_scope == "Leg entry"
    assert rows_by_id[ENTRY_2_ID].section_scope == "Leg entry"
    assert any(row.section_scope == "Route section" for row in projection.rows)
    assert rows_by_id[COMMON_1_ID].pressure_gradient_Pa_per_m > 0.0

    context = SimpleNamespace(
        project_state=project,
        room_state_changed=_Signal(),
        project_changed=_Signal(),
        project_state_changed=_Signal(),
        hydronic_section_focus_requested=_Signal(),
    )
    panel = LocalKPanel()
    adapter = LocalKPanelAdapter(panel=panel, context=context)

    combo = panel._section_combo
    combo_rows = [combo.itemData(index) or {} for index in range(combo.count())]
    combo_ids = {str(row.get("section_id") or "") for row in combo_rows}
    assert set(MAIN_IDS).issubset(combo_ids)

    labels = [combo.itemText(index) for index in range(combo.count())]
    assert any(label.startswith("Common main |") for label in labels)
    assert any(label.startswith("Leg entry |") for label in labels)
    assert any(label.startswith("Route section |") for label in labels)

    adapter._on_local_k_changed(
        {
            "section_id": COMMON_1_ID,
            "bend_90_count": 3,
            "bend_45_count": 1,
            "tee_through_count": 2,
            "tee_branch_count": 1,
            "isolation_valve_count": 1,
            "trv_count": 0,
            "lockshield_count": 0,
            "misc_k": 0.35,
            "length_m": 8.5,
        }
    )
    intent = project.hydronic_local_k_intent
    assert intent is not None
    persisted = intent.sections[COMMON_1_ID]
    assert persisted.section_id == COMMON_1_ID
    assert persisted.length_m == 8.5
    assert persisted.bend_90_count == 3
    assert persisted.tee_branch_count == 1
    assert persisted.misc_k == 0.35

    pressure = build_common_main_leg_entry_pressure_authority_v1(project)
    pressure_by_id = {row.section_id: row for row in pressure.rows}
    main_row = pressure_by_id[COMMON_1_ID]
    assert main_row.length_m == 8.5
    assert main_row.k_total > 0.0
    assert main_row.section_total_pressure_drop_Pa is not None

    adapter.refresh()
    selected = combo.currentData() or {}
    assert selected.get("section_id") == COMMON_1_ID
    assert panel._length_m.value() == 8.5
    assert panel._bend_90.value() == 3

    panel.close()
    app.processEvents()
    print("OK — H-S42-B common-main / leg-entry Local K editor passed.")


if __name__ == "__main__":
    main()
