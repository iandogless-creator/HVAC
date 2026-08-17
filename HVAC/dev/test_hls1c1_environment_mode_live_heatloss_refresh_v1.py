from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter


class _Project:
    def __init__(self) -> None:
        self.environment = EnvironmentStateV1(
            default_internal_temp_C=21.0,
            use_internal_environmental_temperature=False,
        )
        self.heatloss_valid = True


class _Context(QObject):
    room_state_changed = Signal(str)
    current_room_changed = Signal(str)
    construction_focus_changed = Signal(str)
    environment_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.project_state = _Project()
        self.current_room_id = None


class _Panel(QObject):
    run_requested = Signal()
    cell_selected = Signal(int, int)
    surface_focus_requested = Signal(object)
    wall_wizard_requested = Signal(str)
    adjacency_edit_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.environmental_mode = None
        self.heatloss_valid = None
        self.refresh_projection_count = 0

    def set_environmental_temperature_mode(self, enabled: bool) -> None:
        self.environmental_mode = bool(enabled)
        self.refresh_projection_count += 1

    def set_heatloss_status(self, *, is_valid: bool) -> None:
        self.heatloss_valid = bool(is_valid)

    def clear(self) -> None:
        return

    def set_run_enabled(self, _enabled: bool) -> None:
        return


def main() -> None:
    app = QApplication.instance() or QApplication([])
    context = _Context()
    panel = _Panel()
    adapter = HeatLossPanelAdapter(panel=panel, context=context)

    adapter.refresh()
    assert panel.environmental_mode is False
    assert panel.heatloss_valid is True
    initial_count = panel.refresh_projection_count

    context.project_state.environment.use_internal_environmental_temperature = True
    context.project_state.heatloss_valid = False
    context.environment_changed.emit()
    app.processEvents()

    assert panel.refresh_projection_count == initial_count + 1
    assert panel.environmental_mode is True
    assert panel.heatloss_valid is False

    print(
        "OK — HL-S1C1 Environment mode changes immediately refresh the "
        "Heat-Loss Ti/tei, tai-row and dirty-state projection."
    )


if __name__ == "__main__":
    main()
