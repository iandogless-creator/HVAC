from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "_clean_proportioned_route_output_table" in source
    assert "Proportioned route output — read-only" in source

    assert '"Pipe DN"' in source
    assert '"Chosen Δp"' in source
    assert '"Added Δp"' in source
    assert '"Authority"' in source

    assert "def _configure_clean_proportioned_route_output_table_v1" in source
    assert "setAlternatingRowColors(True)" in source
    assert "setWordWrap(False)" in source
    assert "setColumnWidth" in source
    assert "setStretchLastSection(True)" in source

    assert "Clean Proportioned route output projection only" in source
    assert "not final hydraulics" in source
    assert "no valve product" in source
    assert "no Kv/Kvs" in source
    assert "no pump selection" in source
    assert "no pipe resizing" in source

    assert "self._configure_clean_proportioned_route_output_table_v1()" in source
    assert "self.set_clean_proportioned_route_output_rows([])" in source

    print("OK — H-S33-E clean route output column polish passed.")


if __name__ == "__main__":
    main()
