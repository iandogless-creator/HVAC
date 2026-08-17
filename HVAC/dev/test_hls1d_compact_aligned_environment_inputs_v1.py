from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QFormLayout

from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = EnvironmentPanel()

    numeric_inputs = (
        panel._te_input,
        panel._ti_input,
        panel._height_input,
        panel._ach_input,
        panel._design_flow_temp_input,
        panel._design_return_temp_input,
        panel._basic_ps_max_velocity_input,
        panel._bare_pipe_pair_centre_spacing_input_v1,
    )
    assert all(editor.minimumWidth() == 125 for editor in numeric_inputs)
    assert all(editor.maximumWidth() == 125 for editor in numeric_inputs)

    assert panel._bare_pipe_emissivity_input.minimumWidth() == 235
    assert panel._bare_pipe_emissivity_input.maximumWidth() == 235
    assert panel._bare_pipe_pair_size_input_v1.minimumWidth() == 105
    assert panel._bare_pipe_pair_size_input_v1.maximumWidth() == 105
    assert panel._bare_pipe_pair_support_input_v1.minimumWidth() == 235
    assert panel._bare_pipe_pair_support_input_v1.maximumWidth() == 235

    expected_labels = {
        "External design temperature (°C)",
        "Default room height (m)",
        "Design flow temperature (°C)",
        "Universal bare-pipe emissivity (0–1)",
    }
    labels = {
        label.text(): label
        for label in panel.findChildren(QLabel)
        if label.text() in expected_labels
    }
    assert set(labels) == expected_labels
    assert all(label.minimumWidth() == 255 for label in labels.values())
    assert all(label.maximumWidth() == 255 for label in labels.values())

    forms = panel.findChildren(QFormLayout)
    assert len(forms) == 4
    assert all(
        form.fieldGrowthPolicy() == QFormLayout.FieldsStayAtSizeHint
        for form in forms
    )
    assert panel._internal_environmental_temperature_mode.text() == "Ti"
    assert not any(
        label.text() == "Internal temperature basis"
        for label in panel.findChildren(QLabel)
    )
    app.processEvents()
    print(
        "OK — HL-S1D Environment labels align and numeric/choice inputs "
        "remain purpose-sized."
    )


if __name__ == "__main__":
    main()
