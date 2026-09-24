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


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(prefix="hvac-navigation-test-") as temporary:
        root = Path(temporary)
        settings = GuiSettings(root)
        qt_settings = QSettings(str(root / "gui.ini"), QSettings.IniFormat)
        with patch("HVAC.gui_v3.main_window.GuiSettings", return_value=settings), patch(
            "HVAC.gui_v3.main_window.QSettings", return_value=qt_settings
        ):
            window = MainWindowV3(context=GuiProjectContext(
                project_state=make_dev_bootstrap_project_state()
            ))
        window.show()

        def settle() -> None:
            for _ in range(6):
                app.processEvents()

        settle()
        nav = window._dock_navigation
        nav.setFloating(True)
        nav.show()
        settle()
        nav.setGeometry(QRect(60, 80, 540, 160))
        settle()
        original = QRect(nav.geometry())

        def unchanged(label: str) -> None:
            settle()
            assert nav.isFloating(), f"{label}: Navigation re-docked"
            assert nav.isVisible(), f"{label}: Navigation hidden"
            assert nav.geometry() == original, f"{label}: Navigation moved/resized"

        try:
            for route in (
                "heat_loss_edit", "heat_loss_presentation", "pipe_estimate",
                "proportioning_schematic", "return_schematic", "results",
            ):
                window._on_workspace_navigation_view_requested_v1(route)
                unchanged(f"route {route}")
                for mode in ("floating", "main", "floating"):
                    window._on_workspace_navigation_presentation_requested_v1(mode)
                    unchanged(f"{route} / {mode}")

            window._show_exclusive_panel_view_v1(window._dock_rooms)
            unchanged("individual Rooms panel")

            # A legacy saved list must never claim ownership of Navigation.
            settings.set_named_workspace_layout_v1("results:exploded", {
                "panel_ids": ["dock_hydronics", "dock_navigation"],
                "docks": {},
            })
            window._apply_named_workspace_exploded_view_v2("results")
            unchanged("legacy exploded membership")
            assert nav not in window._active_exploded_workspace_docks_v1
            window._apply_named_workspace_main_view_v2("results")
            unchanged("return from legacy exploded membership")

            # Protect against an old in-memory active list too.
            window._active_exploded_workspace_docks_v1 = (nav, window._dock_rooms)
            window._finish_active_exploded_workspace_v1()
            unchanged("stale active exploded list")
            window._active_docked_workspace_docks_v1 = (nav, window._dock_rooms)
            window._prepare_hydronics_workspace_view_v1("results", (window._dock_rooms,))
            unchanged("stale active docked list")

            settings.set_workspace_panel_set_v1(
                "results:docked", ["dock_rooms", "dock_navigation"]
            )
            window._show_hydronics_workspace_docks_v1((window._dock_rooms,))
            unchanged("legacy docked membership")

            settings.set_named_workspace_layout_v1("user:exploded", {
                "docks": {
                    "dock_navigation": {"x": 5, "y": 5, "width": 320, "height": 200},
                    "dock_rooms": {"x": 5, "y": 5, "width": 320, "height": 200},
                },
            })
            window._apply_user_workspace_v1()
            unchanged("legacy user workspace membership")
            assert nav not in window._active_exploded_workspace_docks_v1

            nav.hide()
            window._apply_named_workspace_main_view_v2("results")
            window._apply_named_workspace_exploded_view_v2("results")
            settle()
            assert nav.isHidden(), "closed Navigation reopened by a view switch"

            # Deliberate docking remains supported; switching does not force float.
            nav.setFloating(False)
            nav.show()
            window._apply_named_workspace_main_view_v2("results")
            window._apply_named_workspace_exploded_view_v2("results")
            settle()
            assert not nav.isFloating(), "deliberately docked Navigation floated"
        finally:
            window.close()
            settle()

    print("OK — H-S72-A4D real Navigation retains floating geometry and visibility "
          "across views, Main/Exploded, individual panels and legacy membership.")


if __name__ == "__main__":
    main()
