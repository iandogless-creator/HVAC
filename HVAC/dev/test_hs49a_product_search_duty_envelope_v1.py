from dataclasses import MISSING, fields
from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    ResolvedPointAcceptedKvsConsequenceDispositionRowV1,
    ResolvedPointAcceptedKvsConsequenceDispositionV1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
    BalancingPointAcceptedKvsHydraulicConsequenceRowV1,
    BalancingPointAcceptedKvsHydraulicConsequenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    BalancingPointKvsCandidateUtilisationEvidenceRowV1,
    BalancingPointKvsCandidateUtilisationEvidenceV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    PRODUCT_SEARCH_ENVELOPE_AVAILABLE,
    PRODUCT_SEARCH_ENVELOPE_PENDING,
    PRODUCT_SEARCH_ENVELOPE_REVISION_REQUIRED,
    build_balancing_point_valve_product_search_duty_envelope_v1,
)


def make_dataclass(cls, **overrides):
    obj = object.__new__(cls)
    for field in fields(cls):
        if field.name in overrides:
            value = overrides[field.name]
        elif field.default is not MISSING:
            value = field.default
        elif field.default_factory is not MISSING:
            value = field.default_factory()
        else:
            value = False if field.type is bool else ""
        object.__setattr__(obj, field.name, value)
    return obj


def main() -> None:
    point = "balancing-point:subleg:approved"
    utilisation_row = make_dataclass(
        BalancingPointKvsCandidateUtilisationEvidenceRowV1,
        balancing_point_id=point,
        point_scope="subleg",
        point_role="common_route_downstream",
        label="Approved downstream point",
        downstream_route_ids=("route-1",),
        is_route_exclusive=True,
        ready=True,
        point_flow_kg_s=0.1794,
        flow_m3_h=0.6471,
        design_valve_dp_pa=1128.6,
        authority=0.074,
        required_kv=6.092,
        kvs_series_id="generic_preferred_kvs_series_v1",
        kvs_candidates=(6.3, 10.0, 16.0),
    )
    utilisation = BalancingPointKvsCandidateUtilisationEvidenceV1(
        ready=True, rows=(utilisation_row,)
    )
    consequence_row = BalancingPointAcceptedKvsHydraulicConsequenceRowV1(
        balancing_point_id=point,
        ready=True,
        consequence_state_id=ACCEPTED_KVS_CONSEQUENCE_AVAILABLE,
        consequence_available=True,
        accepted=True,
        accepted_kvs=10.0,
        flow_m3_h=0.6471,
        controlled_circuit_dp_pa=14199.0,
        implied_valve_dp_bar=0.004188,
        implied_valve_dp_pa=418.8,
        implied_authority=0.029,
    )
    consequence = BalancingPointAcceptedKvsHydraulicConsequenceV1(
        ready=True, rows=(consequence_row,)
    )
    approved_row = ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
        balancing_point_id=point,
        ready=True,
        disposition="approved_for_product_search",
        accepted_kvs_basis=10.0,
        approved_for_product_search=True,
        status="Approved for later product search — search not started",
    )
    approved = ResolvedPointAcceptedKvsConsequenceDispositionV1(
        ready=True, rows=(approved_row,)
    )
    result = build_balancing_point_valve_product_search_duty_envelope_v1(
        utilisation, consequence, approved
    )
    assert result.ready is True
    row = result.rows[0]
    assert row.envelope_state_id == PRODUCT_SEARCH_ENVELOPE_AVAILABLE
    assert row.envelope_available is True
    assert row.balancing_point_id == point
    assert row.governed_route_ids == ("route-1",)
    assert row.accepted_kvs == 10.0
    assert row.implied_valve_dp_pa == 418.8
    assert row.implied_authority == 0.029
    assert row.design_authority == 0.074
    assert "search not started" in row.status

    pending = ResolvedPointAcceptedKvsConsequenceDispositionV1(
        ready=True,
        rows=(ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
            balancing_point_id=point,
            ready=True,
            status="Manual consequence disposition pending",
        ),),
    )
    pending_result = build_balancing_point_valve_product_search_duty_envelope_v1(
        utilisation, consequence, pending
    )
    assert pending_result.rows[0].envelope_state_id == PRODUCT_SEARCH_ENVELOPE_PENDING
    assert pending_result.rows[0].envelope_available is False

    revision = ResolvedPointAcceptedKvsConsequenceDispositionV1(
        ready=True,
        rows=(ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
            balancing_point_id=point,
            ready=True,
            disposition="kvs_revision_required",
            accepted_kvs_basis=10.0,
            kvs_revision_required=True,
            status="Kvs revision required — no automatic change",
        ),),
    )
    revision_result = build_balancing_point_valve_product_search_duty_envelope_v1(
        utilisation, consequence, revision
    )
    assert revision_result.rows[0].envelope_state_id == PRODUCT_SEARCH_ENVELOPE_REVISION_REQUIRED
    assert revision_result.rows[0].envelope_available is False

    assert "No valve product selected" in result.exclusions
    assert "No product search started" in result.exclusions
    adapter = Path("HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py").read_text()
    panel = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py").read_text()
    assert "build_balancing_point_valve_product_search_duty_envelope_v1(" in adapter
    assert "set_product_search_duty_envelope_rows" in adapter
    assert "Approved point valve product-search duty envelopes" in panel
    assert "No valve product selected" in Path(
        "HVAC/hydronics/proportioning/balancing_point_valve_product_search_duty_envelope_v1.py"
    ).read_text()

    print("OK — H-S49-A approved point valve product-search duty envelope passed.")


if __name__ == "__main__":
    main()
