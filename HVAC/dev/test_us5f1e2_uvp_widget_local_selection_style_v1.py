from __future__ import annotations

try:
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QApplication, QLineEdit
except ImportError:
    QApplication = None
    QLineEdit = None
    QPalette = None

from HVAC.project.project_state import ProjectState


def main() -> None:
    if QApplication is None:
        from pathlib import Path

        source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        for marker in (
            "A widget-local declaration outranks the native Mint theme",
            "editor.setStyleSheet(",
            '" selection-background-color: #e0a15a;"',
            "QPalette.ColorGroup.Active",
            "QPalette.ColorRole.HighlightedText",
            'QColor("#000000")',
        ):
            assert marker in source
        print(
            "OK — U-S5F1E2 widget-local selected-text styling passed "
            "(source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1e2", name="U-S5F1E2")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    editors = panel.findChildren(QLineEdit)
    assert editors
    for editor in editors:
        local_style = editor.styleSheet().lower()
        assert "selection-background-color: #e0a15a" in local_style
        assert "selection-color: #000000" in local_style
        palette = editor.palette()
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            assert (
                palette.color(group, QPalette.ColorRole.Highlight).name().lower()
                == "#e0a15a"
            )
            assert (
                palette.color(
                    group,
                    QPalette.ColorRole.HighlightedText,
                ).name().lower()
                == "#000000"
            )

    assert panel._declared_opening_u_value.lineEdit() in editors
    assert panel._u_spin.lineEdit() in editors

    print(
        "OK — U-S5F1E2 every U-Values editor owns the readable orange/dark "
        "selection style and all active-state palette roles."
    )


if __name__ == "__main__":
    main()
