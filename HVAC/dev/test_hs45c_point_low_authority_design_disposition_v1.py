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
    AUTHORITY_ACCEPTABLE_FOR_REVIEW,
    EVIDENCE_UNAVAILABLE,
    HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED,
    LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED,
    NO_VALVE_REQUIRED,
    build_balancing_point_low_authority_design_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    BalancingPointValveAuthorityInputMappingV1,
    BalancingPointValveAuthorityInputRowV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_preview_v1 import (
    build_balancing_point_valve_authority_preview_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    HIGH_THROTTLING_BURDEN,
    MANUAL_REVIEW_REQUIRED,
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
    high_authority_row = replace(
        authority.rows[2],
        balancing_point_id="point:high",
        downstream_route_ids=("route-high",),
        authority=0.8,
        authority_band_id=HIGH_THROTTLING_BURDEN,
        authority_label="High throttling burden",
        status="Warning — high throttling burden preview",
    )
    authority = replace(
        authority,
        rows=(*authority.rows, high_authority_row),
    )
    disposition = build_balancing_point_low_authority_design_disposition_v1(
        authority
    )
    assert disposition.ready is True
    none_row, low_row, acceptable_row, high_row = disposition.rows

    assert none_row.design_disposition_id == NO_VALVE_REQUIRED
    assert none_row.design_disposition_label == "No valve required"
    assert none_row.manual_review_required is False
    assert none_row.authority is None

    assert low_row.design_disposition_id == LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED
    assert low_row.design_disposition_label == (
        "Low-authority manual review required"
    )
    assert low_row.manual_review_required is True
    assert low_row.balancing_point_id == "point:low"
    assert low_row.is_route_exclusive is True
    assert low_row.downstream_route_ids == ("route-low",)

    assert acceptable_row.design_disposition_id == (
        AUTHORITY_ACCEPTABLE_FOR_REVIEW
    )
    assert acceptable_row.design_disposition_label == (
        "Authority acceptable for review"
    )
    assert acceptable_row.manual_review_required is False

    assert high_row.design_disposition_id == (
        HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED
    )
    assert high_row.manual_review_required is True

    blocked_row = replace(
        authority.rows[1],
        ready=False,
        authority=None,
        authority_band_id=MANUAL_REVIEW_REQUIRED,
        blockers=("required evidence unavailable",),
    )
    blocked_authority = replace(
        authority,
        ready=False,
        blockers=("required evidence unavailable",),
        rows=(blocked_row,),
    )
    blocked = build_balancing_point_low_authority_design_disposition_v1(
        blocked_authority
    )
    assert blocked.ready is False
    assert blocked.rows[0].design_disposition_id == EVIDENCE_UNAVAILABLE
    assert blocked.rows[0].design_disposition_label == (
        "Blocked because required evidence is unavailable"
    )

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    build_pos = adapter_source.find("point_design_disposition =")
    assert build_pos >= 0
    table_pos = adapter_source.find("point_display_rows =", build_pos)
    assert table_pos > build_pos
    assert "point_design_disposition" in adapter_source[table_pos:table_pos + 300]
    schematic_pos = adapter_source.find(
        "_build_schematic_balancing_point_evidence_v1(",
        table_pos,
    )
    assert schematic_pos > table_pos
    assert "point_design_disposition" in adapter_source[
        schematic_pos:schematic_pos + 300
    ]

    print(
        "OK — H-S45-C point-scoped low-authority design-disposition "
        "evidence passed."
    )


if __name__ == "__main__":
    main()
