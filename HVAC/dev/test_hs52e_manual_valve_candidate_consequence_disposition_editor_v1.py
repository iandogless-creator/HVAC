# ======================================================================
# H-S52-E — Manual valve-candidate consequence disposition editor
# ======================================================================

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_consequence_disposition_intent_v1 import (
    APPROVED_FOR_LATER_VALVE_DESIGN,
    ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1,
    ResolvedPointAcceptedValveCandidateConsequenceDispositionV1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    ResolvedPointValveCandidateAcceptanceRowV1,
    ResolvedPointValveCandidateAcceptanceV1,
)
from HVAC.project.project_state import ProjectState


POINT_ID = "balancing-point:subleg:test"
CATALOG_ID = "catalog-v1"
VALVE_REF = "VALVE-KV-10"


def main() -> None:
    candidates = SimpleNamespace(
        catalog_id=CATALOG_ID,
        rows=(
            SimpleNamespace(
                balancing_point_id=POINT_ID,
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
    acceptance = ResolvedPointValveCandidateAcceptanceV1(
        ready=True,
        rows=(
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id=POINT_ID,
                accepted=True,
                catalog_id=CATALOG_ID,
                valve_ref=VALVE_REF,
                current_kv_m3_h=10.0,
                status="Manual valve-candidate identity resolved",
            ),
        ),
    )
    consequence_row = SimpleNamespace(
        balancing_point_id=POINT_ID,
        consequence_available=True,
        catalog_id=CATALOG_ID,
        valve_ref=VALVE_REF,
        current_kv_m3_h=10.0,
        implied_valve_dp_pa=1000.0,
        implied_authority=0.01,
        status="Catalogue consequence available",
        blockers=(),
    )
    consequence = SimpleNamespace(
        ready=True,
        rows=(consequence_row,),
        blockers=(),
    )
    disposition = (
        ResolvedPointAcceptedValveCandidateConsequenceDispositionV1(
            ready=True,
            rows=(
                ResolvedPointAcceptedValveCandidateConsequenceDispositionRowV1(
                    balancing_point_id=POINT_ID,
                    ready=True,
                    disposition=APPROVED_FOR_LATER_VALVE_DESIGN,
                    catalog_id_basis=CATALOG_ID,
                    valve_ref_basis=VALVE_REF,
                    current_kv_m3_h_basis=10.0,
                    approved_for_later_valve_design=True,
                    status=(
                        "Approved for later detailed valve design — "
                        "no valve size or setting committed"
                    ),
                ),
            ),
        )
    )
    rows = (
        HydronicsSchematicPanelAdapter
        ._build_point_valve_candidate_acceptance_editor_rows_v1(
            candidates,
            acceptance,
            consequence,
            disposition,
        )
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["consequence_available"] is True
    assert row["consequence_disposition"] == (
        APPROVED_FOR_LATER_VALVE_DESIGN
    )
    assert row["approved_for_later_valve_design"] is True
    assert "later detailed valve design" in (
        row["consequence_disposition_status"]
    )

    project = ProjectState(project_id="hs52e", name="H-S52-E")
    stub = SimpleNamespace(
        _project_state=project,
        _context=None,
        _balancing_point_accepted_valve_candidate_hydraulic_consequence_preview=(
            consequence
        ),
    )
    refreshes = []
    stub.refresh = lambda: refreshes.append(True)
    HydronicsSchematicPanelAdapter.set_point_valve_candidate_consequence_disposition(
        stub,
        {
            "action": "set",
            "balancing_point_id": POINT_ID,
            "disposition": APPROVED_FOR_LATER_VALVE_DESIGN,
        },
    )
    intent = (
        project
        .hydronic_point_accepted_valve_candidate_consequence_disposition_intent
    )
    assert intent is not None
    entry = intent.disposition_by_point_id[POINT_ID]
    assert entry.catalog_id_basis == CATALOG_ID
    assert entry.valve_ref_basis == VALVE_REF
    assert entry.current_kv_m3_h_basis == 10.0
    assert refreshes

    HydronicsSchematicPanelAdapter.set_point_valve_candidate_consequence_disposition(
        stub,
        {
            "action": "clear",
            "balancing_point_id": POINT_ID,
        },
    )
    assert POINT_ID not in intent.disposition_by_point_id

    unavailable_stub = SimpleNamespace(
        _project_state=ProjectState(
            project_id="blocked",
            name="Blocked",
        ),
        _context=None,
        _balancing_point_accepted_valve_candidate_hydraulic_consequence_preview=(
            SimpleNamespace(
                rows=(
                    SimpleNamespace(
                        balancing_point_id=POINT_ID,
                        consequence_available=False,
                    ),
                ),
            )
        ),
        refresh=lambda: None,
    )
    try:
        HydronicsSchematicPanelAdapter.set_point_valve_candidate_consequence_disposition(
            unavailable_stub,
            {
                "action": "set",
                "balancing_point_id": POINT_ID,
                "disposition": APPROVED_FOR_LATER_VALVE_DESIGN,
            },
        )
    except ValueError as exc:
        assert "H-S52-C" in str(exc)
    else:
        raise AssertionError("Unavailable H-S52-C consequence was accepted")

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert (
        "resolve_balancing_point_accepted_valve_candidate_"
        "consequence_disposition_v1(" in adapter_source
    )
    assert (
        "set_point_valve_candidate_consequence_disposition_callback"
        in adapter_source
    )
    assert "Approve for later detailed valve design" in panel_source
    assert (
        "Require catalogue valve-candidate revision" in panel_source
    )
    assert "Apply consequence disposition" in panel_source
    assert "Clear consequence disposition" in panel_source
    assert "Consequence disposition:" in panel_source

    print(
        "OK — H-S52-E manual accepted valve-candidate consequence "
        "disposition editor passed."
    )


if __name__ == "__main__":
    main()
