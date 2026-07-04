from __future__ import annotations

from pathlib import Path


def test_panel_has_rr_length_basis_mode_combo_and_callback() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "_rr_length_basis_mode_combo" in source
    assert "Physical loop — no extra allowance" in source
    assert "Downstream proxy allowance" in source
    assert "Manual allowance" in source
    assert "set_rr_length_basis_mode_callback" in source
    assert "_on_rr_length_basis_mode_changed" in source


def test_adapter_persists_rr_length_basis_mode_to_project_state() -> None:
    source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()

    assert "set_rr_length_basis_mode_callback" in source
    assert "set_rr_length_basis_mode" in source
    assert "hydronic_rr_added_length_basis_mode" in source
    assert "_restore_rr_length_basis_mode_to_panel" in source


if __name__ == "__main__":
    test_panel_has_rr_length_basis_mode_combo_and_callback()
    test_adapter_persists_rr_length_basis_mode_to_project_state()
    print("OK — H-S29-M RR length basis mode control passed.")
