# ======================================================================
# H-S53-C — Explicit detailed valve product-data blockers
# ======================================================================

from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
    DETAILED_VALVE_DESIGN_DUTY_PENDING,
    NO_DETAILED_VALVE_DESIGN_DUTY_REQUIRED,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1,
    BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1,
)
from HVAC.hydronics.proportioning.balancing_point_detailed_valve_design_readiness_v1 import (
    CURRENT_CATALOGUE_MISSING_PRODUCT_EVIDENCE,
    DETAILED_VALVE_PRODUCT_DATA_BLOCKED,
    DETAILED_VALVE_PRODUCT_DATA_PENDING,
    NO_DETAILED_VALVE_PRODUCT_DATA_REQUIRED,
    build_balancing_point_detailed_valve_design_readiness_v1,
)


def main() -> None:
    source = BalancingPointApprovedValveCandidateDesignDutyEnvelopeV1(
        ready=True,
        rows=(
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                balancing_point_id="point:no-valve",
                ready=True,
                envelope_state_id=(
                    NO_DETAILED_VALVE_DESIGN_DUTY_REQUIRED
                ),
                detailed_valve_design_required=False,
                status="No detailed valve-design duty required",
            ),
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                balancing_point_id="point:approved",
                ready=True,
                envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
                detailed_valve_design_required=True,
                envelope_available=True,
                approved_for_later_valve_design=True,
                catalog_id="local-generic-valves-v1",
                valve_ref="LOCAL-GENERIC-KV-10",
                current_kv_m3_h=10.0,
                point_flow_kg_s=0.1794,
                flow_m3_h=0.6471,
                required_kv=4.307,
                controlled_circuit_dp_pa=34_605.0,
                implied_valve_dp_pa=418.8,
                implied_authority=0.012,
                design_valve_dp_pa=2257.3,
                design_authority=0.061,
                status="Approved detailed valve-design duty available",
            ),
            BalancingPointApprovedValveCandidateDesignDutyEnvelopeRowV1(
                balancing_point_id="point:pending",
                ready=True,
                envelope_state_id=DETAILED_VALVE_DESIGN_DUTY_PENDING,
                detailed_valve_design_required=True,
                envelope_available=False,
                catalog_id="local-generic-valves-v1",
                valve_ref="LOCAL-GENERIC-KV-6.3",
                current_kv_m3_h=6.3,
                status="Manual detailed valve-design approval pending",
            ),
        ),
    )
    before = source
    result = build_balancing_point_detailed_valve_design_readiness_v1(
        source
    )
    assert source == before
    assert result.ready is False
    rows = {row.balancing_point_id: row for row in result.rows}

    no_valve = rows["point:no-valve"]
    assert no_valve.ready is True
    assert no_valve.readiness_state_id == (
        NO_DETAILED_VALVE_PRODUCT_DATA_REQUIRED
    )

    approved = rows["point:approved"]
    assert approved.ready is False
    assert approved.duty_envelope_available is True
    assert approved.readiness_state_id == (
        DETAILED_VALVE_PRODUCT_DATA_BLOCKED
    )
    assert approved.catalog_id == "local-generic-valves-v1"
    assert approved.valve_ref == "LOCAL-GENERIC-KV-10"
    assert approved.current_kv_m3_h == 10.0
    assert approved.missing_product_evidence == (
        CURRENT_CATALOGUE_MISSING_PRODUCT_EVIDENCE
    )
    assert any("nominal valve size / DN" in value for value in approved.blockers)
    assert any("connection / end type" in value for value in approved.blockers)
    assert any(
        "setting / preset characteristic data" in value
        for value in approved.blockers
    )
    assert "approved hydraulic duty ready" in approved.status

    pending = rows["point:pending"]
    assert pending.ready is False
    assert pending.readiness_state_id == (
        DETAILED_VALVE_PRODUCT_DATA_PENDING
    )
    assert "H-S53-A approved" in pending.blockers[0]

    blocked = build_balancing_point_detailed_valve_design_readiness_v1(
        None
    )
    assert blocked.ready is False
    assert "H-S53-A" in blocked.blockers[0]

    assert "No catalogue schema extension" in result.exclusions
    assert "No manufacturer or product data invented" in result.exclusions
    assert "No committed valve product selection" in result.exclusions
    assert "No ProjectState mutation" in result.exclusions

    print(
        "OK — H-S53-C explicit detailed valve product-data blockers "
        "passed."
    )


if __name__ == "__main__":
    main()
