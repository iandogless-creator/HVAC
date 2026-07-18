# ======================================================================
# HVAC/dev/test_hs38a2_grouped_scoped_rr_length_controls_v1.py
# H-S38-A2 — Grouped scoped RR length editor regression
# ======================================================================

from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    ReturnArrangementIntentV1,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()

    controls = panel._return_arrangement_scope_controls
    assert controls["SYSTEM"]["rr_basis_combo"] is (
        panel._rr_length_basis_mode_combo
    )
    assert controls["SYSTEM"]["rr_length_spin"] is (
        panel._rr_manual_extra_length_spin
    )

    for scope in ("LEG", "COMMON_SUBLEG", "BRANCH_SUBLEG"):
        control = controls[scope]
        basis_combo = control["rr_basis_combo"]
        assert basis_combo.findData("INHERIT") >= 0
        assert basis_combo.findData("physical_loop_zero_extra") >= 0
        assert basis_combo.findData("downstream_proxy") >= 0
        assert basis_combo.findData("manual_allowance") >= 0
        assert control["rr_length_spin"] is not None
        assert control["rr_status_label"] is not None

    leg_control = controls["LEG"]
    leg_control["combo"].clear()
    leg_control["combo"].addItem("Heating Leg 1", "leg-001")
    panel.set_scoped_rr_length_basis_overrides(
        leg_basis_modes={"leg-001": "manual_allowance"},
        leg_lengths_m={"leg-001": 6.25},
        subleg_basis_modes={},
        subleg_lengths_m={},
    )
    assert leg_control["rr_basis_combo"].currentData() == "manual_allowance"
    assert leg_control["rr_length_spin"].value() == 6.25

    captured: list[dict] = []
    panel.set_scoped_rr_length_basis_callback(captured.append)
    inherit_index = leg_control["rr_basis_combo"].findData("INHERIT")
    leg_control["rr_basis_combo"].setCurrentIndex(inherit_index)
    assert captured[-1]["scope"] == "LEG"
    assert captured[-1]["target_id"] == "leg-001"
    assert captured[-1]["basis_mode"] == "INHERIT"

    project = SimpleNamespace(
        hydronic_return_arrangement_intent=ReturnArrangementIntentV1(),
        dirty=False,
    )
    project.mark_dirty = lambda: setattr(project, "dirty", True)

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project
    adapter._return_arrangement_acceptance_intent = (
        project.hydronic_return_arrangement_intent
    )
    adapter.refresh = lambda: None

    adapter.set_scoped_rr_length_basis(
        {
            "scope": "LEG",
            "target_id": "leg-001",
            "basis_mode": "manual_allowance",
            "added_length_m": 7.5,
        }
    )
    intent = project.hydronic_return_arrangement_intent
    assert intent.leg_rr_added_length_basis_modes["leg-001"] == (
        "manual_allowance"
    )
    assert intent.leg_rr_added_lengths_m["leg-001"] == 7.5
    assert project.dirty is True

    adapter.set_scoped_rr_length_basis(
        {
            "scope": "LEG",
            "target_id": "leg-001",
            "basis_mode": "INHERIT",
            "added_length_m": 99.0,
        }
    )
    assert "leg-001" not in intent.leg_rr_added_length_basis_modes
    assert "leg-001" not in intent.leg_rr_added_lengths_m

    adapter.set_scoped_rr_length_basis(
        {
            "scope": "BRANCH_SUBLEG",
            "target_id": "leg-001-subleg-b",
            "parent_subleg_id": "leg-001-primary-subleg",
            "basis_mode": "downstream_proxy",
            "added_length_m": 3.0,
        }
    )
    assert intent.subleg_rr_added_length_basis_modes[
        "leg-001-subleg-b"
    ] == "downstream_proxy"
    assert intent.subleg_rr_added_lengths_m["leg-001-subleg-b"] == 3.0

    panel._return_arrangement_direct_radio.setChecked(True)
    panel._update_rr_manual_extra_length_enabled()
    assert panel._rr_length_basis_mode_combo.isEnabled() is False
    assert "dormant" in panel._rr_length_basis_status_label.text().lower()

    panel.close()
    app.processEvents()
    print("OK — H-S38-A2 grouped scoped RR length controls passed.")


if __name__ == "__main__":
    main()
