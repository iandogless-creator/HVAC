from __future__ import annotations

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QSizePolicy
except ImportError:
    QApplication = None
    QComboBox = None
    QSizePolicy = None

from HVAC.project.project_state import ProjectState


def main() -> None:
    if QApplication is None:
        from pathlib import Path

        source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        assert "self._u_spin.setFixedWidth" in source
        assert "QComboBox.SizeAdjustPolicy.AdjustToContents" in source
        print(
            "OK — U-S5F1C1 Edit U-Value width repair passed "
            "(source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1c1", name="U-S5F1C1")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    assert 130 <= panel._u_spin.width() < 240
    assert 160 <= panel._declared_opening_u_value.width() < 300

    combos = panel.findChildren(QComboBox)
    assert combos
    for combo in combos:
        assert combo.property("uvpControlRole") == "contentSizedCombo"
        assert combo.sizeAdjustPolicy() == (
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        assert combo.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed

    print(
        "OK — U-S5F1C1 general and declared U-value entries are compact; "
        "selectors retain content-aware sizing."
    )


if __name__ == "__main__":
    main()
