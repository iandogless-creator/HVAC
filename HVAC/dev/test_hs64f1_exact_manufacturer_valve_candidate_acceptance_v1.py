# ======================================================================
# H-S64-F1 — Exact manufacturer valve-candidate acceptance freshness
# ======================================================================

from dataclasses import replace

from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_acceptance_intent_v1 import (
    BalancingPointManufacturerValveCandidateAcceptanceIntentV1,
    balancing_point_manufacturer_valve_candidate_acceptance_intent_from_dict_v1,
    balancing_point_manufacturer_valve_candidate_acceptance_intent_to_dict_v1,
    build_manufacturer_valve_candidate_comparison_fingerprint_v1,
    resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_comparison_v1 import (
    MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
    BalancingPointManufacturerValveCandidateComparisonRowV1,
    BalancingPointManufacturerValveCandidateComparisonV1,
    ManufacturerValveCandidateComparisonEvidenceV1,
)
from HVAC.project.project_state import ProjectState


POINT_ID = "balancing-point:subleg:hs64f1"
CATALOG_ID = "manufacturer-products-v1"
CATALOG_REVISION = "2026-08-02"
STANDARD_REF = "STANDARD-20"


def _candidate(
    valve_ref: str = STANDARD_REF,
    *,
    cost_band_id: str = "standard",
    product_kvs: float = 10.0,
    compatible: bool = True,
) -> ManufacturerValveCandidateComparisonEvidenceV1:
    return ManufacturerValveCandidateComparisonEvidenceV1(
        valve_ref=valve_ref,
        manufacturer_name=f"Example {cost_band_id.title()} Manufacturer",
        product_family="Example balancing valves",
        model_name=f"Example {valve_ref}",
        valve_type_id="static_balancing_valve",
        nominal_dn=20,
        connection_type="threaded",
        cost_band_id=cost_band_id,
        approved_current_kv_m3_h=10.0,
        product_kvs_m3_h=product_kvs,
        kvs_basis_matches=compatible,
        required_kv=6.0,
        target_kv_bracketed=compatible,
        lower_setting_value=1.0,
        lower_setting_kv_m3_h=4.0,
        upper_setting_value=2.0,
        upper_setting_kv_m3_h=7.0,
        compatible=compatible,
        status=("Compatible" if compatible else "Not compatible"),
    )


def _row(
    *candidates: ManufacturerValveCandidateComparisonEvidenceV1,
    revision: str = CATALOG_REVISION,
    required_kv: float = 6.0,
) -> BalancingPointManufacturerValveCandidateComparisonRowV1:
    rows = candidates or (
        _candidate(),
        _candidate("BUDGET-20", cost_band_id="budget"),
        _candidate("PREMIUM-20", cost_band_id="premium"),
    )
    return BalancingPointManufacturerValveCandidateComparisonRowV1(
        balancing_point_id=POINT_ID,
        ready=True,
        comparison_state_id=MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
        comparison_required=True,
        comparison_available=True,
        approved_basis_catalog_id="generic-valves-v1",
        approved_basis_valve_ref="GENERIC-KVS-10",
        approved_current_kv_m3_h=10.0,
        required_kv=required_kv,
        product_catalog_id=CATALOG_ID,
        product_catalog_revision=revision,
        candidates=tuple(rows),
        compatible_candidate_count=sum(c.compatible for c in rows),
        standard_candidate_count=sum(
            c.compatible and c.cost_band_id == "standard" for c in rows
        ),
        budget_candidate_count=sum(
            c.compatible and c.cost_band_id == "budget" for c in rows
        ),
        premium_candidate_count=sum(
            c.compatible and c.cost_band_id == "premium" for c in rows
        ),
        status="Manufacturer comparison available; no ranking",
    )


def _comparison(row) -> BalancingPointManufacturerValveCandidateComparisonV1:
    return BalancingPointManufacturerValveCandidateComparisonV1(
        ready=True,
        status="Ready",
        rows=(row,),
    )


def main() -> None:
    row = _row()
    standard = row.candidates[0]
    fingerprint = (
        build_manufacturer_valve_candidate_comparison_fingerprint_v1(
            row,
            standard,
        )
    )
    assert len(fingerprint) == 64

    intent = BalancingPointManufacturerValveCandidateAcceptanceIntentV1()
    intent.accept_candidate(
        balancing_point_id=POINT_ID,
        product_catalog_id=CATALOG_ID,
        product_catalog_revision=CATALOG_REVISION,
        valve_ref=STANDARD_REF,
        comparison_fingerprint=fingerprint,
    )
    resolved = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(row),
        )
    )
    repeated = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(row),
        )
    )
    assert resolved == repeated
    assert resolved.ready is True, resolved.status
    assert resolved.rows[0].accepted is True
    assert resolved.rows[0].valve_ref == STANDARD_REF
    assert resolved.rows[0].cost_band_id == "standard"
    assert "no preset or hydraulics committed" in resolved.rows[0].status
    assert "No valve preset or setting selected" in resolved.exclusions
    assert (
        "No premium, standard or budget ranking or recommendation"
        in resolved.exclusions
    )

    pending = resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
        None,
        _comparison(row),
    )
    assert pending.ready is True
    assert pending.rows[0].accepted is False
    assert "pending" in pending.rows[0].status

    stale_revision = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(_row(revision="2026-08-03")),
        )
    )
    assert stale_revision.ready is False
    assert "revision does not match" in stale_revision.status

    changed_selected = replace(standard, product_kvs_m3_h=10.1)
    stale_product = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(_row(changed_selected, *row.candidates[1:])),
        )
    )
    assert stale_product.ready is False
    assert "fingerprint does not match" in stale_product.status

    # The choice was made from the complete comparison set. Adding or
    # removing another tier therefore requires a fresh manual review.
    stale_comparison_set = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(_row(*row.candidates[:2])),
        )
    )
    assert stale_comparison_set.ready is False

    stale_duty = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(_row(required_kv=6.1)),
        )
    )
    assert stale_duty.ready is False

    incompatible_standard = replace(
        standard,
        compatible=False,
        target_kv_bracketed=False,
    )
    stale_compatibility = (
        resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1(
            intent,
            _comparison(_row(incompatible_standard, *row.candidates[1:])),
        )
    )
    assert stale_compatibility.ready is False
    assert "no longer compatible" in stale_compatibility.status
    assert build_manufacturer_valve_candidate_comparison_fingerprint_v1(
        _row(incompatible_standard),
        incompatible_standard,
    ) == ""

    payload = (
        balancing_point_manufacturer_valve_candidate_acceptance_intent_to_dict_v1(
            intent
        )
    )
    restored = (
        balancing_point_manufacturer_valve_candidate_acceptance_intent_from_dict_v1(
            payload
        )
    )
    assert restored == intent
    assert payload["accepted_by_point_id"][POINT_ID][
        "comparison_fingerprint"
    ] == fingerprint

    project = ProjectState(project_id="hs64f1", name="H-S64-F1")
    project.hydronic_point_manufacturer_valve_candidate_acceptance_intent = intent
    restored_project = ProjectState.from_dict(project.to_dict())
    assert (
        restored_project.hydronic_point_manufacturer_valve_candidate_acceptance_intent
        == intent
    )
    blank = ProjectState.from_dict(
        ProjectState(project_id="blank", name="Blank").to_dict()
    )
    assert (
        blank.hydronic_point_manufacturer_valve_candidate_acceptance_intent
        is None
    )

    print(
        "OK — H-S64-F1 exact manufacturer valve-candidate manual "
        "acceptance and comparison freshness passed."
    )


if __name__ == "__main__":
    main()
