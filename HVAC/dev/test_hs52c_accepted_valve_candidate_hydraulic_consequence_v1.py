# ======================================================================
# H-S52-C — Accepted catalogue valve-candidate hydraulic consequence
# ======================================================================

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE,
    ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_PENDING,
    NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED,
    build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    ResolvedPointValveCandidateAcceptanceRowV1,
    ResolvedPointValveCandidateAcceptanceV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    BalancingPointValveProductSearchDutyEnvelopeRowV1,
    BalancingPointValveProductSearchDutyEnvelopeV1,
)


CATALOG_ID = "catalog-v1"
VALVE_REF = "VALVE-KV-10"


def main() -> None:
    envelopes = BalancingPointValveProductSearchDutyEnvelopeV1(
        ready=True,
        rows=(
            BalancingPointValveProductSearchDutyEnvelopeRowV1(
                balancing_point_id="point-accepted",
                ready=True,
                product_search_required=True,
                envelope_available=True,
                approved_for_product_search=True,
                flow_m3_h=1.0,
                controlled_circuit_dp_pa=99_000.0,
            ),
            BalancingPointValveProductSearchDutyEnvelopeRowV1(
                balancing_point_id="point-pending",
                ready=True,
                product_search_required=True,
                envelope_available=True,
                approved_for_product_search=True,
                flow_m3_h=0.5,
                controlled_circuit_dp_pa=20_000.0,
            ),
            BalancingPointValveProductSearchDutyEnvelopeRowV1(
                balancing_point_id="point-not-required",
                ready=True,
                product_search_required=False,
            ),
        ),
    )
    acceptance = ResolvedPointValveCandidateAcceptanceV1(
        ready=True,
        rows=(
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id="point-accepted",
                accepted=True,
                catalog_id=CATALOG_ID,
                valve_ref=VALVE_REF,
                current_kv_m3_h=10.0,
            ),
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id="point-pending",
                accepted=False,
            ),
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id="point-not-required",
                accepted=False,
            ),
        ),
    )

    result = (
        build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1(
            envelopes,
            acceptance,
        )
    )
    assert result.ready is True, result.status
    by_id = {row.balancing_point_id: row for row in result.rows}
    accepted = by_id["point-accepted"]
    assert accepted.consequence_state_id == (
        ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_AVAILABLE
    )
    assert accepted.consequence_available is True
    assert accepted.catalog_id == CATALOG_ID
    assert accepted.valve_ref == VALVE_REF
    assert accepted.current_kv_m3_h == 10.0
    assert abs(accepted.implied_valve_dp_pa - 1_000.0) < 1e-9
    assert abs(accepted.implied_authority - 0.01) < 1e-12
    assert by_id["point-pending"].consequence_state_id == (
        ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_PENDING
    )
    assert by_id["point-not-required"].consequence_state_id == (
        NO_ACCEPTED_VALVE_CANDIDATE_CONSEQUENCE_REQUIRED
    )
    assert "No product-derived hydraulic mutation" in result.exclusions
    assert "No ProjectState mutation" in result.exclusions

    candidate_evidence = SimpleNamespace(
        catalog_id=CATALOG_ID,
        rows=(
            SimpleNamespace(
                balancing_point_id="point-accepted",
                catalog_id=CATALOG_ID,
                candidates=(
                    SimpleNamespace(
                        catalog_id=CATALOG_ID,
                        valve_ref=VALVE_REF,
                        kv_m3_h=10.0,
                        note="Current catalogue evidence",
                    ),
                ),
            ),
        ),
    )
    editor_rows = (
        HydronicsSchematicPanelAdapter
        ._build_point_valve_candidate_acceptance_editor_rows_v1(
            candidate_evidence,
            acceptance,
            result,
        )
    )
    assert len(editor_rows) == 1
    editor = editor_rows[0]
    assert editor["consequence_available"] is True
    assert editor["current_catalogue_kv"] == "10.000"
    assert editor["catalogue_implied_valve_dp"] == "1000.0 Pa"
    assert editor["catalogue_implied_authority"] == "0.010"

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_balancing_point_accepted_valve_candidate_"
        "hydraulic_consequence_v1(" in adapter_source
    )
    assert "point_valve_candidate_consequence" in adapter_source
    assert "Hydraulic consequence:" in panel_source
    assert "_point_valve_candidate_consequence_label" in panel_source
    assert "Current catalogue Kv" in panel_source
    assert "preview only" in panel_source

    print(
        "OK — H-S52-C accepted catalogue valve-candidate hydraulic "
        "consequence evidence passed."
    )


if __name__ == "__main__":
    main()
