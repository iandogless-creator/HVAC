# ======================================================================
# H-S54-B — Commit Proportioning hydraulic-authority handoff
# ======================================================================

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)
from HVAC.hydronics.proportioning import proportioned_basis_snapshot_v1 as snapshot_module


class _Button:
    def __init__(self):
        self.text_value = ""
        self.tooltip = ""

    def setText(self, value):
        self.text_value = str(value)

    def setToolTip(self, value):
        self.tooltip = str(value)


class _Label:
    def __init__(self):
        self.text_value = ""

    def setText(self, value):
        self.text_value = str(value)


def main() -> None:
    authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        status="Ready — committed hydraulic authority",
    )
    readiness = SimpleNamespace(
        return_arrangement_basis_ready=True,
        return_arrangement_basis_label="F&R",
        return_arrangement_basis_status="Accepted",
        index_room_id="room-index",
        index_room_label="Index",
        terminal_room_id="room-index",
        terminal_room_label="Index",
        terminal_alignment_status="Aligned",
        basis_mode="direct",
        total_index_length_label="20.0 m",
        nominal_gradient_label="200 Pa/m",
    )
    original = snapshot_module.build_proportioning_readiness_v1
    snapshot_module.build_proportioning_readiness_v1 = lambda project: readiness
    try:
        result = snapshot_module.build_proportioned_basis_snapshot_v1(
            object(),
            hydraulic_input_authority=authority,
        )
    finally:
        snapshot_module.build_proportioning_readiness_v1 = original

    assert result.ready is True, result.status
    assert result.snapshot is not None
    assert result.snapshot.hydraulic_input_authority is authority
    assert result.snapshot.hydraulic_input_authority_status == authority.status

    blocked_authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=False,
        blockers=("Missing section length",),
        status="Blocked — Missing section length",
    )
    snapshot_module.build_proportioning_readiness_v1 = lambda project: readiness
    try:
        blocked = snapshot_module.build_proportioned_basis_snapshot_v1(
            object(),
            hydraulic_input_authority=blocked_authority,
        )
    finally:
        snapshot_module.build_proportioning_readiness_v1 = original
    assert blocked.ready is False
    assert "Missing section length" in blocked.status

    panel_stub = SimpleNamespace(
        _commit_proportioning_button=_Button(),
        _return_arrangement_acceptance_status_label=_Label(),
    )
    HydronicsSchematicPanel.set_commit_proportioning_committed(
        panel_stub,
        committed=True,
    )
    assert panel_stub._commit_proportioning_button.text_value == (
        "Recommit Proportioning"
    )
    assert "hydraulic basis is committed" in (
        panel_stub._return_arrangement_acceptance_status_label.text_value
    )

    HydronicsSchematicPanel.set_commit_proportioning_committed(
        panel_stub,
        committed=False,
    )
    assert panel_stub._commit_proportioning_button.text_value == (
        "Commit Proportioning"
    )

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_committed_proportioning_hydraulic_input_authority_v1("
        in adapter_source
    )
    assert "_committed_hydraulic_route_pressure_projection_v1" in (
        adapter_source
    )
    assert "_committed_hydraulic_chosen_controlling_rows_v1" in (
        adapter_source
    )
    assert "_committed_hydraulic_resistance_basis_v1" in adapter_source
    assert "hydraulic_input_authority=hydraulic_input_authority" in (
        adapter_source
    )
    assert "set_commit_proportioning_committed" in adapter_source
    assert "Recommit Proportioning" in panel_source
    assert "Proportioning hydraulic basis is committed" in panel_source

    print(
        "OK — H-S54-B Commit Proportioning hydraulic-authority "
        "handoff passed."
    )


if __name__ == "__main__":
    main()
