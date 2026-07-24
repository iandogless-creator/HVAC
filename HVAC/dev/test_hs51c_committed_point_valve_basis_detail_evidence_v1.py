from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def main() -> None:
    snapshot = SimpleNamespace(
        committed_point_valve_bases=(
            SimpleNamespace(
                balancing_point_id="balancing-point:main:leg-002",
                accepted_kvs_basis=6.3,
                disposition="approved_for_product_search",
            ),
            SimpleNamespace(
                balancing_point_id=(
                    "balancing-point:subleg:leg-002-primary-subleg:"
                    "downstream-exclusive"
                ),
                accepted_kvs_basis=10.0,
                disposition="approved_for_product_search",
            ),
        )
    )

    rows = (
        HydronicsSchematicPanelAdapter
        ._build_committed_point_valve_basis_detail_rows_v1(snapshot)
    )
    assert [row["accepted_kvs"] for row in rows] == ["6.300", "10.000"]
    assert rows[0]["balancing_point_id"] == (
        "balancing-point:main:leg-002"
    )
    assert rows[0]["disposition"] == (
        "Approved for later product search"
    )
    assert all(
        row["status"]
        == "Committed basis only — no valve product selected"
        for row in rows
    )
    assert (
        HydronicsSchematicPanelAdapter
        ._build_committed_point_valve_basis_detail_rows_v1(None)
        == []
    )

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    snapshot_source = Path(
        "HVAC/hydronics/proportioning/proportioned_basis_snapshot_v1.py"
    ).read_text(encoding="utf-8")

    assert "Committed point-valve basis detail — read-only" in panel_source
    assert "set_committed_point_valve_basis_detail_rows" in panel_source
    assert (
        "Not committed — point-valve basis remains in "
        "Proportioning preview"
    ) in panel_source
    assert "_build_committed_point_valve_basis_detail_rows_v1" in adapter_source
    assert '"hydronic_proportioned_basis_snapshot"' in adapter_source
    assert '"committed_point_valve_bases"' in adapter_source
    assert "catalog_id" not in (
        adapter_source[
            adapter_source.index(
                "def _build_committed_point_valve_basis_detail_rows_v1"
            ):
            adapter_source.index(
                "def _build_proportioned_output_status_rows_v1"
            )
        ]
    )
    assert "class CommittedPointValveBasisV1" in snapshot_source
    assert "accepted_kvs_basis: float" in snapshot_source

    print(
        "OK — H-S51-C committed point-valve basis detail evidence passed."
    )


if __name__ == "__main__":
    main()
