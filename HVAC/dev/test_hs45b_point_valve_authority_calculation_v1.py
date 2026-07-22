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
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    BalancingPointValveAuthorityInputMappingV1,
    BalancingPointValveAuthorityInputRowV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_preview_v1 import (
    build_balancing_point_valve_authority_preview_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    TOO_LOW_AUTHORITY_PREVIEW,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)
from HVAC.hydronics.proportioning.valve_authority_preview_v1 import (
    calculate_valve_authority_v1,
)


def _input(point_id, route_ids, *, shared, added_dp):
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
            _input(
                "balancing-point:main:leg-001",
                ("leg-001-primary-subleg", "leg-001-subleg-b"),
                shared=True,
                added_dp=200.0,
            ),
            _input(
                "balancing-point:subleg:leg-001-primary-subleg:downstream-exclusive",
                ("leg-001-primary-subleg",),
                shared=False,
                added_dp=100.0,
            ),
            _input(
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
    pressure = build_balancing_point_controlled_circuit_dp_authority_v1(
        inputs,
        chosen,
    )
    preview = build_balancing_point_valve_authority_preview_v1(pressure)
    assert preview.ready is True
    assert preview.blockers == ()
    shared, exclusive, none_required = preview.rows

    expected_shared = 200.0 / (200.0 + 1200.0)
    assert math.isclose(shared.authority or 0.0, expected_shared)
    assert shared.authority_band_id == TOO_LOW_AUTHORITY_PREVIEW
    assert shared.authority_label == "Too low authority preview"
    assert shared.controlled_circuit_dp_pa == 1200.0
    assert shared.controlling_route_ids == ("leg-001-subleg-b",)
    assert shared.is_shared is True

    expected_exclusive = 100.0 / (100.0 + 900.0)
    assert math.isclose(exclusive.authority or 0.0, expected_exclusive)
    assert exclusive.authority_band_id == TOO_LOW_AUTHORITY_PREVIEW
    assert exclusive.controlled_circuit_dp_pa == 900.0
    assert exclusive.is_route_exclusive is True
    assert exclusive.downstream_route_ids == ("leg-001-primary-subleg",)

    assert none_required.ready is True
    assert none_required.authority is None
    assert none_required.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED
    assert none_required.controlled_circuit_dp_pa is None

    assert math.isclose(
        calculate_valve_authority_v1(
            design_valve_dp_pa=250.0,
            controlled_circuit_dp_pa=750.0,
        ) or 0.0,
        0.25,
    )

    blocked_pressure = pressure.__class__(
        ready=False,
        status="Blocked",
        blockers=("upstream unavailable",),
        rows=pressure.rows,
    )
    blocked = build_balancing_point_valve_authority_preview_v1(blocked_pressure)
    assert blocked.ready is False
    assert any("upstream unavailable" in item for item in blocked.blockers)

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "build_balancing_point_valve_authority_preview_v1(" in adapter_source
    assert "point_valve_authority" in adapter_source
    assert "_balancing_point_valve_authority_preview" in adapter_source
    assert (
        "_build_balancing_point_gui_rows_v1(\n"
        "                point_valve_authority"
    ) in adapter_source

    print("OK — H-S45-B point-scoped valve-authority calculation and classification passed.")


if __name__ == "__main__":
    main()
