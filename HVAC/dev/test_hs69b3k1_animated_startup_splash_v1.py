from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from HVAC.gui_v3.widgets.startup_splash_widget_v1 import (
    StartupSplashWidgetV1,
    splash_animation_state_v1,
)


def main() -> None:
    assert splash_animation_state_v1(0).phase == "forming"
    assert splash_animation_state_v1(219).phase == "forming"
    assert splash_animation_state_v1(220).phase == "falling"
    assert splash_animation_state_v1(979).phase == "falling"
    assert splash_animation_state_v1(980).phase == "splash"
    assert splash_animation_state_v1(1379).phase == "splash"
    assert splash_animation_state_v1(1380).phase == "settled"
    assert splash_animation_state_v1(1800).phase == "forming"

    app = QApplication.instance() or QApplication([])
    splash = StartupSplashWidgetV1()
    assert splash.objectName() == "hvacgooeeStartupSplashV1"
    assert splash.width() == 360
    assert splash.height() == 210
    assert splash.minimum_visible_ms_v1() == 1800
    assert splash.windowFlags() & Qt.WindowType.SplashScreen
    assert splash.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert splash.windowFlags() & Qt.WindowType.WindowStaysOnTopHint

    splash.show()
    app.processEvents()
    assert splash.isVisible()
    assert splash.remaining_minimum_ms_v1() <= 1800

    main_window = QWidget()
    splash.finish_v1(main_window)
    app.processEvents()
    assert main_window.isVisible()
    assert not splash.isVisible()
    main_window.close()
    splash.close()

    widget_source = Path(
        "HVAC/gui_v3/widgets/startup_splash_widget_v1.py"
    ).read_text(encoding="utf-8")
    assert "QPainterPath" in widget_source
    assert '"forming"' in widget_source
    assert '"falling"' in widget_source
    assert '"splash"' in widget_source
    assert "ProjectState" not in widget_source

    runner_source = Path("HVAC/gui_v3/run_gui_v3.py").read_text(
        encoding="utf-8"
    )
    splash_show = runner_source.index("splash.show()")
    callback = runner_source.index("def build_main_window_v1()")
    project_build = runner_source.index(
        "project_state = make_dev_bootstrap_project_state()"
    )
    main_build = runner_source.index("win = MainWindowV3(context=context)")
    reveal_call = runner_source.index("splash.finish_v1(win)")
    event_loop = runner_source.index("sys.exit(app.exec())")
    assert splash_show < callback < project_build < main_build < reveal_call
    assert reveal_call < event_loop
    assert "app.processEvents()" not in runner_source
    assert "splash.remaining_minimum_ms_v1()" in runner_source
    assert "build_main_window_v1," in runner_source

    print(
        "OK — H-S69-B3K1 shows a genuine code-painted startup splash "
        "with one forming/falling drop and one surface splash cycle, then "
        "reveals the unchanged main window without engineering mutation."
    )


if __name__ == "__main__":
    main()
