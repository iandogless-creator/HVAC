class RoomStore:
    def __init__(self):
        self._rows = {}

    def get_row(self, room_id):
        return self._rows[room_id]

    def upsert_row(self, row_dto):
        self._rows[row_dto.room_id] = row_dto

    def all_rows(self):
        return list(self._rows.values())
