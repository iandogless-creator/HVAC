from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.hydronic_control_panel import HydronicControlPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app

    panel = HydronicControlPanel()

    # Ordinary controls remain purpose-sized rather than filling the panel.
    expected_widths = (
        (panel._room_combo, 260),
        (panel._emitter_combo, 420),
        (panel._emitter_type, 180),
        (panel._quantity, 90),
        (panel._design_output_W, 150),
        (panel._before_emitter_length_m, 120),
        (panel._after_emitter_length_m, 120),
        (panel._flow_temp_C, 140),
        (panel._return_temp_C, 140),
    )
    for editor, expected_width in expected_widths:
        assert editor.minimumWidth() == expected_width
        assert editor.maximumWidth() == expected_width

    # Legacy authority is preserved behind concise disclosure and hover help.
    assert panel._legacy_overrides_container.isHidden()
    help_text = panel._legacy_overrides_toggle.toolTip()
    assert help_text.count("\n") >= 2
    assert "Environment supplies" in help_text
    panel._legacy_overrides_toggle.setChecked(True)
    assert not panel._legacy_overrides_container.isHidden()
    assert panel._legacy_overrides_toggle.arrowType() == Qt.ArrowType.DownArrow

    # Existing stored override evidence automatically remains visible.
    panel._legacy_overrides_toggle.setChecked(False)
    panel.set_emitter_editor_values(
        emitter_type="radiator",
        design_output_W=800.0,
        flow_temp_C=75.0,
        return_temp_C=55.0,
    )
    assert not panel._legacy_overrides_container.isHidden()
    assert panel._flow_temp_C.value() == 75.0
    assert panel._return_temp_C.value() == 55.0

    # Purpose colours and concise labels do not alter enable-state authority.
    assert panel._add_btn.text() == "Add"
    assert panel._update_btn.text() == "Update"
    assert panel._remove_btn.text() == "Remove"
    assert "#d9ead3" in panel._add_btn.styleSheet().lower()
    assert "#dbe9f6" in panel._update_btn.styleSheet().lower()
    assert "#f4d7d7" in panel._remove_btn.styleSheet().lower()
    assert "\n" in panel._remove_btn.toolTip()

    panel.set_no_existing_emitter()
    assert panel._add_btn.isEnabled()
    assert not panel._update_btn.isEnabled()
    assert not panel._remove_btn.isEnabled()

    print(
        "OK — H-S69-A3 compacts Hydronic Emitters, keeps legacy "
        "temperature intent discoverable and gives Add/Update/Remove "
        "distinct purpose colours without changing authority."
    )


if __name__ == "__main__":
    main()
