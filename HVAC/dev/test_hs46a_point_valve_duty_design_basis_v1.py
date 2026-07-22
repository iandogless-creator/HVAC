from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.balancing_point_controlled_circuit_dp_authority_v1 import (
    build_balancing_point_controlled_circuit_dp_authority_v1,
)
from HVAC.hydronics.proportioning.balancing_point_low_authority_design_disposition_v1 import (
    EVIDENCE_UNAVAILABLE,
    build_balancing_point_low_authority_design_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    BalancingPointValveAuthorityInputMappingV1,
    BalancingPointValveAuthorityInputRowV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_preview_v1 import (
    build_balancing_point_valve_authority_preview_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_duty_design_basis_v1 import (
    ENGINEERING_APPROVAL_NOT_APPLICABLE,
    MANUAL_ENGINEERING_APPROVAL_PENDING,
    NO_VALVE_DUTY_REQUIRED,
    POINT_VALVE_DUTY_BASIS_AVAILABLE,
    POINT_VALVE_DUTY_EVIDENCE_UNAVAILABLE,
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
            _input("point:acceptable", "route-acceptable", 300.0),
        ),
    )
    chosen = (
        {"route_id": "route-low", "chosen_dp_pa": 900.0},
        {"route_id": "route-acceptable", "chosen_dp_pa": 700.0},
    )
    pressure = build_balancing_point_controlled_circuit_dp_authority_v1(
        inputs,
        chosen,
    )
    authority = build_balancing_point_valve_authority_preview_v1(pressure)
    disposition = build_balancing_point_low_authority_design_disposition_v1(
        authority
    )
    basis = build_balancing_point_valve_duty_design_basis_v1(disposition)
    assert basis.ready is True
    none_row, low_row, acceptable_row = basis.rows

    assert none_row.valve_duty_state_id == NO_VALVE_DUTY_REQUIRED
    assert none_row.valve_duty_required is False
    assert none_row.valve_duty_basis_available is False
    assert none_row.manual_engineering_approval_required is False
    assert none_row.engineering_approval_state == (
        ENGINEERING_APPROVAL_NOT_APPLICABLE
    )

    assert low_row.valve_duty_state_id == POINT_VALVE_DUTY_BASIS_AVAILABLE
    assert low_row.valve_duty_required is True
    assert low_row.valve_duty_basis_available is True
    assert low_row.manual_engineering_approval_required is True
    assert low_row.engineering_approval_state == (
        MANUAL_ENGINEERING_APPROVAL_PENDING
    )
    assert low_row.point_flow_kg_s == 0.18
    assert low_row.design_valve_dp_pa == 100.0
    assert low_row.balancing_point_id == "point:low"
    assert low_row.downstream_route_ids == ("route-low",)

    assert acceptable_row.valve_duty_required is True
    assert acceptable_row.valve_duty_basis_available is True
    assert acceptable_row.engineering_approval_state == (
        MANUAL_ENGINEERING_APPROVAL_PENDING
    )

    blocked_disposition_row = replace(
        disposition.rows[1],
        ready=False,
        evidence_available=False,
        design_disposition_id=EVIDENCE_UNAVAILABLE,
        blockers=("required evidence unavailable",),
    )
    blocked_disposition = replace(
        disposition,
        ready=False,
        blockers=("required evidence unavailable",),
        rows=(blocked_disposition_row,),
    )
    blocked = build_balancing_point_valve_duty_design_basis_v1(
        blocked_disposition
    )
    assert blocked.ready is False
    assert blocked.rows[0].valve_duty_state_id == (
        POINT_VALVE_DUTY_EVIDENCE_UNAVAILABLE
    )
    assert blocked.rows[0].valve_duty_basis_available is False

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    build_pos = adapter_source.find("point_valve_duty_basis =")
    assert build_pos >= 0
    assert "point_design_disposition" in adapter_source[
        build_pos:build_pos + 300
    ]
    table_pos = adapter_source.find("point_display_rows =", build_pos)
    assert table_pos > build_pos
    assert "point_valve_duty_basis" in adapter_source[table_pos:table_pos + 300]
    schematic_pos = adapter_source.find(
        "_build_schematic_balancing_point_evidence_v1(",
        table_pos,
    )
    assert schematic_pos > table_pos
    assert "point_valve_duty_basis" in adapter_source[
        schematic_pos:schematic_pos + 300
    ]

    print("OK — H-S46-A point-scoped valve-duty design basis passed.")


if __name__ == "__main__":
    main()
