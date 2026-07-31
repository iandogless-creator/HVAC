from __future__ import annotations

import inspect
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def _text(table, row, column):
    item = table.item(row, column)
    return item.text() if item is not None else ""


def main() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    panel = HydronicsSchematicPanel()
    tab_labels = [
        panel._tabs.tabText(index)
        for index in range(panel._tabs.count())
    ]
    assert "Pipe Resizing" in tab_labels
    assert panel._resized_pipe_section_review_table.columnCount() == 12
    assert panel._resized_pipe_route_review_table.columnCount() == 9
    assert panel._resized_pipe_point_review_table.columnCount() == 10
    assert (
        panel._resized_pipe_section_review_table.alternatingRowColors()
        is True
    )

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    section_result = SimpleNamespace(
        ready=True,
        sections=(
            SimpleNamespace(
                section_id="section-1",
                route_ids=("route-1",),
                current_pipe_size_label="15 mm",
                projected_pipe_size_label="22 mm",
                recommendation="INCREASE",
                carried_flow_kg_s=0.1500,
                velocity_m_s=0.478,
                maximum_velocity_m_s=1.0,
                pressure_gradient_Pa_per_m=180.0,
                maximum_pressure_gradient_Pa_per_m=200.0,
                straight_pressure_drop_Pa=900.0,
                local_pressure_drop_Pa=171.0,
                section_total_pressure_drop_Pa=1071.0,
                status="Projected section",
            ),
        ),
    )
    section_rows = (
        adapter._build_resized_pipe_section_review_rows_v1(section_result)
    )
    panel.set_resized_pipe_section_review_rows_v1(section_rows)
    assert _text(panel._resized_pipe_section_review_table, 0, 0) == (
        "section-1"
    )
    assert _text(panel._resized_pipe_section_review_table, 0, 2) == (
        "15 mm"
    )
    assert _text(panel._resized_pipe_section_review_table, 0, 3) == (
        "22 mm"
    )
    assert _text(panel._resized_pipe_section_review_table, 0, 4) == (
        "Increase"
    )
    assert "180.0 / 200.0 Pa/m" == _text(
        panel._resized_pipe_section_review_table, 0, 7
    )
    assert _text(panel._resized_pipe_section_review_table, 0, 9) == (
        "171.0 Pa"
    )

    resized = SimpleNamespace(
        ready=True,
        routes=(
            SimpleNamespace(
                route_id="route-1",
                section_count=4,
                route_pressure_drop_total_Pa=1250.0,
                controlling_target_Pa=1300.0,
                required_added_dp_Pa=50.0,
            ),
        ),
    )
    reconciliation = SimpleNamespace(
        ready=True,
        route_rows=(
            SimpleNamespace(
                projected_route_id="route-1",
                allocated_path_dp_Pa=50.0,
                residual_Pa=-0.0,
                conserved=True,
                status="Reconciled route",
            ),
        ),
        point_rows=(
            SimpleNamespace(
                balancing_point_id="point-1",
                point_scope="subleg",
                projected_route_ids=("route-1",),
                point_flow_kg_s=0.15,
                previous_allocated_dp_Pa=20.0,
                reconciled_allocated_dp_Pa=50.0,
                allocation_change_dp_Pa=30.0,
                reconciled_resistance_Pa_per_kg_s2=2222.2,
                valve_duty_required=True,
                status="Reconciled point",
            ),
        ),
    )
    route_rows = adapter._build_resized_pipe_route_review_rows_v1(
        resized,
        reconciliation,
    )
    panel.set_resized_pipe_route_review_rows_v1(route_rows)
    assert _text(panel._resized_pipe_route_review_table, 0, 0) == "route-1"
    assert _text(panel._resized_pipe_route_review_table, 0, 6) == "0.0 Pa"
    assert _text(panel._resized_pipe_route_review_table, 0, 7) == "Yes"

    point_rows = adapter._build_resized_pipe_point_review_rows_v1(
        reconciliation
    )
    panel.set_resized_pipe_point_review_rows_v1(point_rows)
    assert _text(panel._resized_pipe_point_review_table, 0, 0) == "point-1"
    assert _text(panel._resized_pipe_point_review_table, 0, 4) == "20.0 Pa"
    assert _text(panel._resized_pipe_point_review_table, 0, 5) == "50.0 Pa"
    assert _text(panel._resized_pipe_point_review_table, 0, 6) == "30.0 Pa"
    assert _text(panel._resized_pipe_point_review_table, 0, 8) == "Yes"

    adapter_source = inspect.getsource(HydronicsSchematicPanelAdapter)
    panel_source = inspect.getsource(HydronicsSchematicPanel)
    for builder_name in (
        "build_proportioned_pipe_sizing_authority_v1",
        "build_proportioned_pipe_size_candidate_evaluation_v1",
        "build_proportioned_pipe_resizing_hydraulic_projection_v1",
        "build_resized_balancing_point_reconciliation_v1",
    ):
        assert builder_name in adapter_source
    assert '"Pipe Resizing"' in panel_source
    assert "DNs remain unchanged" in panel_source
    assert "set_resized_pipe_section_review_rows_v1" in panel_source
    assert "set_resized_pipe_route_review_rows_v1" in panel_source
    assert "set_resized_pipe_point_review_rows_v1" in panel_source

    panel.close()
    print("OK — H-S61-E resized pipework engineering review UI passed.")


if __name__ == "__main__":
    main()
