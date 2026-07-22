# ======================================================================
# H-S48-C — Accepted generic Kvs hydraulic-consequence evidence
# ======================================================================

from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
    ACCEPTED_KVS_CONSEQUENCE_PENDING,
    NO_ACCEPTED_KVS_CONSEQUENCE_REQUIRED,
    build_balancing_point_accepted_kvs_hydraulic_consequence_v1,
    calculate_accepted_kvs_hydraulic_consequence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_acceptance_intent_v1 import (
    ResolvedPointKvsCandidateAcceptanceRowV1,
    ResolvedPointKvsCandidateAcceptanceV1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    BalancingPointKvsCandidateUtilisationEvidenceRowV1,
    BalancingPointKvsCandidateUtilisationEvidenceV1,
)


def main() -> None:
    dp_bar, dp_pa, authority = (
        calculate_accepted_kvs_hydraulic_consequence_v1(
            flow_m3_h=1.0,
            accepted_kvs=10.0,
            controlled_circuit_dp_pa=99_000.0,
        )
    )
    assert abs(dp_bar - 0.01) < 1e-12
    assert abs(dp_pa - 1_000.0) < 1e-9
    assert abs(authority - 0.01) < 1e-12

    evidence = BalancingPointKvsCandidateUtilisationEvidenceV1(
        ready=True,
        rows=(
            BalancingPointKvsCandidateUtilisationEvidenceRowV1(
                balancing_point_id="point-accepted",
                point_scope="subleg",
                point_role="common_route_downstream",
                label="Accepted point",
                parent_balancing_point_id="",
                anchor_section_id="section-accepted",
                downstream_route_ids=("route-accepted",),
                is_shared=False,
                is_route_exclusive=True,
                balancing_method_id="proportional_added_resistance",
                balancing_method_label="Proportional added resistance",
                authority_band_id="too_low_authority_preview",
                authority_label="Too low authority preview",
                design_valve_dp_pa=1_000.0,
                point_flow_kg_s=0.277222,
                candidate_resistance_pa_per_kg_s2=13_010.0,
                ready=True,
                flow_m3_h=1.0,
                controlled_circuit_dp_pa=99_000.0,
                kvs_candidates=(6.3, 10.0, 16.0),
            ),
            BalancingPointKvsCandidateUtilisationEvidenceRowV1(
                balancing_point_id="point-pending",
                point_scope="subleg",
                point_role="common_route_downstream",
                label="Pending point",
                parent_balancing_point_id="",
                anchor_section_id="section-pending",
                downstream_route_ids=("route-pending",),
                is_shared=False,
                is_route_exclusive=True,
                balancing_method_id="proportional_added_resistance",
                balancing_method_label="Proportional added resistance",
                authority_band_id="too_low_authority_preview",
                authority_label="Too low authority preview",
                design_valve_dp_pa=1_000.0,
                point_flow_kg_s=0.138611,
                candidate_resistance_pa_per_kg_s2=52_040.0,
                ready=True,
                flow_m3_h=0.5,
                controlled_circuit_dp_pa=20_000.0,
                kvs_candidates=(6.3, 10.0, 16.0),
            ),
            BalancingPointKvsCandidateUtilisationEvidenceRowV1(
                balancing_point_id="point-no-valve",
                point_scope="leg",
                point_role="leg_entry",
                label="No-valve point",
                parent_balancing_point_id="",
                anchor_section_id="section-no-valve",
                downstream_route_ids=("route-no-valve",),
                is_shared=True,
                is_route_exclusive=False,
                balancing_method_id="none_required",
                balancing_method_label="None required",
                authority_band_id="no_valve_authority_required",
                authority_label="No valve authority required",
                design_valve_dp_pa=0.0,
                point_flow_kg_s=0.1,
                candidate_resistance_pa_per_kg_s2=0.0,
                ready=True,
                kvs_candidates=(),
            ),
        ),
    )
    acceptance = ResolvedPointKvsCandidateAcceptanceV1(
        ready=True,
        rows=(
            ResolvedPointKvsCandidateAcceptanceRowV1(
                balancing_point_id="point-accepted",
                accepted=True,
                accepted_kvs=10.0,
            ),
            ResolvedPointKvsCandidateAcceptanceRowV1(
                balancing_point_id="point-pending",
                accepted=False,
            ),
            ResolvedPointKvsCandidateAcceptanceRowV1(
                balancing_point_id="point-no-valve",
                accepted=False,
            ),
        ),
    )

    result = build_balancing_point_accepted_kvs_hydraulic_consequence_v1(
        evidence,
        acceptance,
    )
    assert result.ready is True
    by_id = {row.balancing_point_id: row for row in result.rows}
    accepted = by_id["point-accepted"]
    assert accepted.consequence_state_id == ACCEPTED_KVS_CONSEQUENCE_AVAILABLE
    assert accepted.consequence_available is True
    assert accepted.accepted_kvs == 10.0
    assert abs(accepted.implied_valve_dp_pa - 1_000.0) < 1e-9
    assert abs(accepted.implied_authority - 0.01) < 1e-12
    assert by_id["point-pending"].consequence_state_id == (
        ACCEPTED_KVS_CONSEQUENCE_PENDING
    )
    assert by_id["point-pending"].implied_valve_dp_pa is None
    assert by_id["point-no-valve"].consequence_state_id == (
        NO_ACCEPTED_KVS_CONSEQUENCE_REQUIRED
    )

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    assert "build_balancing_point_accepted_kvs_hydraulic_consequence_v1(" in adapter_source
    assert "_enrich_balancing_point_gui_rows_with_kvs_consequence_v1(" in adapter_source
    assert '"Accepted Kvs"' in panel_source
    assert '"Implied valve Δp"' in panel_source
    assert '"Implied authority"' in panel_source
    assert '"Design authority"' in panel_source

    print("OK — H-S48-C accepted Kvs hydraulic-consequence evidence passed.")


if __name__ == "__main__":
    main()
