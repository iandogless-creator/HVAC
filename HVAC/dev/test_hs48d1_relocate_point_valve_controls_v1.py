# ======================================================================
# H-S48-D1 — Relocate active point-valve evidence and controls
# ======================================================================

from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    start = source.index(
        "# H-S44-E — point allocation / method / valve-duty evidence"
    )
    end = source.index(
        "# H-S27-F — Chosen-basis proportioned readiness summary",
        start,
    )
    point_valve_section = source[start:end]

    assert "_balancing_point_evidence_table" in point_valve_section
    assert "Manual point Kvs candidate acceptance — design intent" in (
        point_valve_section
    )
    assert point_valve_section.count(
        "self._add_section(\n            proportioning_layout,"
    ) == 2
    assert "self._add_section(\n            proportioned_layout," not in (
        point_valve_section
    )

    print(
        "OK — H-S48-D1 active point-valve evidence and controls are in "
        "Proportioning."
    )


if __name__ == "__main__":
    main()
