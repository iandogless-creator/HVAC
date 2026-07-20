from __future__ import annotations

from dataclasses import dataclass

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    balancing_method_candidate_mapping_to_dict_v1,
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    PreliminaryBalancingResistanceRowV1,
    build_chosen_basis_balancing_resistance_basis_v1,
)


@dataclass(frozen=True)
class _Chosen:
    route_id: str
    route: str
    basis: str
    chosen_dp_pa: float
    is_controlling: bool
    dp_below_controlling_pa: float
    common_main_dp_pa: float = 0.0
    leg_entry_dp_pa: float = 0.0
    physical_main_entry_dp_pa: float = 0.0


def main() -> None:
    chosen_rows = [
        _Chosen(
            route_id="route-a",
            route="Route A",
            basis="F&R",
            chosen_dp_pa=1500.0,
            is_controlling=True,
            dp_below_controlling_pa=0.0,
            physical_main_entry_dp_pa=700.0,
        ),
        _Chosen(
            route_id="route-b",
            route="Route B",
            basis="F+RR",
            chosen_dp_pa=1400.0,
            is_controlling=False,
            dp_below_controlling_pa=100.0,
            physical_main_entry_dp_pa=100.0,
        ),
    ]

    # These legacy resistance values are intentionally stale. H-S43-B must
    # replace them before H-S43-C maps the balancing-method candidates.
    legacy_flow_basis = PreliminaryBalancingResistanceBasisV1(
        ready=True,
        rows=[
            PreliminaryBalancingResistanceRowV1(
                route_id="route-a",
                route_label="Route A",
                flow_kg_s="0.20000 kg/s",
                required_added_dp="999.0 Pa",
                resistance_pa_per_kg_s2="999999.0 Pa/(kg/s)²",
            ),
            PreliminaryBalancingResistanceRowV1(
                route_id="route-b",
                route_label="Route B",
                flow_kg_s="0.10000 kg/s",
                required_added_dp="888.0 Pa",
                resistance_pa_per_kg_s2="888888.0 Pa/(kg/s)²",
            ),
        ],
    )

    chosen_resistance = build_chosen_basis_balancing_resistance_basis_v1(
        chosen_controlling_rows=chosen_rows,
        flow_basis=legacy_flow_basis,
    )
    assert chosen_resistance.ready is True

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    burden_rows = adapter._build_provisional_proportioning_burden_rows_v1(
        chosen_rows,
        resistance_basis=chosen_resistance,
    )
    mapping = adapter._build_balancing_method_candidate_mapping_preview_v1(
        provisional_burden_rows=burden_rows,
    )

    assert mapping.ready is True
    assert len(mapping.candidates) == 2
    by_route = {candidate.route: candidate for candidate in mapping.candidates}
    controlling = by_route["Route A"]
    proportional = by_route["Route B"]

    assert controlling.method_id == NONE_REQUIRED
    assert controlling.ready is True
    assert controlling.controlling is True
    assert controlling.required_added_dp_pa == 0.0
    assert controlling.resistance_pa_per_kg_s2 == 0.0

    assert proportional.method_id == PROPORTIONAL_ADDED_RESISTANCE
    assert proportional.ready is True
    assert proportional.controlling is False
    assert proportional.required_added_dp_pa == 100.0
    assert proportional.flow_kg_s == 0.1
    assert proportional.resistance_pa_per_kg_s2 == 10000.0
    assert proportional.resistance_pa_per_kg_s2 not in {888888.0, 999999.0}
    assert "no valve selected" in proportional.note
    assert "Kv/Kvs" in proportional.note

    payload = balancing_method_candidate_mapping_to_dict_v1(mapping)
    assert payload is not None
    assert "No valve product selected" in payload["exclusions"]
    assert "No pump selected" in payload["exclusions"]
    assert "No final balancing" in payload["exclusions"]
    assert "No pipe resizing" in payload["exclusions"]

    # A controlling flag with positive added Δp is inconsistent and must not
    # silently become NONE_REQUIRED.
    inconsistent = build_balancing_method_candidate_mapping_v1(
        [
            {
                "route": "Broken controlling route",
                "controlling": "Yes",
                "required_added_dp": "10.0 Pa",
                "flow_kg_s": "0.1 kg/s",
                "resistance_pa_per_kg_s2": "0.0",
            }
        ]
    )
    assert inconsistent.ready is False
    assert inconsistent.candidates[0].method_id == MANUAL_REVIEW_REQUIRED
    assert any(
        "zero added Δp" in blocker
        for blocker in inconsistent.candidates[0].blockers
    )

    missing = build_balancing_method_candidate_mapping_v1(
        [
            {
                "route": "Missing evidence route",
                "controlling": "No",
                "required_added_dp": "100.0 Pa",
                "flow_kg_s": "—",
                "resistance_pa_per_kg_s2": "—",
            }
        ]
    )
    assert missing.ready is False
    assert missing.candidates[0].method_id == MANUAL_REVIEW_REQUIRED

    print(
        "OK — H-S43-C mains-aware balancing-method candidate "
        "consumption passed."
    )


if __name__ == "__main__":
    main()
