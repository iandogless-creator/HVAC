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
            "from PySide6.QtGui import QColor, QPalette",
            "for editor in self.findChildren(QLineEdit)",
            "QPalette.HighlightedText",
            'QColor("#000000")',
        ):
            assert marker in source
        print(
            "OK — U-S5F1E1 explicit readable input-selection palette "
            "passed (source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1e1", name="U-S5F1E1")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    editors = panel.findChildren(QLineEdit)
    assert editors
    for editor in editors:
        palette = editor.palette()
        assert palette.color(QPalette.Highlight).name().lower() == "#e0a15a"
        assert (
            palette.color(QPalette.HighlightedText).name().lower()
            == "#000000"
        )

    declared_editor = panel._declared_opening_u_value.lineEdit()
    general_editor = panel._u_spin.lineEdit()
    assert declared_editor in editors
    assert general_editor in editors
    declared_editor.selectAll()
    general_editor.selectAll()
    assert declared_editor.hasSelectedText()
    assert general_editor.hasSelectedText()

    print(
        "OK — U-S5F1E1 selected text is explicitly dark on orange in "
        "ordinary entries and both U-value spin boxes."
    )


if __name__ == "__main__":
    main()
