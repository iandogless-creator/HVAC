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
            "def _apply_uvp_button_hierarchy_v1",
            'button.setProperty("uvpButtonRole", "primaryAction")',
            'toggle.setProperty("uvpButtonRole", "sectionToggle")',
            "Select a surface before assigning a construction",
        ):
            assert marker in source
        print(
            "OK — U-S5F1A U-Values button hierarchy passed "
            "(source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1a", name="U-S5F1A")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    primary_actions = (
        panel._declared_opening_save_button,
        panel._member_spacing_apply,
        panel._teaching_layer_apply,
        panel._teaching_path_apply,
        panel._teaching_save_button,
        panel._assign_btn,
    )
    for button in primary_actions:
        assert button.property("uvpButtonRole") == "primaryAction"
        assert button.minimumHeight() >= 34
        assert button.minimumWidth() >= 230
        assert button.maximumWidth() <= 360

    reset = panel._teaching_property_reset
    assert reset.property("uvpButtonRole") == "secondaryAction"
    assert reset.minimumHeight() >= 34
    assert reset.maximumWidth() <= 360

    toggles = (
        panel._declared_opening_toggle,
        panel._teaching_toggle,
        panel._teaching_property_toggle,
    )
    for toggle in toggles:
        assert toggle.property("uvpButtonRole") == "sectionToggle"
        assert toggle.minimumHeight() >= 32
        assert toggle.text().startswith("▸")

    assert not panel._assign_btn.isEnabled()
    assert "Select a surface" in panel._assign_btn.toolTip()
    panel._set_assign_target_available_v1(True)
    assert panel._assign_btn.isEnabled()
    assert "focused surface" in panel._assign_btn.toolTip()

    panel._declared_opening_toggle.click()
    assert panel._declared_opening_toggle.text().startswith("▾")
    assert panel._declared_opening_box.isVisibleTo(panel)
    panel._teaching_toggle.click()
    assert panel._teaching_toggle.text().startswith("▾")

    style = panel.styleSheet()
    assert "#2e7d32" in style
    assert 'uvpButtonRole="sectionToggle"' in style
    assert "orange" not in style.lower()

    print(
        "OK — U-S5F1A U-Values actions are consistently sized and "
        "section controls are visibly distinct."
    )


if __name__ == "__main__":
    main()
