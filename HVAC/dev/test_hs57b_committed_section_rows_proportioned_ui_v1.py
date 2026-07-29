# ======================================================================
# H-S57-B — Committed section rows in clean Proportioned UI evidence
# ======================================================================

from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.committed_basis_section_hydraulic_result_v1 import (
    CommittedBasisSectionHydraulicResultV1,
    CommittedBasisSectionHydraulicRowV1,
)


def _row(route_id, route_label, section_id, order, *, shared=False):
    return CommittedBasisSectionHydraulicRowV1(
        committed_route_id=route_id,
        committed_route_label=route_label,
        basis="F&R",
        section_id=section_id,
        section_scope="common_main" if shared else "route_section",
        route_ids=(
            ("route-a", "route-b") if shared else (route_id,)
        ),
        shared_across_routes=shared,
        order=order,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.2,
        pipe_size_label="22 mm",
        dn=22,
        length_m=10.0,
        k_total=1.5,
        velocity_m_s=0.5,
        reynolds_number=10_000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=0 if not shared else 5,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=200.0,
        straight_pressure_drop_Pa=2_000.0,
        local_pressure_drop_Pa=100.0,
        section_total_pressure_drop_Pa=2_100.0,
    )


class _Panel:
    def __init__(self):
        self.rows = None
        self._proportioning_snapshot_section_rows = [
            {"route": "Preview route", "section": "99"}
        ]

    def set_clean_proportioned_focused_section_source_rows_v1(self, rows):
        self.rows = list(rows)


def main() -> None:
    result = CommittedBasisSectionHydraulicResultV1(
        ready=True,
        rows=(
            _row(
                "route-a",
                "Leg 1A Common subleg",
                "common-main-001",
                1,
                shared=True,
            ),
            _row(
                "route-a",
                "Leg 1A Common subleg",
                "route-a-001",
                2,
            ),
        ),
        unique_section_count=2,
        route_count=1,
        status="Ready",
    )

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    rows = adapter._build_committed_section_hydraulic_gui_rows_v1(result)
    assert len(rows) == 2
    assert rows[0]["route"] == "Leg 1A Common subleg"
    assert rows[0]["route_id"] == "route-a"
    assert rows[0]["section"] == "1"
    assert rows[0]["section_id"] == "common-main-001"
    assert rows[0]["flow_kg_s"] == "0.2000 kg/s"
    assert rows[0]["pipe_dn"] == "22 mm"
    assert rows[0]["dp_per_m"] == "200.0"
    assert rows[0]["length"] == "10.00 m"
    assert rows[0]["k"] == "1.50"
    assert rows[0]["section_dp"] == "2100.0 Pa"
    assert rows[0]["iter"] == "5"
    assert rows[0]["shared_across_routes"] is True
    assert rows[0]["evidence_source"] == "committed_hs57a"
    assert "preview" not in rows[0]["status"].lower()
    assert rows[1]["iter"] == "0"

    panel = _Panel()
    adapter._panel = panel
    adapter._committed_basis_section_hydraulic_result_v1 = result
    adapter._build_clean_proportioned_focused_section_source_rows_v1 = (
        lambda: (_ for _ in ()).throw(
            AssertionError("live preview source must not be read")
        )
    )
    adapter._push_clean_proportioned_focused_section_source_rows_v1()
    assert panel.rows == rows
    assert panel.rows[0]["route"] != "Preview route"

    adapter._committed_basis_section_hydraulic_result_v1 = (
        CommittedBasisSectionHydraulicResultV1(
            ready=False,
            status="Blocked — committed sections unavailable",
        )
    )
    adapter._push_clean_proportioned_focused_section_source_rows_v1()
    assert panel.rows[0]["evidence_source"] == "committed_hs57a"
    assert panel.rows[0]["status"].startswith("Blocked")

    adapter._committed_basis_section_hydraulic_result_v1 = None
    preview_rows = [{"route": "Preview route", "section": "99"}]
    adapter._build_clean_proportioned_focused_section_source_rows_v1 = (
        lambda: preview_rows
    )
    adapter._push_clean_proportioned_focused_section_source_rows_v1()
    assert panel.rows == preview_rows

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "build_committed_basis_section_hydraulic_result_v1(" in (
        adapter_source
    )
    assert "_build_committed_section_hydraulic_gui_rows_v1" in adapter_source
    assert "_push_clean_proportioned_focused_section_source_rows_v1()" in (
        adapter_source
    )
    assert '"evidence_source": "committed_hs57a"' in adapter_source
    assert (
        "set_clean_proportioned_focused_section_source_rows_v1(rows)"
        in adapter_source
    )
    assert (
        "self._refresh_clean_proportioned_schematic_section_evidence_v1()"
        in panel_source
    )
    assert (
        "self._refresh_clean_proportioned_focused_section_view_v1()"
        in panel_source
    )

    print(
        "OK — H-S57-B committed section rows Proportioned UI evidence passed."
    )


if __name__ == "__main__":
    main()
