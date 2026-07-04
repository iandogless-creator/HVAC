from __future__ import annotations

from pathlib import Path


def test_return_acceptance_uses_rr_length_basis_wording() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "RR length basis:" in source
    assert "RR extra length:" in source
    assert "RR extra Δp:" in source
    assert "RR pipe allowance:" not in source
    assert "_return_arrangement_rr_length_evidence_summary" in source


if __name__ == "__main__":
    test_return_acceptance_uses_rr_length_basis_wording()
    print("OK — H-S29-L RR length basis visible in return acceptance.")
