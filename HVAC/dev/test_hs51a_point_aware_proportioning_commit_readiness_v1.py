from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
    KVS_REVISION_REQUIRED,
    ResolvedPointAcceptedKvsConsequenceDispositionRowV1,
    ResolvedPointAcceptedKvsConsequenceDispositionV1,
)
from HVAC.hydronics.proportioning.balancing_point_proportioning_commit_readiness_v1 import (
    GENERIC_KVS_BASIS_APPROVED,
    KVS_REVISION_BLOCKS_COMMIT,
    MANUAL_DISPOSITION_PENDING,
    NO_VALVE_POINT_READY,
    build_point_proportioning_commit_readiness_v1,
)


def main() -> None:
    no_valve = ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
        balancing_point_id="point:no-valve",
        ready=True,
        status="No consequence disposition required — no valve duty",
    )
    approved = ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
        balancing_point_id="point:approved",
        ready=True,
        disposition=APPROVED_FOR_PRODUCT_SEARCH,
        accepted_kvs_basis=10.0,
        approved_for_product_search=True,
        status="Approved for later product search — search not started",
    )
    ready = build_point_proportioning_commit_readiness_v1(
        ResolvedPointAcceptedKvsConsequenceDispositionV1(
            ready=True,
            rows=(no_valve, approved),
        )
    )
    assert ready.ready is True
    assert ready.rows[0].readiness_state_id == NO_VALVE_POINT_READY
    assert ready.rows[1].readiness_state_id == GENERIC_KVS_BASIS_APPROVED
    assert "catalogue/product deferred" in ready.status
    assert "No valve catalogue required" in ready.exclusions

    pending = build_point_proportioning_commit_readiness_v1(
        ResolvedPointAcceptedKvsConsequenceDispositionV1(
            ready=True,
            rows=(
                ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
                    balancing_point_id="point:pending",
                    ready=True,
                    status="Manual consequence disposition pending",
                ),
            ),
        )
    )
    assert pending.ready is False
    assert pending.rows[0].readiness_state_id == MANUAL_DISPOSITION_PENDING

    revision = build_point_proportioning_commit_readiness_v1(
        ResolvedPointAcceptedKvsConsequenceDispositionV1(
            ready=True,
            rows=(
                ResolvedPointAcceptedKvsConsequenceDispositionRowV1(
                    balancing_point_id="point:revision",
                    ready=True,
                    disposition=KVS_REVISION_REQUIRED,
                    accepted_kvs_basis=10.0,
                    kvs_revision_required=True,
                    status="Kvs revision required — no automatic change",
                ),
            ),
        )
    )
    assert revision.ready is False
    assert revision.rows[0].readiness_state_id == KVS_REVISION_BLOCKS_COMMIT

    assert build_point_proportioning_commit_readiness_v1(None).ready is False

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "build_point_proportioning_commit_readiness_v1(" in adapter_source
    assert "_point_proportioning_commit_readiness_v1" in adapter_source
    assert "basic_commit_ready and point_commit_readiness.ready" in adapter_source
    assert "H-S51-A Commit Proportioning blocked" in adapter_source

    print("OK — H-S51-A point-aware proportioning commit readiness passed.")


if __name__ == "__main__":
    main()
