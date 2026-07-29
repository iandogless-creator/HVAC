# ======================================================================
# H-S56-D — Committed point reconciliation in the Proportioned UI
# ======================================================================

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def _point(
    point_id,
    routes,
    allocated,
    flow,
    *,
    shared=False,
    exclusive=False,
    duty=True,
    kvs=None,
):
    return SimpleNamespace(
        balancing_point_id=point_id,
        point_scope="main" if shared else "subleg",
        point_role=(
            "common_main_takeoff" if shared else "downstream-exclusive"
        ),
        downstream_route_ids=routes,
        is_shared=shared,
        is_route_exclusive=exclusive,
        point_flow_kg_s=flow,
        allocated_added_dp_pa=allocated,
        allocated_resistance_pa_per_kg_s2=(
            allocated / (flow ** 2) if flow else None
        ),
        valve_duty_required=duty,
        accepted_kvs_basis=kvs,
        reconciled=True,
        status=(
            "Ready — committed point allocation and generic-Kvs basis "
            "reconciled"
            if duty
            else "Ready — no positive point allocation or valve duty"
        ),
    )


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    result = SimpleNamespace(
        ready=True,
        status="Ready — 3 committed balancing points reconciled",
        point_rows=(
            _point(
                "point-shared",
                ("route-one", "route-two"),
                200.0,
                0.20,
                shared=True,
                kvs=6.3,
            ),
            _point(
                "point-route-one",
                ("route-one",),
                100.0,
                0.10,
                exclusive=True,
                kvs=4.0,
            ),
            _point(
                "point-control",
                ("route-control",),
                -0.0,
                0.08,
                exclusive=True,
                duty=False,
            ),
        ),
    )
    rows = adapter._build_committed_point_balancing_reconciliation_rows_v1(
        result
    )
    assert len(rows) == 3
    assert rows[0]["balancing_point_id"] == "point-shared"
    assert rows[0]["scope"] == "Main · shared"
    assert rows[0]["governed_routes"] == "route-one, route-two"
    assert rows[0]["flow_kg_s"] == "0.2000"
    assert rows[0]["allocated_dp"] == "200.0 Pa"
    assert rows[0]["resistance"] == "5000.0 Pa/(kg/s)²"
    assert rows[0]["accepted_kvs"] == "6.300"
    assert rows[0]["reconciled"] == "Yes"
    assert rows[2]["allocated_dp"] == "0.0 Pa"
    assert rows[2]["accepted_kvs"] == "—"

    blocked = adapter._build_committed_point_balancing_reconciliation_rows_v1(
        SimpleNamespace(
            ready=False,
            status="Blocked — committed point authority required",
            point_rows=(),
        )
    )
    assert len(blocked) == 1
    assert blocked[0]["reconciled"] == "No"
    assert blocked[0]["status"].startswith("Blocked")

    adapter._build_preview_proportioned_output_status_rows_v1 = (
        lambda **_kwargs: []
    )
    adapter._committed_basis_route_proportioning_result_v1 = (
        SimpleNamespace(status="Ready — committed route result")
    )
    adapter._committed_point_level_balancing_reconciliation_v1 = result
    summary = adapter._build_proportioned_output_status_rows_v1(
        resolution=None,
        chosen_preview_rows=[],
        chosen_controlling_rows=[],
        readiness_rows=[],
    )
    assert summary[-1]["item"] == "Committed point reconciliation"
    assert "3 committed balancing points" in summary[-1]["status"]

    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    table = panel._committed_point_balancing_reconciliation_table
    headers = [
        table.horizontalHeaderItem(index).text()
        for index in range(table.columnCount())
    ]
    assert headers == [
        "Balancing point",
        "Scope",
        "Governed routes",
        "Flow kg/s",
        "Allocated Δp",
        "Resistance",
        "Generic Kvs",
        "Reconciled",
        "Status",
    ]
    panel.set_committed_point_balancing_reconciliation_rows(rows)
    assert table.item(0, 0).text() == "point-shared"
    assert table.item(0, 4).text() == "200.0 Pa"
    assert table.item(2, 6).text() == "—"
    assert table.item(2, 7).text() == "Yes"
    panel.close()

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_committed_point_level_balancing_reconciliation_v1("
        in adapter_source
    )
    assert (
        "set_committed_point_balancing_reconciliation_rows("
        in adapter_source
    )
    assert "Committed point reconciliation" in adapter_source
    assert (
        "Committed point-level balancing reconciliation — read-only"
        in panel_source
    )
    assert "_committed_point_balancing_reconciliation_table" in panel_source

    print(
        "OK — H-S56-D committed point reconciliation Proportioned UI passed."
    )


if __name__ == "__main__":
    main()
