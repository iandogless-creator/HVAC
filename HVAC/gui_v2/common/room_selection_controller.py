from PySide6.QtCore import QObject, Signal


class RoomSelectionController(QObject):
    """
    Single source of truth for current room selection.
    """

    room_selected = Signal(str)  # room_id

    def __init__(self):
        super().__init__()
        self._current_room_id: str | None = None

    def select_room(self, room_id: str):
        if room_id == self._current_room_id:
            return

        self._current_room_id = room_id
        self.room_selected.emit(room_id)

    @property
    def current_room_id(self) -> str | None:
        return self._current_room_id
