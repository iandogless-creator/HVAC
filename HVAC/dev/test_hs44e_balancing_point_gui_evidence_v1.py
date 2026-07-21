from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegBalancingPointEvidenceV1,
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicV1,
    CommonMainLegSublegSchematicWidgetV1,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    adapter = object.__new__(HydronicsSchematicPanelAdapter)
    mapping = SimpleNamespace(
        rows=(
            SimpleNamespace(
                balancing_point_id="balancing-point:main:leg-001",
                point_scope="main",
                point_role="common_main_takeoff",
                label="Common main take-off to Leg 1",
                downstream_route_ids=("route-a", "route-b"),
                is_shared=True,
                is_route_exclusive=False,
                point_flow_kg_s=0.30,
                design_valve_dp_pa=90.0,
                candidate_resistance_pa_per_kg_s2=1000.0,
                balancing_method_label="Proportional added resistance",
                authority_label="Valve authority input available",
                controlled_circuit_dp_pa=None,
                authority=None,
                ready=True,
                status="Input available — shared point duty",
                blockers=(),
            ),
            SimpleNamespace(
                balancing_point_id="balancing-point:leg:leg-001",
                point_scope="leg",
                point_role="leg_entry",
                label="Leg 1 entry",
                downstream_route_ids=("route-a", "route-b"),
                is_shared=True,
                is_route_exclusive=False,
                point_flow_kg_s=0.20,
                design_valve_dp_pa=40.0,
                candidate_resistance_pa_per_kg_s2=1000.0,
                balancing_method_label="Proportional added resistance",
                authority_label="Valve authority input available",
                controlled_circuit_dp_pa=None,
                authority=None,
                ready=True,
                status="Input available — shared point duty",
                blockers=(),
            ),
            SimpleNamespace(
                balancing_point_id="balancing-point:subleg:leg-001-subleg-b",
                point_scope="subleg",
                point_role="branch",
                label="Subleg 1B",
                downstream_route_ids=("route-b",),
                is_shared=False,
                is_route_exclusive=True,
                point_flow_kg_s=0.10,
                design_valve_dp_pa=50.0,
                candidate_resistance_pa_per_kg_s2=5000.0,
                balancing_method_label="Proportional added resistance",
                authority_label="Valve authority input available",
                controlled_circuit_dp_pa=None,
                authority=None,
                ready=True,
                status="Input available — route-exclusive point duty",
                blockers=(),
            ),
        )
    )
    rows = adapter._build_balancing_point_gui_rows_v1(mapping)
    assert len(rows) == 3
    assert rows[0]["topology"] == "Shared"
    assert rows[0]["target_id"] == "common_main"
    assert rows[1]["target_id"] == "leg-001"
    assert rows[2]["target_id"] == "leg-001-subleg-b"
    assert rows[2]["topology"] == "Route-exclusive"
    assert rows[2]["allocated_dp"] == "50.0 Pa"
    assert rows[2]["controlled_dp"] == "—"
    assert rows[2]["authority"] == "—"

    evidence = adapter._build_schematic_balancing_point_evidence_v1(mapping)
    assert len(evidence) == 3
    assert evidence[0].governed_routes == "route-a, route-b"

    schematic = CommonMainLegSublegSchematicV1(
        common_main_label="Common main",
        routes=(
            CommonMainLegSublegRouteV1(
                leg_id="leg-001",
                leg_label="Leg 1",
                subleg_id="leg-001-subleg-b",
                subleg_label="Subleg 1B",
                role="Branch",
                room_labels=("room-001",),
            ),
        ),
        balancing_point_evidence=evidence,
        status="Read-only",
    )
    widget = CommonMainLegSublegSchematicWidgetV1()
    widget.set_schematic(schematic)
    common_text = widget._hierarchy_tooltip_text_v1(
        "common_main", "common_main"
    )
    leg_text = widget._hierarchy_tooltip_text_v1("leg", "leg-001")
    subleg_text = widget._hierarchy_tooltip_text_v1(
        "subleg", "leg-001-subleg-b"
    )
    assert "Common main take-off to Leg 1" in common_text
    assert "Topology: Shared" in common_text
    assert "Allocated Δp: 90.0 Pa" in common_text
    assert "Point: Leg 1 entry" in leg_text
    assert "Valve duty: Valve authority input available" in leg_text
    assert "Controlled circuit Δp: —" in leg_text
    assert "Point: Subleg 1B" in subleg_text
    assert "Topology: Route-exclusive" in subleg_text
    assert "Governed routes: route-b" in subleg_text

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    assert "build_balancing_point_resistance_allocation_v1(" in adapter_source
    assert "build_balancing_point_valve_authority_input_mapping_v1(" in adapter_source
    assert "balancing_point_evidence=" in adapter_source
    assert "_balancing_point_evidence_table" in panel_source
    assert "set_balancing_point_evidence_rows" in panel_source

    widget.deleteLater()
    app.processEvents()

    print(
        "OK — H-S44-E point allocation, method and valve-duty GUI / "
        "schematic evidence passed."
    )


if __name__ == "__main__":
    main()
