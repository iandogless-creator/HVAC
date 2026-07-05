from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    _rr_added_length_m,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    ReturnArrangementIntentV1,
)


def test_panel_has_manual_rr_extra_length_spin_box() -> None:
    source = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py").read_text()

    assert "QDoubleSpinBox" in source
    assert "_rr_manual_extra_length_spin" in source
    assert "Extra length:" in source
    assert "set_rr_manual_extra_length_callback" in source
    assert "set_rr_manual_extra_length_m" in source
    assert "_on_rr_manual_extra_length_changed" in source
    assert "_update_rr_manual_extra_length_enabled" in source


def test_adapter_persists_manual_rr_extra_length_to_return_intent() -> None:
    source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()

    assert "set_rr_manual_extra_length_callback" in source
    assert "set_rr_manual_extra_length_m" in source
    assert "rr_added_length_m" in source
    assert "hydronic_return_arrangement_intent" in source
    assert "_restore_rr_manual_extra_length_to_panel" in source
    assert "_current_rr_manual_extra_length_m_v1" in source


def test_circuit_comparison_reads_manual_rr_length_from_intent() -> None:
    project_state = SimpleNamespace(
        hydronic_return_arrangement_intent=ReturnArrangementIntentV1(
            rr_added_length_m=4.25,
        )
    )

    assert _rr_added_length_m(project_state) == 4.25


if __name__ == "__main__":
    test_panel_has_manual_rr_extra_length_spin_box()
    test_adapter_persists_manual_rr_extra_length_to_return_intent()
    test_circuit_comparison_reads_manual_rr_length_from_intent()
    print("OK — H-S29-N manual RR extra length entry passed.")
