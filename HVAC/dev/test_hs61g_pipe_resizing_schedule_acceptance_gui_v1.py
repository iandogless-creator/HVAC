# ======================================================================
# H-S61-G — Explicit GUI acceptance and adapter persistence handoff
# ======================================================================

from __future__ import annotations

import inspect
import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from HVAC.dev.test_hs61f_proportioned_pipe_resizing_schedule_acceptance_v1 import (
    _projection,
    _reconciliation,
)
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.proportioned_pipe_resizing_schedule_acceptance_intent_v1 import (
    resolve_proportioned_pipe_resizing_schedule_acceptance_v1,
)
from HVAC.project.project_state import ProjectState


class _Signal:
    def __init__(self) -> None:
        self.emissions = 0

    def emit(self, *_args) -> None:
        self.emissions += 1


def main() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    panel = HydronicsSchematicPanel()
    payloads: list[dict] = []
    panel.set_proportioned_pipe_resizing_schedule_acceptance_callback_v1(
        payloads.append
    )
    panel.set_proportioned_pipe_resizing_schedule_acceptance_state_v1(
        evidence_ready=True,
        accepted=False,
        has_stored_acceptance=False,
        status="Pending — manual proposed DN schedule acceptance required",
    )
    assert (
        panel._proportioned_pipe_resizing_schedule_accept_button_v1.isEnabled()
        is True
    )
    assert (
        panel._proportioned_pipe_resizing_schedule_clear_button_v1.isEnabled()
        is False
    )

    with patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.StandardButton.Yes,
    ):
        panel._on_proportioned_pipe_resizing_schedule_accept_v1()
    assert payloads == [{"action": "accept"}]

    panel.set_proportioned_pipe_resizing_schedule_acceptance_state_v1(
        evidence_ready=True,
        accepted=True,
        has_stored_acceptance=True,
        status="Ready — manually accepted proposed DN schedule",
    )
    assert (
        panel._proportioned_pipe_resizing_schedule_accept_button_v1.isEnabled()
        is False
    )
    assert (
        panel._proportioned_pipe_resizing_schedule_clear_button_v1.isEnabled()
        is True
    )

    panel.set_proportioned_pipe_resizing_schedule_acceptance_state_v1(
        evidence_ready=True,
        accepted=False,
        has_stored_acceptance=True,
        status="Blocked — stale manual DN schedule acceptance",
    )
    assert (
        panel._proportioned_pipe_resizing_schedule_accept_button_v1.isEnabled()
        is True
    )
    assert (
        panel._proportioned_pipe_resizing_schedule_clear_button_v1.isEnabled()
        is True
    )
    assert "stale" in (
        panel._proportioned_pipe_resizing_schedule_acceptance_status_v1
        .text()
        .lower()
    )

    projection = _projection()
    reconciliation = _reconciliation()
    project = ProjectState(project_id="hs61g", name="H-S61-G")
    signal = _Signal()
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project
    adapter._context = SimpleNamespace(project_state_changed=signal)
    adapter._proportioned_pipe_resizing_hydraulic_projection_v1 = projection
    adapter._resized_balancing_point_reconciliation_v1 = reconciliation
    refreshes: list[bool] = []
    adapter.refresh = lambda: refreshes.append(True)

    adapter.set_proportioned_pipe_resizing_schedule_acceptance_v1(
        {"action": "accept"}
    )
    intent = (
        project
        .hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
    )
    assert intent is not None
    assert intent.accepted_schedule is not None
    resolved = resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent,
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert resolved.ready is True, resolved.status
    assert resolved.accepted is True
    assert refreshes == [True]
    assert signal.emissions == 1

    adapter.set_proportioned_pipe_resizing_schedule_acceptance_v1(
        {"action": "clear"}
    )
    assert intent.accepted_schedule is None
    assert refreshes == [True, True]
    assert signal.emissions == 2

    panel_source = inspect.getsource(HydronicsSchematicPanel)
    adapter_source = inspect.getsource(HydronicsSchematicPanelAdapter)
    assert "Accept proposed DN schedule" in panel_source
    assert "Clear acceptance" in panel_source
    assert "QMessageBox.question(" in panel_source
    assert "Current committed" in panel_source
    assert "DNs remain unchanged" in panel_source
    assert (
        "set_proportioned_pipe_resizing_schedule_acceptance_callback_v1"
        in adapter_source
    )
    assert (
        "resolve_proportioned_pipe_resizing_schedule_acceptance_v1("
        in adapter_source
    )
    accept_handler_source = inspect.getsource(
        HydronicsSchematicPanel
        ._on_proportioned_pipe_resizing_schedule_accept_v1
    )
    assert "ProjectState" not in accept_handler_source
    assert "accepted_dn" not in accept_handler_source

    panel.close()
    print(
        "OK — H-S61-G proposed DN schedule GUI acceptance and "
        "persistence handoff passed."
    )


if __name__ == "__main__":
    main()
