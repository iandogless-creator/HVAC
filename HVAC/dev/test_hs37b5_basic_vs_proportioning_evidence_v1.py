# ======================================================================
# HVAC/dev/test_hs37b5_basic_vs_proportioning_evidence_v1.py
# H-S37-B5 — Basic PS and Proportioning evidence remain distinct
# ======================================================================

from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

import HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter as adapter_module
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


SECTION_ID = "leg-001-primary-subleg-section-002"


def _projection():
    result = SimpleNamespace(
        section_id=SECTION_ID,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
        order=2,
        from_label="L1A-R01",
        to_room_label="L1A-R02",
        carried_heat_W=6200.0,
        carried_flow_kg_s=0.1483,
        pipe_size_label="15 mm",
        velocity_m_s=1.023,
        applied_max_velocity_m_s=1.05,
        max_velocity_source="Environment default",
        reynolds_number=13900.0,
        friction_factor=0.0285,
        pressure_gradient_Pa_per_m=1100.0,
        status=(
            "First-pass Haaland estimate / Maximum velocity "
            "1.05 m/s — Environment default"
        ),
    )
    topology_section = SimpleNamespace(
        section_id=SECTION_ID,
        status="Branch-aware carried-flow basis",
    )
    preview = SimpleNamespace(
        section_id=SECTION_ID,
        section_length_m=4.0,
        section_pressure_drop_Pa=4400.0,
        status="Preview only",
    )
    return SimpleNamespace(
        sections_projection=SimpleNamespace(
            leg_label="Heating Leg 1",
            subleg_label="Leg 1A Common subleg",
            sections=(topology_section,),
        ),
        pipe_sizing_projection=SimpleNamespace(results=(result,)),
        pressure_preview_projection=SimpleNamespace(rows=(preview,)),
    )


def _route_section():
    return SimpleNamespace(
        velocity_m_s=1.120,
        pressure_gradient_Pa_per_m=1359.4,
        reynolds_number=14527.0,
        friction_factor=0.0282,
        friction_method="colebrook",
        colebrook_iteration_count=6,
        colebrook_converged=True,
    )


def _test_adapter_evidence_keys() -> dict:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = SimpleNamespace(
        environment=SimpleNamespace(basic_ps_max_velocity_m_s=1.05),
        basic_hydronic_sizing_intent=SimpleNamespace(
            section_max_velocity_overrides_m_s={}
        ),
    )

    local_k_calls: list[dict] = []
    original_builder = adapter_module.build_local_k_pressure_preview_v1

    def fake_local_k(project_state, **kwargs):
        local_k_calls.append(dict(kwargs))
        return SimpleNamespace(
            length_m=4.0,
            section_total_pressure_drop_Pa=7627.2,
            status="Local K preview",
            k_total=3.5,
            local_pressure_drop_Pa=2189.7,
            straight_pressure_drop_Pa=5437.5,
        )

    adapter_module.build_local_k_pressure_preview_v1 = fake_local_k
    try:
        rows = adapter._build_proportioning_basic_ps_sections(
            _projection(),
            route_section_by_id={SECTION_ID: _route_section()},
        )
    finally:
        adapter_module.build_local_k_pressure_preview_v1 = original_builder

    assert len(rows) == 1
    row = rows[0]
    assert row["pipe"] == "15 mm"
    assert "1.023" in row["basic_velocity_m_s"]
    assert "1.050" in row["basic_max_velocity_m_s"]
    assert row["basic_velocity_source"] == "Environment default"
    assert row["basic_friction_basis"] == (
        "Velocity selection / Haaland Δp"
    )
    assert "1.120" in row["proportioning_velocity_m_s"]
    assert "1359.4" in row["proportioning_dp_per_m"]
    assert row["proportioning_reynolds_number"] == "14527"
    assert row["proportioning_friction_method"] == "colebrook"
    assert row["proportioning_colebrook_iterations"] == "6"
    assert row["velocity_m_s"] == row["proportioning_velocity_m_s"]
    assert local_k_calls == [
        {
            "section_id": SECTION_ID,
            "velocity_m_s": 1.120,
            "pressure_gradient_Pa_per_m": 1359.4,
        }
    ]
    return row


def _test_panel_columns(row: dict) -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    panel.set_proportioning_basic_ps_sections([row])
    table = panel._proportioning_basic_ps_sections_table

    expected_headers = [
        "Order",
        "From",
        "To",
        "Q carried",
        "Flow kg/s",
        "Basic pipe",
        "Basic v",
        "Max v",
        "v source",
        "Basic basis",
        "Prop v",
        "Prop Δp/m",
        "Prop Re",
        "Prop f",
        "Prop method",
        "Iter",
        "Length",
        "K",
        "Local Δp",
        "Straight Δp",
        "Section Δp",
        "Status",
    ]
    assert table.columnCount() == len(expected_headers)
    assert [
        table.horizontalHeaderItem(index).text()
        for index in range(table.columnCount())
    ] == expected_headers
    assert "1.023" in table.item(0, 6).text()
    assert "1.050" in table.item(0, 7).text()
    assert table.item(0, 8).text() == "Environment default"
    assert table.item(0, 9).text() == "Velocity selection / Haaland Δp"
    assert "1.120" in table.item(0, 10).text()
    assert "1359.4" in table.item(0, 11).text()
    assert table.item(0, 14).text() == "colebrook"
    assert table.item(0, 15).text() == "6"

    panel._build_clean_proportioned_table_viewer_v1()
    assert panel._clean_proportioned_table_viewer_dialog.windowTitle() == (
        "Proportioned data viewer — read-only"
    )
    panel.close()
    app.processEvents()


def _test_missing_proportioning_evidence_is_honest() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = SimpleNamespace(
        environment=SimpleNamespace(basic_ps_max_velocity_m_s=1.05),
        basic_hydronic_sizing_intent=None,
    )
    original_builder = adapter_module.build_local_k_pressure_preview_v1
    adapter_module.build_local_k_pressure_preview_v1 = lambda *args, **kwargs: (
        SimpleNamespace(
            length_m=None,
            section_total_pressure_drop_Pa=None,
            status="No Local K intent",
            k_total=0.0,
            local_pressure_drop_Pa=0.0,
            straight_pressure_drop_Pa=None,
        )
    )
    try:
        row = adapter._build_proportioning_basic_ps_sections(
            _projection(),
            route_section_by_id={},
        )[0]
    finally:
        adapter_module.build_local_k_pressure_preview_v1 = original_builder

    assert row["basic_friction_basis"] == (
        "Velocity selection / Haaland Δp"
    )
    assert row["proportioning_velocity_m_s"] == "—"
    assert row["proportioning_dp_per_m"] == "—"
    assert row["proportioning_friction_method"] == "—"
    assert row["proportioning_colebrook_iterations"] == "—"


def main() -> None:
    row = _test_adapter_evidence_keys()
    _test_panel_columns(row)
    _test_missing_proportioning_evidence_is_honest()
    print(
        "OK — H-S37-B5 Basic PS / Proportioning evidence separation passed."
    )


if __name__ == "__main__":
    main()
