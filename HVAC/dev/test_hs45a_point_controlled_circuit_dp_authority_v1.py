from __future__ import annotations

from pathlib import Path

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.balancing_point_controlled_circuit_dp_authority_v1 import (
    POINT_CONTROLLED_CIRCUIT_NOT_REQUIRED_V1,
    POINT_GOVERNED_ROUTE_CHOSEN_DP_V1,
    build_balancing_point_controlled_circuit_dp_authority_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    BalancingPointValveAuthorityInputMappingV1,
    BalancingPointValveAuthorityInputRowV1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)


def _row(point_id, route_ids, *, shared, added_dp):
    none_required = added_dp == 0.0
    return BalancingPointValveAuthorityInputRowV1(
        balancing_point_id=point_id,
        point_scope="main" if shared else "subleg",
        point_role="common_main_takeoff" if shared else "common_route_downstream",
        label=point_id,
        parent_balancing_point_id="",
        anchor_section_id="",
        downstream_route_ids=route_ids,
        is_shared=shared,
        is_route_exclusive=not shared,
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
        status="H-S44-D input ready",
        blockers=(),
        note="Scope preserved.",
    )


def main():
    inputs = BalancingPointValveAuthorityInputMappingV1(
        ready=True,
        status="Ready",
        blockers=(),
        rows=(
            _row(
                "balancing-point:main:leg-001",
                ("leg-001-primary-subleg", "leg-001-subleg-b"),
                shared=True,
                added_dp=200.0,
            ),
            _row(
                "balancing-point:subleg:leg-001-primary-subleg:downstream-exclusive",
                ("leg-001-primary-subleg",),
                shared=False,
                added_dp=100.0,
            ),
            _row(
                "balancing-point:subleg:leg-001-subleg-b",
                ("leg-001-subleg-b",),
                shared=False,
                added_dp=0.0,
            ),
        ),
    )
    chosen = (
        {"route_id": "leg-001:leg-001-primary-subleg", "chosen_dp_pa": 900.0},
        {"route_id": "leg-001:leg-001-subleg-b", "chosen_dp_pa": 1200.0},
    )

    projection = build_balancing_point_controlled_circuit_dp_authority_v1(
        inputs,
        chosen,
    )
    assert projection.ready is True
    assert projection.blockers == ()
    shared, exclusive, none_required = projection.rows

    assert shared.controlled_circuit_basis_id == POINT_GOVERNED_ROUTE_CHOSEN_DP_V1
    assert shared.governed_route_dp_evidence == (
        ("leg-001-primary-subleg", 900.0),
        ("leg-001-subleg-b", 1200.0),
    )
    assert shared.controlled_circuit_dp_pa == 1200.0
    assert shared.controlled_circuit_dp_pa != 2100.0
    assert shared.controlling_route_ids == ("leg-001-subleg-b",)
    assert shared.authority is None

    assert exclusive.controlled_circuit_dp_pa == 900.0
    assert exclusive.controlling_route_ids == ("leg-001-primary-subleg",)
    assert exclusive.authority is None

    assert none_required.controlled_circuit_basis_id == POINT_CONTROLLED_CIRCUIT_NOT_REQUIRED_V1
    assert none_required.controlled_circuit_dp_pa is None

    missing = build_balancing_point_controlled_circuit_dp_authority_v1(
        inputs,
        chosen[:1],
    )
    assert missing.ready is False
    assert any("chosen-route Δp evidence missing" in item for item in missing.blockers)

    duplicate = build_balancing_point_controlled_circuit_dp_authority_v1(
        inputs,
        (*chosen, chosen[0]),
    )
    assert duplicate.ready is False
    assert any("duplicate chosen-route Δp evidence" in item for item in duplicate.blockers)

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "point_controlled_circuit_dp = (" in adapter_source
    assert "chosen_preview_rows," in adapter_source
    assert "_balancing_point_controlled_circuit_dp_authority_preview" in adapter_source

    print("OK — H-S45-A point-scoped controlled-circuit Δp authority passed.")


if __name__ == "__main__":
    main()
