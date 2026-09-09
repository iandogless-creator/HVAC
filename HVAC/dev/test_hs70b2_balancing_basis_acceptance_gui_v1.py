from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from HVAC.dev.test_hs70a_balancing_completion_readiness_v1 import (
    POINT_CONTROL,
    POINT_DUTY,
    _snapshot,
    _topology,
)
from HVAC.gui_v3.adapters import hydronics_schematic_panel_adapter as module
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.balancing_completion_basis_acceptance_intent_v1 import (
    resolve_balancing_completion_basis_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_completion_readiness_v1 import (
    build_balancing_completion_readiness_v1,
)
from HVAC.project.project_state import ProjectState


class _Signal:
    def __init__(self) -> None:
        self.count = 0

    def emit(self, *_args) -> None:
        self.count += 1


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    calls: list[dict] = []
    panel.set_balancing_completion_basis_acceptance_callback_v1(calls.append)

    panel.set_balancing_completion_basis_rows_v1(
        [],
        readiness_ready=False,
        accepted_ready=False,
        has_acceptance=False,
        status="Blocked",
        blockers=("Exact blocker",),
    )
    assert not panel._balancing_completion_basis_accept_button.isEnabled()
    assert not panel._balancing_completion_basis_clear_button.isEnabled()
    assert "Exact blocker" in (
        panel._balancing_completion_basis_status_label.text()
    )

    rows = [{
        "balancing_point_id": POINT_DUTY,
        "duty": "Added resistance",
        "required_method": "Proportional Added Resistance",
        "committed_kvs": "1.6",
        "accepted": "No",
        "status": "Pending",
        "blockers": "—",
    }]
    panel.set_balancing_completion_basis_rows_v1(
        rows,
        readiness_ready=True,
        accepted_ready=False,
        has_acceptance=False,
        status="Ready for explicit acceptance",
        blockers=(),
    )
    assert panel._balancing_completion_basis_accept_button.isEnabled()
    item = panel._balancing_completion_basis_table.item(0, 3)
    assert item.text() == "1.6"
    assert not bool(item.flags() & Qt.ItemIsEditable)
    panel._balancing_completion_basis_accept_button.click()
    assert calls == [{"action": "accept"}]

    project = ProjectState(project_id="hs70b2", name="H-S70-B2")
    snapshot = _snapshot()
    topology = _topology()
    project.hydronic_proportioned_basis_snapshot = snapshot
    context = SimpleNamespace(
        project_state_changed=_Signal(),
        project_changed=_Signal(),
    )
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project
    adapter._context = context
    adapter._panel = panel
    adapter.refresh = lambda: None

    original_topology_builder = (
        module.build_balancing_point_topology_authority_v1
    )
    module.build_balancing_point_topology_authority_v1 = lambda _project: topology
    try:
        adapter.set_balancing_completion_basis_acceptance_v1(
            {"action": "accept"}
        )
        intent = (
            project.hydronic_balancing_completion_basis_acceptance_intent
        )
        assert set(intent.accepted_by_point_id) == {
            POINT_DUTY,
            POINT_CONTROL,
        }
        readiness = build_balancing_completion_readiness_v1(
            snapshot=snapshot,
            topology=topology,
        )
        resolved = resolve_balancing_completion_basis_acceptance_v1(
            intent=intent,
            readiness=readiness,
            snapshot=snapshot,
        )
        assert resolved.ready is True, resolved.status
        assert project.hydronics_valid is False
        assert context.project_state_changed.count == 1
        assert context.project_changed.count == 1

        adapter.set_balancing_completion_basis_acceptance_v1(
            {"action": "clear"}
        )
        assert (
            project.hydronic_balancing_completion_basis_acceptance_intent
            is None
        )
    finally:
        module.build_balancing_point_topology_authority_v1 = (
            original_topology_builder
        )
        panel.close()
        app.processEvents()

    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    b2_panel_start = panel_source.index(
        "    def set_balancing_completion_basis_acceptance_callback_v1"
    )
    b2_panel_end = panel_source.index(
        "    def set_balancing_point_evidence_rows(",
        b2_panel_start,
    )
    b2_panel_source = panel_source[b2_panel_start:b2_panel_end]
    assert "ProjectState" not in b2_panel_source
    assert "hydronic_balancing_completion" not in b2_panel_source
    adapter_source_lower = adapter_source.lower()
    assert "no valve product" in adapter_source_lower
    assert "pump duty" in adapter_source_lower
    assert "build_balancing_completion_readiness_v1" in adapter_source
    assert "build_balancing_completion_basis_fingerprint_v1" in adapter_source

    print(
        "OK — H-S70-B2 presents current point method/Kvs acceptance evidence, "
        "gates one system-level acceptance on H-S70-A, persists only B1 intent "
        "through the adapter and introduces no valve-product or pump authority."
    )


if __name__ == "__main__":
    main()
