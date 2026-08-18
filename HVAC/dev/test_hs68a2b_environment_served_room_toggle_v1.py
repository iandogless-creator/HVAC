from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.environment_panel_adapter import (
    EnvironmentPanelAdapter,
)
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    REMOTE_HEAT_SOURCE_LOCATION_MODE_V1,
    SERVED_ROOM_HEAT_SOURCE_LOCATION_MODE_V1,
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)


class _Context(QObject):
    environment_changed = Signal()
    project_changed = Signal()

    def __init__(self, project_state) -> None:
        super().__init__()
        self.project_state = project_state


def main() -> None:
    app = QApplication.instance() or QApplication([])
    topology = HydronicTopologyV1(
        heat_source_room_id="room-route",
        heat_source_location_mode=SERVED_ROOM_HEAT_SOURCE_LOCATION_MODE_V1,
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id="leg-001-primary-subleg",
                        label="Principal subleg",
                        origin_room_id="common-main",
                        route_room_ids=["room-route", "room-terminal"],
                        index_room_id="room-terminal",
                    )
                ],
            )
        ],
    )
    project = SimpleNamespace(
        environment=EnvironmentStateV1(),
        rooms={
            "room-remote": SimpleNamespace(name="Plant room"),
            "room-route": SimpleNamespace(name="Kitchen"),
            "room-terminal": SimpleNamespace(name="Hall"),
        },
        hydronic_topology=topology,
        hydronics_valid=True,
        heatloss_valid=True,
    )
    context = _Context(project)
    panel = EnvironmentPanel()
    adapter = EnvironmentPanelAdapter(context, panel)
    adapter.refresh()

    checkbox = panel._heat_source_served_room_mode
    combo = panel._heat_source_room_input
    routes_before = topology.all_route_room_ids()
    assert checkbox.text() == "In served room"
    assert checkbox.isChecked()
    assert "Unchecked:" in checkbox.toolTip()
    assert "Route membership is never changed here" in checkbox.toolTip()
    assert combo.currentData() == "room-route"

    project_change_count = 0

    def _count_project_change() -> None:
        nonlocal project_change_count
        project_change_count += 1

    context.project_changed.connect(_count_project_change)

    # Remote mode clears only the host reference.
    checkbox.setChecked(False)
    app.processEvents()
    assert not checkbox.isChecked()
    assert topology.heat_source_location_mode == REMOTE_HEAT_SOURCE_LOCATION_MODE_V1
    assert topology.heat_source_room_id == ""
    assert topology.all_route_room_ids() == routes_before
    assert combo.currentData() == ""
    assert combo.currentText() == "Remote / no room"
    assert not combo.isEnabled()
    assert project.hydronics_valid is False
    assert project.heatloss_valid is True
    assert project_change_count == 1

    # Served-room mode is explicit and requires a subsequent host choice.
    project.hydronics_valid = True
    checkbox.setChecked(True)
    app.processEvents()
    assert checkbox.isChecked()
    assert topology.heat_source_location_mode == SERVED_ROOM_HEAT_SOURCE_LOCATION_MODE_V1
    assert topology.heat_source_room_id == ""
    assert combo.isEnabled()
    assert combo.currentData() == ""
    assert combo.currentText() == "Select Heat Source room"
    assert project.hydronics_valid is False
    assert project.heatloss_valid is True
    assert project_change_count == 2

    project.hydronics_valid = True
    combo.setCurrentIndex(combo.findData("room-route"))
    app.processEvents()
    assert topology.heat_source_room_id == "room-route"
    assert topology.heat_source_location_mode == "served_room"
    assert topology.all_route_room_ids() == routes_before
    assert project.hydronics_valid is False
    assert project.heatloss_valid is True
    assert project_change_count == 3

    # Returning to remote clears the association again, never the room.
    project.hydronics_valid = True
    checkbox.setChecked(False)
    app.processEvents()
    assert topology.heat_source_room_id == ""
    assert topology.heat_source_location_mode == "remote"
    assert topology.all_route_room_ids() == routes_before
    assert project.hydronics_valid is False
    assert project.heatloss_valid is True
    assert project_change_count == 4

    print(
        "OK — H-S68-A2B Environment exposes a compact served-room Heat "
        "Source toggle with hover help; guarded changes mark Hydronics dirty, "
        "leave Heat-Loss and route membership unchanged."
    )


if __name__ == "__main__":
    main()
