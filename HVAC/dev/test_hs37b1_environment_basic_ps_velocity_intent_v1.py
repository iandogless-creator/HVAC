# ======================================================================
# HVAC/dev/test_hs37b1_environment_basic_ps_velocity_intent_v1.py
# H-S37-B1 — Environment Basic PS maximum velocity intent/persistence
# ======================================================================

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.project.project_state import ProjectState


class _Context(QObject):
    environment_changed = Signal()

    def __init__(self, project_state: ProjectState) -> None:
        super().__init__()
        self.project_state = project_state


def main() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    default_environment = EnvironmentStateV1()
    assert default_environment.basic_ps_max_velocity_m_s == 1.0

    legacy_environment = EnvironmentStateV1.from_dict(
        {
            "design_flow_temp_c": 75.0,
            "design_return_temp_c": 65.0,
        }
    )
    assert legacy_environment.basic_ps_max_velocity_m_s == 1.0

    stored_environment = EnvironmentStateV1(
        basic_ps_max_velocity_m_s=1.15,
    )
    payload = stored_environment.to_dict()
    assert payload["basic_ps_max_velocity_m_s"] == 1.15
    restored_environment = EnvironmentStateV1.from_dict(payload)
    assert restored_environment.basic_ps_max_velocity_m_s == 1.15

    project = ProjectState(
        project_id="dev-hs37b1-environment-velocity",
        name="DEV H-S37-B1 Environment Velocity",
    )
    project.environment = restored_environment
    context = _Context(project)
    panel = EnvironmentPanel()
    adapter = EnvironmentPanelAdapter(context, panel)

    notifications: list[str] = []
    context.environment_changed.connect(
        lambda: notifications.append("environment_changed")
    )

    adapter.refresh()
    assert panel._basic_ps_max_velocity_input.value() == 1.15
    assert notifications == []

    panel._basic_ps_max_velocity_input.setValue(1.25)
    assert project.environment.basic_ps_max_velocity_m_s == 1.25
    assert notifications == ["environment_changed"]

    print(
        "OK — H-S37-B1 Environment Basic PS maximum velocity "
        "intent/persistence passed."
    )


if __name__ == "__main__":
    main()
