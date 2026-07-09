from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert 'self._make_tab("Proportioning Data")' in source
    assert 'self._make_tab("Proportioned")' in source

    assert "_clean_proportioned_tab" in source
    assert "_clean_proportioned_output_table" in source
    assert "Proportioned output summary — read-only" in source

    assert "Clean Proportioned output — summary only" in source
    assert "Proportioning Data" in source

    assert "def set_clean_proportioned_output_rows(" in source
    assert "_clean_proportioned_output_table" in source

    assert "def set_proportioned_status(" in source
    assert "set_clean_proportioned_output_rows(rows)" in source

    # Detailed evidence remains in the data tab/panel source.
    assert "Proportioned system — final output" in source
    assert "Valve authority preview — read-only" in source
    assert "_provisional_proportioning_burden_table" in source
    assert "_valve_authority_input_table" in source

    print("OK — H-S33-B clean Proportioned summary table passed.")


if __name__ == "__main__":
    main()
