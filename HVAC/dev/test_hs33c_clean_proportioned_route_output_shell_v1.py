from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert 'self._make_tab("Proportioning Data")' in source
    assert 'self._make_tab("Proportioned")' in source

    assert "_clean_proportioned_output_table" in source
    assert "_clean_proportioned_route_output_table" in source

    assert "Proportioned output summary — read-only" in source
    assert "Proportioned route output — read-only" in source

    assert '"Route"' in source
    assert '"Basis"' in source
    assert '"Sections"' in source
    assert '"Flow kg/s"' in source
    assert '"Pipe DN"' in source
    assert '"Δp/m"' in source
    assert '"Chosen Δp"' in source
    assert '"Added Δp"' in source
    assert '"Authority"' in source
    assert '"Status"' in source

    assert "def set_clean_proportioned_route_output_rows(" in source
    assert "Waiting for clean Proportioned route output " in source
    assert "projection" in source
    assert "self.set_clean_proportioned_route_output_rows([])" in source

    # Detailed evidence still remains elsewhere.
    assert "Valve authority preview — read-only" in source
    assert "_provisional_proportioning_burden_table" in source
    assert "_valve_authority_input_table" in source

    print("OK — H-S33-C clean Proportioned route output shell passed.")


if __name__ == "__main__":
    main()
