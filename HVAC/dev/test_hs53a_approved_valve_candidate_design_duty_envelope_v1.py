# ======================================================================
# H-S53-A — Approved catalogue valve-candidate design duty envelope
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_consequence_disposition_intent_v1 import (
    ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1,
    ResolvedPointAcceptedValveCandidateConsequenceDispositionV1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1,
    BalancingPointAcceptedValveCandidateHydraulicConsequenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    DETAILED_VALVE_DESIGN_DUTY_AVAILABLE,
    DETAILED_VALVE_DESIGN_DUTY_PENDING,
    DETAILED_VALVE_DESIGN_DUTY_REVISION_REQUIRED,
    build_balancing_point_approved_valve_candidate_design_duty_envelope_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


POINT_ID = "balancing-point:subleg:approved"
CATALOG_ID = "catalog-v1"
VALVE_REF = "VALVE-KV-10"


def product_duties():
    return BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        rows=(
            BalancingPointValveProductSearchDutyEnvelopeRowV1(
                balancing_point_id=POINT_ID,
                point_scope="subleg",
                point_role="common_route_downstream",
                label="Approved downstream point",
                topology="Route-exclusive",
                governed_route_ids=("route-1",),
                ready=True,
                product_search_required=True,
                envelope_available=True,
                approved_for_product_search=True,
                point_flow_kg_s=0.1794,
                flow_m3_h=0.6471,
                required_kv=6.092,
                accepted_kvs=10.0,
                implied_valve_dp_pa=418.8,
                controlled_circuit_dp_pa=34_605.0,
                implied_authority=0.012,
                design_valve_dp_pa=2257.3,
                design_authority=0.061,
            ),
        ),
    )


def consequence():
    return BalancingPointAcceptedValveCandidateHydraulicConsequenceV1(
        ready=True,
        rows=(
            BalancingPointAcceptedValveCandidateHydraulicConsequenceRowV1(
                balancing_point_id=POINT_ID,
                ready=True,
                consequence_state_id=(
                    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
                ),
                consequence_available=True,
                accepted=True,
                catalog_id=CATALOG_ID,
                valve_ref=VALVE_REF,
                current_kv_m3_h=10.0,
                flow_m3_h=0.6471,
                controlled_circuit_dp_pa=34_605.0,
                implied_valve_dp_bar=0.004188,
                implied_valve_dp_pa=418.8,
                implied_authority=0.012,
            ),
        ),
    )


def resolution(*, approved=False, revision=False):
    return (
        ResolvedPointAcceptedValveCandidateConsequenceDispositionV1(
            ready=True,
            rows=(
                ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1(
                    balancing_point_id=POINT_ID,
                    ready=True,
                    disposition=(
                        "approved_for_later_valve_design"
                        if approved
                        else "valve_candidate_revision_required"
                        if revision
                        else ""
                    ),
                    catalog_id_basis=CATALOG_ID if approved or revision else "",
                    valve_ref_basis=VALVE_REF if approved or revision else "",
                    current_kv_m3_h_basis=(
                        10.0 if approved or revision else None
                    ),
                    approved_for_later_valve_design=approved,
                    valve_candidate_revision_required=revision,
                    status=(
                        "Approved for later detailed valve design"
                        if approved
                        else "Catalogue candidate revision required"
                        if revision
                        else "Manual disposition pending"
                    ),
                ),
            ),
        )
    )


def main() -> None:
    result = (
        build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
            product_duties(),
            consequence(),
            resolution(approved=True),
        )
    )
    assert result.ready is True, result.status
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.envelope_state_id == DETAILED_VALVE_DESIGN_DUTY_AVAILABLE
    assert row.envelope_available is True
    assert row.approved_for_later_valve_design is True
    assert row.balancing_point_id == POINT_ID
    assert row.governed_route_ids == ("route-1",)
    assert row.catalog_id == CATALOG_ID
    assert row.valve_ref == VALVE_REF
    assert row.current_kv_m3_h == 10.0
    assert row.point_flow_kg_s == 0.1794
    assert row.flow_m3_h == 0.6471
    assert row.required_kv == 6.092
    assert row.implied_valve_dp_pa == 418.8
    assert row.controlled_circuit_dp_pa == 34_605.0
    assert row.implied_authority == 0.012
    assert row.design_valve_dp_pa == 2257.3
    assert row.design_authority == 0.061
    assert "not started" in row.status

    pending = (
        build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
            product_duties(),
            consequence(),
            resolution(),
        )
    )
    assert pending.ready is True
    assert pending.rows[0].envelope_state_id == (
        DETAILED_VALVE_DESIGN_DUTY_PENDING
    )
    assert pending.rows[0].envelope_available is False

    revision = (
        build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
            product_duties(),
            consequence(),
            resolution(revision=True),
        )
    )
    assert revision.ready is True
    assert revision.rows[0].envelope_state_id == (
        DETAILED_VALVE_DESIGN_DUTY_REVISION_REQUIRED
    )
    assert revision.rows[0].valve_candidate_revision_required is True
    assert revision.rows[0].envelope_available is False

    blocked = (
        build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
            None,
            consequence(),
            resolution(approved=True),
        )
    )
    assert blocked.ready is False
    assert "H-S49-A" in blocked.blockers[0]

    assert "No committed valve product selection" in result.exclusions
    assert "No valve size, DN, connection or setting selected" in (
        result.exclusions
    )
    assert "No product-derived hydraulic mutation" in result.exclusions
    assert "No ProjectState mutation" in result.exclusions

    print(
        "OK — H-S53-A approved catalogue valve-candidate detailed "
        "design duty envelope passed."
    )


if __name__ == "__main__":
    main()
