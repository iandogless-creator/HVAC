from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QMainWindow

from HVAC.gui_v3.context.workspace_dock_layout_reset_v2 import (
    apply_named_workspace_docks_v2,
)
from HVAC.gui_v3.panels.basic_hydronics_panel import (
    BasicHydronicsPanel,
)
from HVAC.gui_v3.panels.construction_panel import ConstructionPanel
from HVAC.gui_v3.panels.local_k_panel import LocalKPanel
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel


def _dock(window: QMainWindow, name: str, widget) -> QDockWidget:
    dock = QDockWidget(name, window)
    dock.setObjectName(name)
    dock.setWidget(widget)
    return dock


def main() -> None:
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.resize(1280, 900)

    main_dock = _dock(
        window, "dock_main", BasicHydronicsPanel()
    )
    local_k = _dock(window, "dock_local_k", LocalKPanel())
    construction = _dock(
        window, "dock_construction", ConstructionPanel()
    )
    rooms = _dock(window, "dock_rooms", RoomTreePanel())
    docks = (main_dock, local_k, construction, rooms)

    visible = apply_named_workspace_docks_v2(
        window,
        all_docks=docks,
        main_dock=main_dock,
        side_docks=(local_k, construction),
        bottom_docks=(rooms,),
    )
    window.show()
    app.processEvents()
    window.resizeDocks([local_k, main_dock], [360, 920], Qt.Horizontal)
    window.resizeDocks([main_dock, rooms], [680, 220], Qt.Vertical)
    app.processEvents()

    assert visible == docks
    assert all(dock.isVisible() for dock in docks)
    assert all(dock.width() >= 160 and dock.height() >= 80 for dock in docks)
    assert window.height() <= 920
    assert bool(local_k.widget().property("hvacNamedWorkspaceSideScrollV2"))
    assert bool(
        construction.widget().property("hvacNamedWorkspaceSideScrollV2")
    )
    assert not bool(
        main_dock.widget().property("hvacNamedWorkspaceSideScrollV2")
    )
    assert not bool(rooms.widget().property("hvacNamedWorkspaceSideScrollV2"))
    assert local_k.width() < main_dock.width()
    assert construction.geometry().top() > local_k.geometry().top()
    assert rooms.geometry().top() > main_dock.geometry().top()
    assert rooms.geometry().bottom() <= window.rect().bottom()
    assert all(not window.tabifiedDockWidgets(dock) for dock in docks)

    window.close()
    print(
        "OK — H-S72-A3C1 real Basic Hydronics, scrollable Side "
        "panels and Rooms fit within one compact Main/Side/Bottom window."
    )


if __name__ == "__main__":
    main()
