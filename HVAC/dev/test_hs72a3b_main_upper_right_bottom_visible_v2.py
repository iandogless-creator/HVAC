from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QLabel, QMainWindow

from HVAC.gui_v3.context.workspace_dock_layout_reset_v2 import (
    apply_named_workspace_docks_v2,
)


def _dock(window: QMainWindow, name: str) -> QDockWidget:
    dock = QDockWidget(name, window)
    dock.setObjectName(name)
    dock.setWidget(QLabel(name, dock))
    return dock


def main() -> None:
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.resize(1280, 900)

    main_dock = _dock(window, "dock_main")
    side_a = _dock(window, "dock_side_a")
    side_b = _dock(window, "dock_side_b")
    bottom_a = _dock(window, "dock_bottom_a")
    bottom_b = _dock(window, "dock_bottom_b")
    docks = (main_dock, side_a, side_b, bottom_a, bottom_b)

    # Tall Side panels reproduce the practical constraint which collapsed a
    # global Qt Bottom area in the Basic Sizing runtime view.
    side_a.setMinimumHeight(390)
    side_b.setMinimumHeight(390)
    bottom_a.setMinimumHeight(70)
    bottom_b.setMinimumHeight(70)

    window.addDockWidget(Qt.LeftDockWidgetArea, main_dock)
    window.addDockWidget(Qt.LeftDockWidgetArea, side_a)
    window.tabifyDockWidget(side_a, main_dock)

    visible = apply_named_workspace_docks_v2(
        window,
        all_docks=docks,
        main_dock=main_dock,
        side_docks=(side_a, side_b),
        bottom_docks=(bottom_a, bottom_b),
    )
    window.show()
    app.processEvents()
    window.resizeDocks([side_a, main_dock], [420, 860], Qt.Horizontal)
    window.resizeDocks([main_dock, bottom_a], [620, 220], Qt.Vertical)
    app.processEvents()

    assert visible == docks
    assert window.dockWidgetArea(main_dock) == Qt.RightDockWidgetArea
    assert window.dockWidgetArea(side_a) == Qt.LeftDockWidgetArea
    assert window.dockWidgetArea(side_b) == Qt.LeftDockWidgetArea
    assert window.dockWidgetArea(bottom_a) == Qt.RightDockWidgetArea
    assert window.dockWidgetArea(bottom_b) == Qt.RightDockWidgetArea
    assert all(not window.tabifiedDockWidgets(dock) for dock in docks)
    assert all(dock.isVisible() and dock.width() > 0 and dock.height() > 0
               for dock in docks)
    assert main_dock.geometry().center().x() > side_a.geometry().center().x()
    assert bottom_a.geometry().top() > main_dock.geometry().top()
    assert bottom_b.geometry().top() > main_dock.geometry().top()
    assert bottom_a.geometry().left() < bottom_b.geometry().left()

    window.close()
    print(
        "OK — H-S72-A3B keeps Main upper-right, Side panels stacked left "
        "and Bottom panels visible below Main without changing focus colours."
    )


if __name__ == "__main__":
    main()
