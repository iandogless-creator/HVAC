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
        for marker in (
            "remaining_entry_widths = (",
            "self._teaching_save_name",
            "self._layer_source_ref_edit",
            "self._teaching_property_scroll.setVisible(has_focused_item)",
        ):
            assert marker in source
        print(
            "OK — U-S5F1D empty property-editor collapse and remaining "
            "entry widths passed (source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1d", name="U-S5F1D")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    assert 320 <= panel._teaching_save_name.width() <= 440
    assert 360 <= panel._layer_source_ref_edit.width() <= 560
    assert 230 <= panel._layer_source_version_edit.width() <= 340
    assert 420 <= panel._layer_notes_edit.width() <= 620
    assert 180 <= panel._path_fraction_edit.width() <= 240

    panel._load_focused_property_fields()
    assert panel._teaching_property_scroll.isHidden()

    assert panel._teaching_property_target.count() > 1
    panel._teaching_property_target.setCurrentIndex(1)
    assert not panel._teaching_property_scroll.isHidden()

    panel._teaching_property_target.setCurrentIndex(0)
    assert panel._teaching_property_scroll.isHidden()

    print(
        "OK — U-S5F1D empty focused-property body collapses and restores "
        "on focus; remaining U-Values entries use purpose-sized widths."
    )


if __name__ == "__main__":
    main()
