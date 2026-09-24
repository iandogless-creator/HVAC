from __future__ import annotations

import inspect

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.gui_v3.panels.workspace_navigation_panel_v1 import (
    WorkspaceNavigationPanelV1,
)
from HVAC.gui_v3.widgets.workspace_view_manager_dialog_v2 import (
    WorkspaceViewManagerDialogV2,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = WorkspaceNavigationPanelV1()

    expected_routes = (
        "heat_loss_edit",
        "heat_loss_presentation",
        "pipe_estimate",
        "proportioning_schematic",
        "return_schematic",
        "results",
    )
    expected_labels = {
        "heat_loss_edit": "HL Edit",
        "heat_loss_presentation": "HL View",
        "pipe_estimate": "Pipe Est.",
        "proportioning_schematic": "Prop. Sch.",
        "return_schematic": "RR View",
        "results": "Results",
    }
    requested: list[str] = []
    panel.view_requested.connect(requested.append)
    for route_id in expected_routes:
        button = panel.button_for_route_v1(route_id)
        assert button is not None
        assert button.text() == expected_labels[route_id]
        assert button.property("hvacNavigationRole") == "view"

    panel.button_for_route_v1("return_schematic").click()
    assert requested == ["return_schematic"]
    assert panel.button_for_route_v1("return_schematic").isChecked()

    modes: list[str] = []
    panel.presentation_mode_requested.connect(modes.append)
    assert panel.presentation_mode_v1() == "main"
    assert panel.presentation_button_v1().text() == "Explode"
    panel.presentation_button_v1().click()
    assert modes == ["floating"]
    assert panel.presentation_mode_v1() == "floating"
    assert panel.presentation_button_v1().text() == "Main"
    assert panel.presentation_button_v1().property(
        "hvacNavigationRole"
    ) == "presentation"
    panel.set_presentation_mode_v1("main")
    assert modes == ["floating"]

    education_states: list[bool] = []
    panel.education_toggled.connect(education_states.append)
    panel.education_button_v1().click()
    assert education_states == [True]
    assert panel.education_button_v1().property(
        "hvacNavigationRole"
    ) == "education"

    preferences = []
    panel.preferences_requested.connect(lambda: preferences.append(True))
    panel.preferences_button_v1().click()
    assert preferences == [True]
    assert panel.preferences_button_v1().text() == "⚙"

    panel.resize(520, 120)
    app.processEvents()
    positions = {
        panel._button_grid.getItemPosition(index)[:2]
        for index in range(panel._button_grid.count())
    }
    assert len({row for row, _column in positions}) >= 2

    manager_source = inspect.getsource(WorkspaceViewManagerDialogV2)
    assert "panel_float_requested" not in manager_source
    assert "WindowStaysOnTopHint" not in manager_source

    routing_source = inspect.getsource(
        MainWindowV3._on_workspace_navigation_view_requested_v1
    )
    for route_id in expected_routes:
        assert route_id in routing_source
    assert "_apply_named_workspace_main_view_v2" in routing_source
    assert "_apply_named_workspace_exploded_view_v2" in routing_source

    mode_source = inspect.getsource(
        MainWindowV3._on_workspace_navigation_presentation_requested_v1
    )
    assert 'stable_mode == "floating"' in mode_source
    assert "active_route_v1" in mode_source

    exploded_source = inspect.getsource(
        MainWindowV3._apply_named_workspace_exploded_view_v2
    )
    assert 'mode="floating"' in exploded_source
    assert "dock_navigation" in exploded_source
    assert "addDockWidget(Qt.TopDockWidgetArea" not in exploded_source

    main_source = inspect.getsource(
        MainWindowV3._apply_named_workspace_main_view_v2
    )
    assert "dock is not self._dock_navigation" in main_source
    assert "addDockWidget(Qt.TopDockWidgetArea" not in main_source

    legacy_exploded_source = inspect.getsource(
        MainWindowV3._apply_exploded_workspace_view_v1
    )
    assert '"_dock_navigation"' in legacy_exploded_source
    assert "continue" in legacy_exploded_source

    restore_source = inspect.getsource(
        MainWindowV3._restore_last_workspace_presentation_v1
    )
    assert 'selected["mode"] == "floating"' in restore_source
    assert "_apply_named_workspace_exploded_view_v2" in restore_source

    build_source = inspect.getsource(MainWindowV3._build_ui)
    assert "DockWidgetFloatable" in build_source

    return_source = inspect.getsource(
        HydronicsSchematicPanel.focus_return_schematic_v1
    )
    assert "_return_path_comparison_table" in return_source
    assert "select_proportioning_tab" in return_source

    panel.close()
    print(
        "OK — H-S72-A4 integrated Navigation panel routes the accepted "
        "views, retains Main/Exploded mode, reflows when narrow, toggles "
        "Education and opens preferences without a floating palette."
    )


if __name__ == "__main__":
    main()
