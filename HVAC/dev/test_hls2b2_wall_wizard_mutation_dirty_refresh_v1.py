from __future__ import annotations

from pathlib import Path


SOURCE_PATH = Path("HVAC/gui_v3/adapters/wall_wizard_adapter.py")


def main() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")

    helper_start = source.index("    def _notify_opening_schedule_changed(")
    next_handler = source.index("    def _on_opening_requested(", helper_start)
    helper = source[helper_start:next_handler]

    dirty_pos = helper.index("ps.mark_heatloss_dirty()")
    refresh_pos = helper.index("self._context.room_state_changed.emit(room_id)")
    assert dirty_pos < refresh_pos

    assert source.count(
        "self._notify_opening_schedule_changed(ps, room_id)"
    ) == 3
    assert "notify_project_changed" not in helper
    assert "heatloss_results" not in helper
    assert "run_heatloss" not in helper

    print(
        "OK — HL-S2B2 Wall Wizard Add/Remove/Clear invalidate committed "
        "Heat-Loss and emit one room-scoped live refresh handoff."
    )


if __name__ == "__main__":
    main()
