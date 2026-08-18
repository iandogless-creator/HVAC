from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel
from HVAC.project.guarded_room_deletion_v1 import (
    build_guarded_room_deletion_plan_v1,
    delete_room_guarded_v1,
)


class TopologyStub:
    def __init__(self, host: str = "", routes=()) -> None:
        self.heat_source_room_id = host
        self.routes = tuple(routes)

    def all_route_room_ids(self):
        return self.routes


class ProjectStub:
    def __init__(self) -> None:
        self.rooms = {
            "room-boiler": SimpleNamespace(name="Boiler / Heat Source"),
            "room-001": SimpleNamespace(name="Kitchen"),
        }
        self.hydronic_topology = TopologyStub()
        self.emitters = {}
        self.boundary_segments = {
            "boiler-wall": SimpleNamespace(
                owner_room_id="room-boiler",
                adjacent_room_id=None,
            ),
            "kitchen-wall": SimpleNamespace(
                owner_room_id="room-001",
                adjacent_room_id=None,
            ),
        }
        self.surface_construction_map = {"boiler-wall": "DEV-EXT-WALL"}
        self.openings_by_surface = {"boiler-wall": [object()]}
        self.room_opening_schedules = {"room-boiler": object()}
        self.hydronic_room_paired_pipe_length_intent = SimpleNamespace(
            lengths_by_room_id={"room-boiler": object()}
        )
        self.heatloss_valid = True
        self.hydronics_valid = True

    def mark_heatloss_dirty(self) -> None:
        self.heatloss_valid = False


def main() -> None:
    project = ProjectStub()
    plan = build_guarded_room_deletion_plan_v1(project, "room-boiler")
    assert plan.ready
    assert plan.owned_surface_ids == ("boiler-wall",)

    project.hydronic_topology.heat_source_room_id = "room-boiler"
    blocked = build_guarded_room_deletion_plan_v1(project, "room-boiler")
    assert "active Heat Source" in " ".join(blocked.blockers)
    project.hydronic_topology.heat_source_room_id = ""

    project.hydronic_topology.routes = ("room-boiler",)
    blocked = build_guarded_room_deletion_plan_v1(project, "room-boiler")
    assert "served hydronic route" in " ".join(blocked.blockers)
    project.hydronic_topology.routes = ()

    project.emitters["emitter-1"] = SimpleNamespace(room_id="room-boiler")
    blocked = build_guarded_room_deletion_plan_v1(project, "room-boiler")
    assert "assigned hydronic emitter" in " ".join(blocked.blockers)
    project.emitters.clear()

    project.boundary_segments["kitchen-adjacent"] = SimpleNamespace(
        owner_room_id="room-001",
        adjacent_room_id="room-boiler",
    )
    blocked = build_guarded_room_deletion_plan_v1(project, "room-boiler")
    assert "adjacent-room surface" in " ".join(blocked.blockers)
    project.boundary_segments.pop("kitchen-adjacent")

    delete_room_guarded_v1(project, "room-boiler")
    assert set(project.rooms) == {"room-001"}
    assert "boiler-wall" not in project.boundary_segments
    assert "boiler-wall" not in project.surface_construction_map
    assert "boiler-wall" not in project.openings_by_surface
    assert "room-boiler" not in project.room_opening_schedules
    assert (
        "room-boiler"
        not in project.hydronic_room_paired_pipe_length_intent.lengths_by_room_id
    )
    assert project.heatloss_valid is False
    assert project.hydronics_valid is False

    app = QApplication.instance() or QApplication([])
    panel = RoomTreePanel()
    assert panel._remove_room_btn.text() == "Remove"
    assert panel._remove_room_btn.toolTip().count("\n") == 2
    assert callable(panel._emit_remove_requested)
    panel.close()

    adapter_source = Path(
        "HVAC/gui_v3/adapters/room_tree_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "QMessageBox.question(" in adapter_source
    assert "delete_room_guarded_v1(ps, room_id)" in adapter_source

    print(
        "OK — H-S68-A3 guarded room deletion and compact wrapped "
        "Rooms-panel help passed."
    )


if __name__ == "__main__":
    main()
