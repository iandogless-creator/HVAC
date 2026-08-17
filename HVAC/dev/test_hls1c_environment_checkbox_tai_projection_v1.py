from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.environment_panel_adapter import (
    EnvironmentPanelAdapter,
)
from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3


class _Project:
    def __init__(self) -> None:
        self.environment = EnvironmentStateV1(
            default_internal_temp_C=21.0,
            use_internal_environmental_temperature=False,
        )
        self.heatloss_valid = True

    def mark_heatloss_dirty(self) -> None:
        self.heatloss_valid = False


class _Context(QObject):
    environment_changed = Signal()
    project_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.project_state = _Project()


def main() -> None:
    app = QApplication.instance() or QApplication([])

    context = _Context()
    environment_panel = EnvironmentPanel()
    adapter = EnvironmentPanelAdapter(context, environment_panel)
    adapter.refresh()

    checkbox = environment_panel._internal_environmental_temperature_mode
    label = environment_panel._internal_temperature_label
    assert checkbox.isChecked() is False
    assert checkbox.text() == "Ti"
    assert label.text() == "Default internal temperature, Ti (°C)"

    checkbox.click()
    app.processEvents()
    assert context.project_state.environment.use_internal_environmental_temperature
    assert context.project_state.heatloss_valid is False
    assert checkbox.text() == "tei"
    assert label.text() == "Internal environmental temperature, tei (°C)"

    heatloss_panel = HeatLossPanelV3()
    heatloss_panel.set_environmental_temperature_mode(False)
    heatloss_panel.set_internal_temperature(21.0, environmental_mode=False)
    assert heatloss_panel._ti_label.text() == "Ti: 21.0 °C"
    assert heatloss_panel._label_tai.isHidden()

    heatloss_panel.set_environmental_temperature_mode(True)
    heatloss_panel.set_internal_temperature(20.0, environmental_mode=True)
    heatloss_panel.set_room_results(
        sum_qf=960.0,
        ach=0.5,
        qv=462.0,
        qt=1422.0,
        tai=25.0,
    )
    assert heatloss_panel._ti_label.text() == "tei: 20.0 °C"
    assert not heatloss_panel._label_tai.isHidden()
    assert heatloss_panel._value_tai.text() == "25.0 °C"

    layout = heatloss_panel._results_frame.layout()
    tai_row = layout.getItemPosition(
        layout.indexOf(heatloss_panel._label_tai)
    )[0]
    qt_row = layout.getItemPosition(
        layout.indexOf(heatloss_panel._label_qt)
    )[0]
    assert tai_row == 3
    assert qt_row == 4

    shell = object.__new__(HeatLossPanelAdapter)
    results = {
        "room_totals": {"room-a": {"tai_C": 25.0}},
        "tai_C_by_room_id": {"room-a": 99.0},
    }
    assert shell._resolve_committed_tai_C(results, "room-a") == 25.0

    print(
        "OK — HL-S1C Environment checkbox projects Ti/tei intent and the "
        "conditional committed tai row between Qv and Qt."
    )


if __name__ == "__main__":
    main()
