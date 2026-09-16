from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QLabel, QMainWindow

from HVAC.gui_v3.context.workspace_dock_layout_reset_v2 import (
    reset_workspace_docks_v2,
)


def _dock(window: QMainWindow, name: str) -> QDockWidget:
    dock = QDockWidget(name, window)
    dock.setObjectName(name)
    dock.setWidget(QLabel(name, dock))
    return dock


def main() -> None:
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    main_dock = _dock(window, "dock_main")
    side_a = _dock(window, "dock_side_a")
    side_b = _dock(window, "dock_side_b")
    bottom = _dock(window, "dock_bottom")
    docks = (main_dock, side_a, side_b, bottom)

    # Recreate the observed fault: the intended Main dock is still tabified
    # with a Side dock from an earlier workspace arrangement.
    window.addDockWidget(Qt.LeftDockWidgetArea, main_dock)
    window.addDockWidget(Qt.LeftDockWidgetArea, side_b)
    window.tabifyDockWidget(side_b, main_dock)
    window.addDockWidget(Qt.RightDockWidgetArea, side_a)
    window.addDockWidget(Qt.BottomDockWidgetArea, bottom)
    assert side_b in window.tabifiedDockWidgets(main_dock)

    reset_workspace_docks_v2(window, docks)
    assert all(
        window.dockWidgetArea(dock) == Qt.NoDockWidgetArea
        for dock in docks
    )
    assert all(not window.tabifiedDockWidgets(dock) for dock in docks)

    window.addDockWidget(Qt.LeftDockWidgetArea, main_dock)
    window.addDockWidget(Qt.RightDockWidgetArea, side_a)
    window.addDockWidget(Qt.RightDockWidgetArea, side_b)
    window.splitDockWidget(side_a, side_b, Qt.Vertical)
    window.addDockWidget(Qt.BottomDockWidgetArea, bottom)
    for dock in docks:
        dock.show()
    main_dock.raise_()
    window.show()
    app.processEvents()

    assert window.dockWidgetArea(main_dock) == Qt.LeftDockWidgetArea
    assert window.dockWidgetArea(side_a) == Qt.RightDockWidgetArea
    assert window.dockWidgetArea(side_b) == Qt.RightDockWidgetArea
    assert window.dockWidgetArea(bottom) == Qt.BottomDockWidgetArea
    assert all(not window.tabifiedDockWidgets(dock) for dock in docks)
    assert all(dock.isVisible() for dock in docks)
    assert bottom.height() > 0

    window.close()
    print(
        "OK — H-S72-A3A clears stale dock tab relationships before "
        "restoring the named Main/Side/Bottom arrangement."
    )


if __name__ == "__main__":
    main()
