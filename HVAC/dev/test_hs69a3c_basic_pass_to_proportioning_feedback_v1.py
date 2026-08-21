from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import HVAC.gui_v3.adapters.basic_hydronics_panel_adapter as adapter_module
from HVAC.gui_v3.adapters.basic_hydronics_panel_adapter import (
    BasicHydronicsPanelAdapter,
)
from HVAC.gui_v3.panels.basic_hydronics_panel import BasicHydronicsPanel


class PanelSpy:
    def __init__(self) -> None:
        self.statuses: list[tuple[str, bool]] = []

    def set_handoff_status(
            self,
            message: str,
            *,
            success: bool = False,
    ) -> None:
        self.statuses.append((message, success))


class SignalSpy:
    def __init__(self) -> None:
        self.values: list[str] = []

    def emit(self, value: str) -> None:
        self.values.append(value)


class ContextStub:
    def __init__(self, project) -> None:
        self.project_state = project
        self.room_state_changed = SignalSpy()
        self.navigation_payloads: list[dict] = []

    def request_pass_to_proportioning(self, payload: dict) -> None:
        self.navigation_payloads.append(dict(payload))


def main() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app

    widget = BasicHydronicsPanel()
    widget.set_handoff_status(
        "Cannot pass to Proportioning.\nChoose another index room."
    )
    assert not widget._handoff_status.isHidden()
    assert widget._handoff_status.text().count("\n") == 1
    assert "#9b3a24" in widget._handoff_status.styleSheet().lower()
    widget.set_handoff_status("Passed.", success=True)
    assert "#2e7d32" in widget._handoff_status.styleSheet().lower()

    project = SimpleNamespace(
        rooms={
            "room-source": SimpleNamespace(name="Heat Source room"),
            "room-index": SimpleNamespace(name="Index room"),
        },
        hydronic_topology=SimpleNamespace(
            heat_source_room_id="room-source"
        ),
    )
    panel = PanelSpy()
    context = ContextStub(project)
    adapter = BasicHydronicsPanelAdapter.__new__(
        BasicHydronicsPanelAdapter
    )
    adapter._panel = panel
    adapter._context = context
    refreshes = {"count": 0}
    adapter.refresh = lambda: refreshes.__setitem__(
        "count", refreshes["count"] + 1
    )

    apply_calls: list[dict] = []

    def fake_apply(_project, payload, **_kwargs):
        apply_calls.append(dict(payload))
        return SimpleNamespace(index_room_id=payload["index_room_id"])

    adapter_module.apply_basic_hydronic_sizing_payload_v1 = fake_apply

    adapter._on_pass_to_proportioning_requested(
        {"index_room_id": "room-source"}
    )
    blocked_message, blocked_success = panel.statuses[-1]
    assert "Cannot pass" in blocked_message
    assert "Heat Source" in blocked_message
    assert "Choose another index room" in blocked_message
    assert not blocked_success
    assert apply_calls == []
    assert context.navigation_payloads == []
    assert refreshes["count"] == 0

    adapter._on_pass_to_proportioning_requested(
        {"index_room_id": "room-index"}
    )
    assert apply_calls == [{"index_room_id": "room-index"}]
    assert context.room_state_changed.values == ["room-index"]
    assert context.navigation_payloads == [
        {"index_room_id": "room-index"}
    ]
    assert refreshes["count"] == 1
    assert panel.statuses[-1] == (
        "Basic intent passed to Proportioning.",
        True,
    )

    print(
        "OK — H-S69-A3C shows a concise Heat Source/index blocker, "
        "prevents blocked mutation/navigation and retains the valid "
        "Basic-to-Proportioning handoff."
    )


if __name__ == "__main__":
    main()
