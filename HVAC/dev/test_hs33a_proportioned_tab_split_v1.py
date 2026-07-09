from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert 'self._make_tab("Proportioning Data")' in source
    assert 'self._make_tab("Proportioned")' in source

    assert "_proportioning_data_tab" in source
    assert "_clean_proportioned_tab" in source
    assert "self._proportioned_tab = self._proportioning_data_tab" in source

    assert "Clean Proportioned output shell" in source
    assert "Proportioning Data" in source

    # Existing evidence stack remains present.
    assert "Proportioned system — final output" in source
    assert "Valve authority preview — read-only" in source
    assert "_provisional_proportioning_burden_table" in source
    assert "_valve_authority_input_table" in source

    print("OK — H-S33-A Proportioned tab split passed.")


if __name__ == "__main__":
    main()
