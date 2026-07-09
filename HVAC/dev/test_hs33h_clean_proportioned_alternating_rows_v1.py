from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "_clean_proportioned_output_table" in source
    assert "_clean_proportioned_route_output_table" in source

    assert "def _configure_clean_proportioned_output_summary_table_v1" in source
    assert "def _configure_clean_proportioned_route_output_table_v1" in source

    assert source.count("setAlternatingRowColors(True)") >= 2

    assert "Clean Proportioned output summary" in source
    assert "Clean Proportioned route output projection only" in source

    assert "self._configure_clean_proportioned_output_summary_table_v1()" in source
    assert "self._configure_clean_proportioned_route_output_table_v1()" in source

    print("OK — H-S33-H clean Proportioned alternating rows passed.")


if __name__ == "__main__":
    main()
