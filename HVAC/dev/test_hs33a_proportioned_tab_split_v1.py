from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "Proportioning Data" in source
    assert '"Proportioned"' in source or "'Proportioned'" in source

    assert "_clean_proportioned_tab" in source
    assert "Clean Proportioned output shell" in source

    assert "detailed route, " in source
    assert "Proportioning Data" in source

    assert "Valve authority preview — read-only" in source
    assert "Proportioned system — final output" in source

    # H-S33-A is layout only. Evidence tables should still exist.
    assert "_valve_authority_input_table" in source
    assert "_provisional_proportioning_burden_table" in source

    print("OK — H-S33-A Proportioned tab split passed.")


if __name__ == "__main__":
    main()
