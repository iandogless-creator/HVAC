"""Run in the complete checkout: custom routes and real Navigation placement."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QSettings, QRect
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.gui_v3.run_gui_v3 import make_dev_bootstrap_project_state
from HVAC.gui_v3.widgets.workspace_view_manager_dialog_v2 import WorkspaceViewManagerDialogV2


def main() -> None:
    app = QApplication.instance() or QApplication([])

    def settle() -> None:
        for _ in range(8):
            app.processEvents()

    with TemporaryDirectory(prefix="hvac-navigation-integration-") as temporary:
        root = Path(temporary)
        settings = GuiSettings(root)
        custom = settings.create_workspace_view_v2(name="Custom Rooms", panels={"dock_rooms": "main"})
        settings.set_workspace_view_in_navigation_v2(custom, True)
        settings.set_last_workspace_view_v2(view_id=custom, mode="floating")
        settings.save()
        qt_settings = QSettings(str(root / "gui.ini"), QSettings.IniFormat)
        with patch("HVAC.gui_v3.main_window.GuiSettings", return_value=settings), patch(
            "HVAC.gui_v3.main_window.QSettings", return_value=qt_settings
        ):
            window = MainWindowV3(context=GuiProjectContext(
                project_state=make_dev_bootstrap_project_state()
            ))
        window.show()
        settle()
        nav = window._dock_navigation
        panel = window._workspace_navigation_panel_v1
        nav.setFloating(True)
        nav.show()
        settle()
        expected = QRect(60, 80, 520, 160)
        nav.setGeometry(expected)
        settle()

        def unchanged() -> None:
            settle()
            assert nav.isFloating() and nav.isVisible()
            assert nav.geometry() == expected

        try:
            assert panel.active_route_v1() == f"view:{custom}"
            assert panel.presentation_mode_v1() == "floating"
            for mode in ("main", "floating", "main"):
                window._on_workspace_navigation_presentation_requested_v1(mode)
                assert settings.last_workspace_view_v2() == {"view_id": custom, "mode": mode}
                unchanged()
            panel.button_for_route_v1("pipe_estimate").click()
            assert settings.last_workspace_view_v2()["view_id"] == "basic_sizing"
            panel.button_for_route_v1(f"view:{custom}").click()
            assert settings.last_workspace_view_v2()["view_id"] == custom
            unchanged()

            dialog = WorkspaceViewManagerDialogV2(
                settings=settings, panel_rows=(("dock_rooms", "Rooms"),), parent=window,
            )
            dialog.navigation_changed.connect(window._refresh_workspace_navigation_views_v1)
            before = settings.last_workspace_view_v2()
            dialog._in_navigation_checkbox.click()
            assert panel.button_for_route_v1(f"view:{custom}") is None
            assert settings.last_workspace_view_v2() == before
            unchanged()
            # Main/Exploded still targets the active view when its button is hidden.
            window._on_workspace_navigation_presentation_requested_v1("floating")
            assert settings.last_workspace_view_v2() == {"view_id": custom, "mode": "floating"}
            unchanged()
            dialog._in_navigation_checkbox.click()
            assert panel.button_for_route_v1(f"view:{custom}").isChecked()
            assert settings.rename_workspace_view_v2(custom, "My Rooms")
            window._refresh_workspace_navigation_views_v1()
            assert panel.button_for_route_v1(f"view:{custom}").text() == "My Rooms"
            unchanged()
            nav.hide()
            window._refresh_workspace_navigation_views_v1()
            settle()
            assert nav.isHidden()
            dialog.close()
        finally:
            window.close()
            settle()
    print("OK — H-S72-A4F real MainWindow routes custom views in Main/Exploded and retains Navigation placement and visibility during membership changes.")


if __name__ == "__main__":
    main()
