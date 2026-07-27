# ======================================================================
# H-S53-B — Approved valve-candidate detailed-design duty table
# ======================================================================

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def main() -> None:
    evidence = SimpleNamespace(
        ready=True,
        rows=(
            SimpleNamespace(
                balancing_point_id="balancing-point:subleg:approved",
                point_scope="subleg",
                point_role="common_route_downstream",
                topology="Route-exclusive",
                governed_route_ids=("route-1",),
                detailed_valve_design_required=True,
                catalog_id="local-generic-valves-v1",
                valve_ref="LOCAL-GENERIC-KV-10",
                current_kv_m3_h=10.0,
                point_flow_kg_s=0.1794,
                required_kv=4.307,
                implied_valve_dp_pa=418.8,
                controlled_circuit_dp_pa=34605.0,
                implied_authority=0.012,
                design_authority=0.061,
                ready=True,
                status=(
                    "Approved catalogue valve-candidate detailed-design "
                    "duty envelope available"
                ),
                blockers=(),
            ),
            SimpleNamespace(
                balancing_point_id="point:not-required",
                detailed_valve_design_required=False,
            ),
        ),
    )
    rows = (
        HydronicsSchematicPanelAdapter
        ._build_approved_valve_candidate_design_duty_gui_rows_v1(
            evidence
        )
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["balancing_point_id"] == (
        "balancing-point:subleg:approved"
    )
    assert row["catalog_id"] == "local-generic-valves-v1"
    assert row["valve_ref"] == "LOCAL-GENERIC-KV-10"
    assert row["current_kv"] == "10.000"
    assert row["point_flow"] == "0.17940 kg/s"
    assert row["required_kv"] == "4.307"
    assert row["implied_dp"] == "418.8 Pa"
    assert row["controlled_dp"] == "34605.0 Pa"
    assert row["implied_authority"] == "0.012"
    assert row["design_authority"] == "0.061"
    assert row["ready"] == "Yes"

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_balancing_point_approved_valve_candidate_"
        "design_duty_envelope_v1(" in adapter_source
    )
    assert (
        "set_approved_valve_candidate_design_duty_envelope_rows"
        in adapter_source
    )
    assert (
        "Approved catalogue valve-candidate detailed-design duty "
        "envelopes — read-only" in panel_source
    )
    assert "_approved_valve_candidate_design_duty_table" in panel_source
    assert "expanded=False" in panel_source

    print(
        "OK — H-S53-B approved valve-candidate detailed-design duty "
        "table passed."
    )


if __name__ == "__main__":
    main()
