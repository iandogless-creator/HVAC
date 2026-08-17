from __future__ import annotations

try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    QApplication = None

from HVAC.project.project_state import ProjectState


def main() -> None:
    if QApplication is None:
        from pathlib import Path

        source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        assert "selection-background-color: #e5a24f" in source
        assert "selection-color: #202020" in source
        assert "QAbstractSpinBox QLineEdit" in source
        print(
            "OK — U-S5F1E readable U-Values text selection passed "
            "(source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1e", name="U-S5F1E")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    style = panel.styleSheet().lower()
    assert "selection-background-color: #e5a24f" in style
    assert style.count("selection-color: #202020") >= 2
    assert "qabstractspinbox qlineedit" in style

    panel._declared_opening_u_value.lineEdit().selectAll()
    panel._u_spin.lineEdit().selectAll()
    assert panel._declared_opening_u_value.lineEdit().hasSelectedText()
    assert panel._u_spin.lineEdit().hasSelectedText()

    print(
        "OK — U-S5F1E selected input text uses the orange focus fill "
        "with dark readable lettering."
    )


if __name__ == "__main__":
    main()
