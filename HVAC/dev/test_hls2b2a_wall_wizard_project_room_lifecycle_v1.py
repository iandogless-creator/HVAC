from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from HVAC.gui_v3.adapters.wall_wizard_adapter import WallWizardAdapter


class FakeContext(QObject):
    wall_wizard_requested = Signal(str)
    project_changed = Signal()
    current_room_changed = Signal(object)

    def __init__(self, project_state: object) -> None:
        super().__init__()
        self.project_state = project_state


class FakeDialog:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def main() -> None:
    first_project = object()
    context = FakeContext(first_project)
    adapter = WallWizardAdapter(context=context)

    same_project_dialog = FakeDialog()
    adapter._dialog = same_project_dialog
    adapter._dialog_project_state = first_project
    context.project_changed.emit()
    assert same_project_dialog.closed is False
    assert adapter._dialog is same_project_dialog

    second_project = object()
    context.project_state = second_project
    context.project_changed.emit()
    assert same_project_dialog.closed is True
    assert adapter._dialog is None
    assert adapter._dialog_project_state is None

    room_change_dialog = FakeDialog()
    adapter._dialog = room_change_dialog
    adapter._dialog_project_state = second_project
    context.current_room_changed.emit("room-002")
    assert room_change_dialog.closed is True
    assert adapter._dialog is None
    assert adapter._dialog_project_state is None

    print(
        "OK — HL-S2B2A stale Wall Wizard closes on authoritative project "
        "swap and room change, but remains open for same-project refresh."
    )


if __name__ == "__main__":
    main()
