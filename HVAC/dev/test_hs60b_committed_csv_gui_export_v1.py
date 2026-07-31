# ======================================================================
# H-S60-B — Committed CSV GUI export handoff test
# ======================================================================

from __future__ import annotations

import inspect
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_export_payload_v1 import (
    CommittedProportionedSystemExportPayloadV1,
)


def _payload():
    return CommittedProportionedSystemExportPayloadV1(
        ready=True,
        status="Ready",
        source_package_schema=(
            "committed_proportioned_system_result_package_v1"
        ),
        accepted_return_arrangement_basis="DIRECT_RETURN",
        summary={"route_count": 1},
        committed_route_results=({"route_id": "route-a"},),
        committed_balancing_point_results=(
            {"balancing_point_id": "point-a"},
        ),
        committed_route_point_reconciliation=(
            {"committed_route_id": "route-a"},
        ),
        committed_section_results=(
            {
                "committed_route_id": "route-a",
                "section_id": "section-a",
            },
        ),
    )


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._committed_proportioned_system_export_payload_v1 = _payload()

    with TemporaryDirectory() as temporary_text:
        temporary = Path(temporary_text)
        destination = temporary / "Proportioned CSV"
        result = adapter._write_committed_proportioned_csv_bundle_v1(
            destination
        )
        assert result.ready is True, result.status
        assert Path(result.destination_directory) == destination
        assert len(result.files) == 5

        existing = adapter._write_committed_proportioned_csv_bundle_v1(
            destination
        )
        assert existing.ready is False
        assert "will not overwrite" in existing.status

    blocked_adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    blocked_adapter._committed_proportioned_system_export_payload_v1 = None
    with TemporaryDirectory() as temporary_text:
        blocked = blocked_adapter._write_committed_proportioned_csv_bundle_v1(
            Path(temporary_text) / "blocked"
        )
        assert blocked.ready is False
        assert "H-S59-B" in blocked.status

    adapter_source = inspect.getsource(HydronicsSchematicPanelAdapter)
    panel_source = inspect.getsource(HydronicsSchematicPanel)

    assert "write_committed_proportioned_csv_bundle_v1(" in adapter_source
    assert "set_committed_proportioned_csv_export_handler_v1(" in (
        adapter_source
    )
    assert "set_committed_proportioned_csv_export_ready_v1(" in (
        adapter_source
    )
    assert "Export committed CSV bundle…" in panel_source
    assert "QFileDialog.getExistingDirectory(" in panel_source
    assert "QInputDialog.getText(" in panel_source
    assert "Path(folder_name).name != folder_name" in panel_source
    assert "Committed CSV export complete" in panel_source
    assert "Committed CSV export blocked" in panel_source
    assert "write_committed_proportioned_csv_bundle_v1(" not in panel_source
    assert "hydronic_proportioned_basis_snapshot" not in inspect.getsource(
        HydronicsSchematicPanel._on_committed_proportioned_csv_export_clicked_v1
    )

    print("OK — H-S60-B committed CSV GUI export handoff passed.")


if __name__ == "__main__":
    main()
