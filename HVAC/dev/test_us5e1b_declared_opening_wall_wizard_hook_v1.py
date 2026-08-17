from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.core.opening_schedule_v1 import (
    OpeningScheduleItemV1,
    RoomOpeningScheduleV1,
)
from HVAC.gui_v3.adapters.wall_wizard_adapter import WallWizardAdapter
from HVAC.gui_v3.wizards.wall_wizard import (
    OpeningPreview,
    WallWizardDialog,
    WallWizardProjection,
)


class ProjectStub:
    def __init__(self) -> None:
        self.constructions = {
            "USR-DECLARED-WINDOW-W1-A1": SimpleNamespace(name="Kitchen window"),
            "USR-DECLARED-DOOR-D1-B2": SimpleNamespace(name="Front door"),
            "DEV-EXT-WALL": SimpleNamespace(name="External wall"),
        }
        self.boundary_segments = {
            "SEG-1": SimpleNamespace(owner_room_id="ROOM-1"),
        }
        self.room_opening_schedules = {}
        self.heatloss_valid = True

    def mark_heatloss_dirty(self) -> None:
        self.heatloss_valid = False

    def get_or_create_room_opening_schedule(self, room_id: str):
        return self.room_opening_schedules.setdefault(
            room_id,
            RoomOpeningScheduleV1(room_id=room_id),
        )


def main() -> None:
    app = QApplication.instance() or QApplication([])
    project = ProjectStub()
    room_notifications = []
    context = SimpleNamespace(
        project_state=project,
        room_state_changed=SimpleNamespace(
            emit=room_notifications.append,
        ),
    )
    adapter = object.__new__(WallWizardAdapter)
    adapter._context = context

    choices = adapter._opening_construction_choices(project)
    assert ("USR-DECLARED-WINDOW-W1-A1", "Kitchen window", "WINDOW") in choices
    assert ("USR-DECLARED-DOOR-D1-B2", "Front door", "DOOR") in choices
    assert all(row[0] != "DEV-EXT-WALL" for row in choices)

    dialog = WallWizardDialog()
    emitted = []
    dialog.opening_requested.connect(lambda sid, opening: emitted.append((sid, opening)))
    dialog.set_projection(WallWizardProjection(
        surface_id="SEG-1",
        room_label="Kitchen",
        element_label="External Wall",
        area_m2=20.0,
        construction_id="DEV-EXT-WALL",
        construction_name="External wall",
        u_value_W_m2K=0.26,
        opening_construction_choices=choices,
    ))
    standard_index = dialog._profile_combo.findData("STANDARD_WINDOW")
    assert standard_index >= 0
    dialog._profile_combo.setCurrentIndex(standard_index)
    assert dialog._opening_construction_combo.count() == 1
    assert dialog._opening_construction_combo.currentData() == "USR-DECLARED-WINDOW-W1-A1"
    dialog._add_selected_opening()
    assert emitted
    opening = emitted[-1][1]
    assert opening.construction_id == "USR-DECLARED-WINDOW-W1-A1"

    adapter._on_opening_requested("SEG-1", opening)
    assert project.heatloss_valid is False
    assert room_notifications == ["ROOM-1"]
    saved = project.room_opening_schedules["ROOM-1"].openings
    assert len(saved) == 1
    assert saved[0].construction_id == "USR-DECLARED-WINDOW-W1-A1"

    # An otherwise-identical opening with another construction remains distinct.
    schedule = project.room_opening_schedules["ROOM-1"]
    schedule.add_item(OpeningScheduleItemV1(
        opening_type="WINDOW",
        profile_id="STANDARD_WINDOW",
        profile_name="Standard Window",
        width_m=1.2,
        height_m=1.2,
        quantity=1,
        construction_id="OTHER-WINDOW",
    ))
    schedule.remove_matching_items(
        profile_id="STANDARD_WINDOW",
        width_m=1.2,
        height_m=1.2,
        construction_id="USR-DECLARED-WINDOW-W1-A1",
    )
    assert [item.construction_id for item in schedule.openings] == ["OTHER-WINDOW"]

    print(
        "OK — U-S5E1B Opening Wizard selects compatible declared window/door "
        "constructions and stores their construction_id."
    )


if __name__ == "__main__":
    main()
