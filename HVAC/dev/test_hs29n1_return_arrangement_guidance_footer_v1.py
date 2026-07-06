from __future__ import annotations

from pathlib import Path


def test_return_arrangement_footer_says_evidence_is_guidance() -> None:
    source = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py").read_text()

    assert "Evidence is guidance only" in source
    assert "user design basis remains authoritative" in source
    assert "No pump, valve, balancing, or pipe resizing." in source


if __name__ == "__main__":
    test_return_arrangement_footer_says_evidence_is_guidance()
    print("OK — H-S29-N1 return-arrangement guidance footer passed.")
