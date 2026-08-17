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
        assert 'combo.setProperty("uvpControlRole", "contentSizedCombo")' in source
        assert "QComboBox.SizeAdjustPolicy.AdjustToContents" in source
        assert "#2e7d32" in source
        print(
            "OK — U-S5F1B green actions and compact U-Values selectors "
            "passed (source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1b", name="U-S5F1B")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    combos = panel.findChildren(QComboBox)
    assert combos
    for combo in combos:
        assert combo.property("uvpControlRole") == "contentSizedCombo"
        assert combo.sizeAdjustPolicy() == (
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        assert combo.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed

    style = panel.styleSheet().lower()
    assert "#2e7d32" in style
    assert "#3b9145" in style
    assert "#2f6f9f" not in style
    assert panel._declared_opening_toggle.property(
        "uvpButtonRole"
    ) == "sectionToggle"

    print(
        "OK — U-S5F1B positive actions use green, section controls remain "
        "light blue and U-Values selectors use compact widths."
    )


if __name__ == "__main__":
    main()
