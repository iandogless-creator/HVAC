from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.dev.test_hs40b_common_main_leg_entry_pipe_sizing_v1 import (
    COMMON_1_ID,
    COMMON_2_ID,
    ENTRY_1_ID,
    ENTRY_2_ID,
)
from HVAC.dev.test_hs42c_route_specific_main_pressure_accumulation_v1 import (
    _install_lengths,
    _project,
)
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    build_circuit_return_path_comparison_v1,
)


EXPECTED_IDS = {
    COMMON_1_ID,
    COMMON_2_ID,
    ENTRY_1_ID,
    ENTRY_2_ID,
}


def _display_rows(projection) -> list[dict]:
    adapter = object.__new__(HydronicsSchematicPanelAdapter)
    return adapter._build_return_path_comparison_rows(projection)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    project = _project()

    incomplete = build_circuit_return_path_comparison_v1(project)
    assert incomplete.rows
    assert all(row.direct_total_dp_Pa is None for row in incomplete.rows)
    assert all(
        row.reverse_return_total_dp_Pa is None
        for row in incomplete.rows
    )

    missing_ids = {
        section_id
        for row in incomplete.rows
        for section_id in row.missing_upstream_length_section_ids
    }
    assert missing_ids == EXPECTED_IDS
    assert all(
        "upstream physical length missing" in row.status
        for row in incomplete.rows
    )

    display_rows = _display_rows(incomplete)
    display_missing_ids = {
        section_id
        for row in display_rows
        for section_id in row["missing_upstream_length_section_ids"]
    }
    assert display_missing_ids == EXPECTED_IDS

    panel = HydronicsSchematicPanel()
    panel._proportioning_snapshot_return_comparison_rows = display_rows
    panel._set_return_arrangement_pressure_evidence_summary(
        display_rows,
        heading="System — pressure evidence (F&R)",
    )
    blocker_text = panel._return_arrangement_pressure_evidence_label.text()
    assert "F&R / F+RR pressure evidence blocked" in blocker_text
    assert "Enter Straight length in Local K / Fittings" in blocker_text
    assert "No default length assumed; return basis unchanged" in blocker_text
    for section_id in EXPECTED_IDS:
        assert section_id in blocker_text

    _install_lengths(project)
    complete = build_circuit_return_path_comparison_v1(project)
    assert complete.rows
    assert all(
        not row.missing_upstream_length_section_ids
        for row in complete.rows
    )
    assert all(row.direct_total_dp_Pa is not None for row in complete.rows)
    assert all(
        row.reverse_return_total_dp_Pa is not None
        for row in complete.rows
    )

    complete_display_rows = _display_rows(complete)
    panel._proportioning_snapshot_return_comparison_rows = (
        complete_display_rows
    )
    panel._set_return_arrangement_pressure_evidence_summary(
        complete_display_rows,
        heading="System — pressure evidence (F&R)",
    )
    complete_text = panel._return_arrangement_pressure_evidence_label.text()
    assert "pressure evidence blocked" not in complete_text
    assert "F&R controlling Δp:" in complete_text
    assert "F+RR controlling Δp:" in complete_text

    panel.close()
    app.processEvents()
    print(
        "OK — H-S51-D explicit missing upstream-length blockers passed."
    )


if __name__ == "__main__":
    main()
