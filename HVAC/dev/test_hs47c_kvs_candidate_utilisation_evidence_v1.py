from __future__ import annotations

import math
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.balancing_point_controlled_circuit_dp_authority_v1 import (
    build_balancing_point_controlled_circuit_dp_authority_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_evidence_v1 import (
    build_balancing_point_kvs_candidate_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    KVS_UTILISATION_EVIDENCE_AVAILABLE,
    NO_KVS_UTILISATION_REQUIRED,
    build_balancing_point_kvs_candidate_utilisation_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_low_authority_design_disposition_v1 import (
    build_balancing_point_low_authority_design_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_required_kv_preview_v1 import (
    build_balancing_point_required_kv_preview_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    BalancingPointValveAuthorityInputMappingV1,
    BalancingPointValveAuthorityInputRowV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_preview_v1 import (
    build_balancing_point_valve_authority_preview_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_duty_design_basis_v1 import (
    MANUAL_ENGINEERING_APPROVAL_PENDING,
    build_balancing_point_valve_duty_design_basis_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)


def _input(point_id: str, route_id: str, added_dp: float):
    none_required = added_dp == 0.0
    return BalancingPointValveAuthorityInputRowV1(
        balancing_point_id=point_id,
        point_scope="subleg",
        point_role="common_route_downstream",
        label=point_id,
        parent_balancing_point_id="",
        anchor_section_id="",
        downstream_route_ids=(route_id,),
        is_shared=False,
        is_route_exclusive=True,
        balancing_method_id=(
            NONE_REQUIRED if none_required else PROPORTIONAL_ADDED_RESISTANCE
        ),
        balancing_method_label=(
            "None required" if none_required else "Proportional added resistance"
        ),
        authority_band_id=(
            VALVE_AUTHORITY_NONE_REQUIRED
            if none_required
            else VALVE_AUTHORITY_INPUT_AVAILABLE
        ),
        authority_label=(
            "No valve authority required"
            if none_required
            else "Valve authority input available"
        ),
        ready=True,
        design_valve_dp_pa=added_dp,
        point_flow_kg_s=0.18,
        candidate_resistance_pa_per_kg_s2=(
            0.0 if none_required else added_dp / (0.18 ** 2)
        ),
        controlled_circuit_dp_pa=None,
        authority=None,
        status="Input ready",
        blockers=(),
        note="Identity preserved.",
    )


def main():
    inputs = BalancingPointValveAuthorityInputMappingV1(
        ready=True,
        status="Ready",
        blockers=(),
        rows=(
            _input("point:none", "route-none", 0.0),
            _input("point:low", "route-low", 100.0),
        ),
    )
    pressure = build_balancing_point_controlled_circuit_dp_authority_v1(
        inputs,
        ({"route_id": "route-low", "chosen_dp_pa": 900.0},),
    )
    authority = build_balancing_point_valve_authority_preview_v1(pressure)
    disposition = build_balancing_point_low_authority_design_disposition_v1(
        authority
    )
    duty = build_balancing_point_valve_duty_design_basis_v1(disposition)
    required_kv = build_balancing_point_required_kv_preview_v1(duty)
    candidates = build_balancing_point_kvs_candidate_evidence_v1(required_kv)
    utilisation = (
        build_balancing_point_kvs_candidate_utilisation_evidence_v1(
            candidates
        )
    )
    assert utilisation.ready is True
    none_row, evidence_row = utilisation.rows

    assert none_row.kvs_utilisation_state_id == NO_KVS_UTILISATION_REQUIRED
    assert none_row.kvs_utilisation_available is False
    assert none_row.kvs_utilisation_summary == ""

    assert evidence_row.kvs_utilisation_state_id == (
        KVS_UTILISATION_EVIDENCE_AVAILABLE
    )
    assert evidence_row.kvs_utilisation_available is True
    assert evidence_row.kvs_candidates == (25.0, 40.0, 63.0)
    assert evidence_row.kvs_utilisation_summary == (
        "25: 82.1% | 40: 51.3% | 63: 32.6%"
    )
    assert evidence_row.balancing_point_id == "point:low"
    assert evidence_row.engineering_approval_state == (
        MANUAL_ENGINEERING_APPROVAL_PENDING
    )
    for percentage, fraction in zip(
        evidence_row.kvs_utilisation_percentages,
        evidence_row.kvs_operating_fractions,
    ):
        assert math.isclose(percentage, fraction * 100.0)

    blocked = build_balancing_point_kvs_candidate_utilisation_evidence_v1(
        None
    )
    assert blocked.ready is False
    assert any("H-S47-B" in item for item in blocked.blockers)

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    widget_source = Path(
        "HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py"
    ).read_text()
    build_pos = adapter_source.find("point_kvs_utilisation =")
    assert build_pos >= 0
    assert "point_kvs_candidates" in adapter_source[build_pos:build_pos + 300]
    table_pos = adapter_source.find("point_display_rows =", build_pos)
    assert table_pos > build_pos
    assert "point_kvs_utilisation" in adapter_source[table_pos:table_pos + 300]
    assert '"Kvs utilisation"' in panel_source
    assert 'row.get("kvs_utilisation", "—")' in panel_source
    assert "kvs_utilisation: str" in widget_source
    assert "Kvs utilisation:" in widget_source

    print("OK — H-S47-C Kvs candidate utilisation evidence passed.")


if __name__ == "__main__":
    main()
