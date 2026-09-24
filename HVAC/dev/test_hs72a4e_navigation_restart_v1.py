from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QSettings, QRect, Qt
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.gui_v3.run_gui_v3 import make_dev_bootstrap_project_state


def child(root: Path, phase: str) -> None:
    app = QApplication.instance() or QApplication([])
    settings = GuiSettings(root)
    qt_settings = QSettings(str(root / "gui.ini"), QSettings.IniFormat)
    absent_screen = {"x": 5000, "y": 200, "width": 680, "height": 160,
                     "screen_name": "disconnected-test-monitor"}
    if phase == "missing-screen":
        qt_settings.setValue("workspace/navigation_placement_v1", json.dumps({
            "floating": True, "visible": True, "geometry": absent_screen,
        }))
    elif phase == "malformed":
        qt_settings.setValue("workspace/navigation_placement_v1", "not valid json")
    with patch("HVAC.gui_v3.main_window.GuiSettings", return_value=settings), patch(
        "HVAC.gui_v3.main_window.QSettings", return_value=qt_settings
    ):
        window = MainWindowV3(context=GuiProjectContext(
            project_state=make_dev_bootstrap_project_state()
        ))
    window.show()

    def settle() -> None:
        for _ in range(8):
            app.processEvents()

    settle()
    nav = window._dock_navigation
    expected = QRect(60, 80, 680, 160)
    try:
        if phase == "save-floating":
            window._apply_named_workspace_exploded_view_v2("basic_sizing")
            nav.setFloating(True)
            nav.show()
            settle()
            nav.setGeometry(expected)
            settle()
            assert nav.geometry() == expected, f"initial: {nav.geometry()}"
        elif phase == "restore-floating":
            assert settings.last_workspace_view_v2()["mode"] == "floating"
            assert nav.isFloating(), "Navigation re-docked after process restart"
            assert nav.isVisible(), "Navigation lost visibility after restart"
            assert nav.geometry() == expected, f"Navigation geometry lost after restart: {nav.geometry()} expected {expected}"
            for mode in ("main", "floating", "main"):
                window._on_workspace_navigation_presentation_requested_v1(mode)
                settle()
                assert nav.isFloating() and nav.geometry() == expected
            nav.close()
        elif phase == "restore-hidden":
            assert nav.isFloating() and nav.isHidden(), "Closed Navigation reopened"
            nav.toggleViewAction().trigger()
            settle()
            assert nav.isVisible() and nav.isFloating()
            assert nav.geometry() == expected
            nav.setFloating(False)
            window.addDockWidget(Qt.BottomDockWidgetArea, nav)
            nav.show()
        elif phase == "restore-docked":
            assert not nav.isFloating(), "User-docked Navigation was floated"
            assert nav.isVisible()
            assert window.dockWidgetArea(nav) == Qt.BottomDockWidgetArea
        elif phase == "missing-screen":
            assert nav.isFloating() and nav.isVisible()
            assert nav.screen().availableGeometry().contains(nav.geometry())
        elif phase == "malformed":
            assert nav.isVisible() and not nav.isFloating()
        settle()
    finally:
        window.close()
        settle()
    if phase == "missing-screen":
        saved = json.loads(str(qt_settings.value("workspace/navigation_placement_v1")))
        assert saved["geometry"] == absent_screen, "Missing-monitor placement overwritten"


def main() -> None:
    if len(sys.argv) == 3:
        child(Path(sys.argv[1]), sys.argv[2])
        return
    with TemporaryDirectory(prefix="hvac-navigation-restart-") as temporary:
        for phase in (
            "save-floating", "restore-floating", "restore-hidden", "restore-docked",
            "missing-screen", "malformed",
        ):
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), temporary, phase],
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode:
                print(result.stdout)
                print(result.stderr, file=sys.stderr)
                raise AssertionError(f"Restart phase failed: {phase}")
    print("OK — H-S72-A4E independent Navigation placement survives fresh-process "
          "restart, mode switches, close/reopen and deliberate bottom docking.")


if __name__ == "__main__":
    main()
