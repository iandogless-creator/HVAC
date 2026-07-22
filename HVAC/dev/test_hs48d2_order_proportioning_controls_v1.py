from pathlib import Path


def main() -> None:
    panel_path = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py")
    source = panel_path.read_text()

    helper_start = source.index("    def _add_section(")
    helper_end = source.index("    def _fit_table_height(", helper_start)
    helper = source[helper_start:helper_end]

    assert "H-S48-D2" in helper
    assert 'layout is getattr(self, "_proportioning_tab", None)' in helper
    assert '"Return arrangement acceptance — user design basis": 100' in helper
    assert '"Local section maximum velocity — authority editor": 200' in helper
    assert '"read-only"\n                ): 900' in helper
    assert '"Manual point Kvs candidate acceptance — design intent"' in helper
    assert "): 1000" in helper
    assert ".get(title, 500)" in helper
    assert "layout.insertWidget(insert_index, section)" in helper
    assert "layout.addWidget(section)" in helper
    assert "return section" in helper

    # Presentation-only: no controller, adapter, hydraulics or persistence.
    assert "ProjectState" not in helper
    assert "mark_dirty" not in helper
    assert "accepted_kvs" not in helper
    assert "design_valve_dp_pa" not in helper

    print(
        "OK — H-S48-D2 Proportioning controls ordered by hydraulic "
        "dependency."
    )


if __name__ == "__main__":
    main()
