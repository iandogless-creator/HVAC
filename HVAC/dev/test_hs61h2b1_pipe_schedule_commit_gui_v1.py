# ======================================================================
# H-S61-H2B1 — Confirmed pipe-schedule commit GUI action
# ======================================================================

from __future__ import annotations

import inspect
import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    panel = HydronicsSchematicPanel()
    commit_calls: list[bool] = []

    def _commit() -> bool:
        commit_calls.append(True)
        return True

    panel.set_proportioned_pipe_resizing_schedule_commit_callback_v1(
        _commit
    )
    panel.set_proportioned_pipe_resizing_schedule_acceptance_state_v1(
        evidence_ready=True,
        accepted=True,
        has_stored_acceptance=True,
        status="Ready — exact accepted material/size schedule",
    )
    panel.set_proportioned_pipe_resizing_schedule_commit_state_v1(
        ready=True,
        status="Ready — immutable committed-snapshot replacement prepared",
    )
    commit_button = (
        panel._proportioned_pipe_resizing_schedule_commit_button_v1
    )
    assert commit_button.isEnabled() is True
    assert "immutable" in commit_button.toolTip()

    with (
        patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.StandardButton.Yes,
        ),
        patch.object(QMessageBox, "information") as information,
    ):
        panel._on_proportioned_pipe_resizing_schedule_commit_v1()
    assert commit_calls == [True]
    information.assert_called_once()

    panel.set_proportioned_pipe_resizing_schedule_commit_state_v1(
        ready=False,
        status="Blocked — accepted schedule fingerprint is stale",
    )
    assert commit_button.isEnabled() is False
    assert "fingerprint is stale" in commit_button.toolTip()
    with patch.object(QMessageBox, "warning") as warning:
        panel._on_proportioned_pipe_resizing_schedule_commit_v1()
    warning.assert_called_once()
    assert commit_calls == [True]

    # Even a nominally ready GUI state must report an adapter-side recheck
    # failure; the panel never treats its cached display state as authority.
    panel.set_proportioned_pipe_resizing_schedule_commit_callback_v1(
        lambda: False
    )
    panel.set_proportioned_pipe_resizing_schedule_commit_state_v1(
        ready=True,
        status="Ready — replacement prepared",
    )
    with (
        patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.StandardButton.Yes,
        ),
        patch.object(QMessageBox, "warning") as warning,
    ):
        panel._on_proportioned_pipe_resizing_schedule_commit_v1()
    warning.assert_called_once()

    panel_source = inspect.getsource(HydronicsSchematicPanel)
    adapter_source = inspect.getsource(HydronicsSchematicPanelAdapter)
    handler_source = inspect.getsource(
        HydronicsSchematicPanel
        ._on_proportioned_pipe_resizing_schedule_commit_v1
    )
    assert "Commit accepted material/size schedule" in panel_source
    assert "generic-Kvs bases will be cleared" in panel_source
    assert "commit_proportioned_pipe_schedule_v1" in adapter_source
    assert (
        "set_proportioned_pipe_resizing_schedule_commit_state_v1"
        in adapter_source
    )
    # Documentation may name the adapter's ProjectState handoff. Guard
    # against actual panel-side state access or replacement authority instead.
    assert "self._project_state" not in handler_source
    assert "hydronic_" not in handler_source
    assert "replacement_snapshot" not in handler_source

    panel.close()
    print(
        "OK — H-S61-H2B1 confirmed pipe-schedule GUI commit action passed."
    )


if __name__ == "__main__":
    main()
