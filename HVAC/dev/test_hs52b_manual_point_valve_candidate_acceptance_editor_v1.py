# ======================================================================
# H-S52-B — Manual point valve-candidate acceptance editor
# ======================================================================

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    ResolvedPointValveCandidateAcceptanceRowV1,
    ResolvedPointValveCandidateAcceptanceV1,
)
from HVAC.project.project_state import ProjectState


POINT_ID = "balancing-point:subleg:test"
CATALOG_ID = "local-generic-valves-v1"
VALVE_REF = "LOCAL-GENERIC-KV-6.3"


def _candidate(ref: str = VALVE_REF):
    return SimpleNamespace(
        catalog_id=CATALOG_ID,
        valve_ref=ref,
        kv_m3_h=6.3,
        note="Generic commissioning valve",
    )


def _evidence():
    return SimpleNamespace(
        ready=True,
        catalog_id=CATALOG_ID,
        blockers=(),
        rows=(
            SimpleNamespace(
                balancing_point_id=POINT_ID,
                catalog_id=CATALOG_ID,
                candidates=(_candidate(),),
            ),
        ),
    )


def main() -> None:
    evidence = _evidence()
    pending = ResolvedPointValveCandidateAcceptanceV1(
        ready=True,
        rows=(
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id=POINT_ID,
                catalog_id=CATALOG_ID,
                status="Manual valve-candidate acceptance pending",
            ),
        ),
    )
    rows = (
        HydronicsSchematicPanelAdapter
        ._build_point_valve_candidate_acceptance_editor_rows_v1(
            evidence,
            pending,
        )
    )
    assert len(rows) == 1
    assert rows[0]["balancing_point_id"] == POINT_ID
    assert rows[0]["candidates"][0]["valve_ref"] == VALVE_REF
    assert rows[0]["has_acceptance"] is False

    accepted = ResolvedPointValveCandidateAcceptanceV1(
        ready=True,
        rows=(
            ResolvedPointValveCandidateAcceptanceRowV1(
                balancing_point_id=POINT_ID,
                accepted=True,
                catalog_id=CATALOG_ID,
                valve_ref=VALVE_REF,
                current_kv_m3_h=6.3,
                status="Manual valve-candidate identity resolved",
            ),
        ),
    )
    accepted_rows = (
        HydronicsSchematicPanelAdapter
        ._build_point_valve_candidate_acceptance_editor_rows_v1(
            evidence,
            accepted,
        )
    )
    assert accepted_rows[0]["has_acceptance"] is True
    assert accepted_rows[0]["accepted_valve_ref"] == VALVE_REF

    stub = SimpleNamespace(
        _project_state=ProjectState(project_id="hs52b", name="H-S52-B"),
        _context=None,
        _balancing_point_valve_catalogue_candidate_match_evidence=evidence,
    )
    refreshes = []
    stub.refresh = lambda: refreshes.append(True)
    HydronicsSchematicPanelAdapter.set_point_valve_candidate_acceptance(
        stub,
        {
            "action": "accept",
            "balancing_point_id": POINT_ID,
            "catalog_id": CATALOG_ID,
            "valve_ref": VALVE_REF,
        },
    )
    intent = (
        stub._project_state
        .hydronic_point_valve_candidate_acceptance_intent
    )
    assert intent is not None
    assert intent.accepted_by_point_id[POINT_ID].valve_ref == VALVE_REF
    assert refreshes

    try:
        HydronicsSchematicPanelAdapter.set_point_valve_candidate_acceptance(
            stub,
            {
                "action": "accept",
                "balancing_point_id": POINT_ID,
                "catalog_id": CATALOG_ID,
                "valve_ref": "NOT-A-CURRENT-CANDIDATE",
            },
        )
    except ValueError as exc:
        assert "current H-S50-A candidate" in str(exc)
    else:
        raise AssertionError("Stale valve reference was accepted")

    HydronicsSchematicPanelAdapter.set_point_valve_candidate_acceptance(
        stub,
        {
            "action": "clear",
            "balancing_point_id": POINT_ID,
        },
    )
    assert POINT_ID not in intent.accepted_by_point_id

    # H-S52-B1: PySide may return QVariant sequence data as a list.
    # A visible selection must enable Apply and emit the stable identity.
    class _Combo:
        def currentData(self):
            return [CATALOG_ID, VALVE_REF]

    class _Button:
        enabled = False

        def setEnabled(self, enabled):
            self.enabled = bool(enabled)

    panel_stub = SimpleNamespace(
        _point_valve_candidate_acceptance_selected_point_id=POINT_ID,
        _point_valve_candidate_acceptance_candidate_combo=_Combo(),
        _point_valve_candidate_acceptance_apply_button=_Button(),
    )
    HydronicsSchematicPanel._on_point_valve_candidate_acceptance_candidate_changed_v1(
        panel_stub
    )
    assert panel_stub._point_valve_candidate_acceptance_apply_button.enabled

    emitted = []
    panel_stub._point_valve_candidate_acceptance_callback = emitted.append
    HydronicsSchematicPanel._on_apply_point_valve_candidate_acceptance_v1(
        panel_stub
    )
    assert emitted == [{
        "action": "accept",
        "balancing_point_id": POINT_ID,
        "catalog_id": CATALOG_ID,
        "valve_ref": VALVE_REF,
    }]

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "resolve_balancing_point_valve_candidate_acceptance_v1(" in (
        adapter_source
    )
    assert "set_point_valve_candidate_acceptance_callback" in adapter_source
    assert "must identify a current H-S50-A candidate" in adapter_source
    assert (
        "Manual point valve-candidate acceptance — design intent"
        in panel_source
    )
    assert "Select a current candidate…" in panel_source
    assert '"action": "accept"' in panel_source
    assert '"action": "clear"' in panel_source
    assert "— unavailable" in panel_source
    assert "does not commit" in panel_source
    assert "product hydraulics" in panel_source

    editor_start = panel_source.index(
        "# H-S52-B — manual point valve-candidate acceptance editor"
    )
    editor_end = panel_source.index(
        "# H-S27-F — Chosen-basis proportioned readiness summary",
        editor_start,
    )
    editor_source = panel_source[editor_start:editor_end]
    assert "valve setting:" not in editor_source.lower()
    assert "pump" not in editor_source.lower()
    assert "pipe resizing" not in editor_source.lower()

    print(
        "OK — H-S52-B manual point valve-candidate acceptance editor "
        "passed."
    )


if __name__ == "__main__":
    main()
