# ======================================================================
# HVAC/dev/test_hs48b_manual_point_kvs_acceptance_editor_v1.py
# H-S48-B — Manual point Kvs candidate acceptance editor
# ======================================================================

from pathlib import Path

from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_acceptance_intent_v1 import (
    BalancingPointKvsCandidateAcceptanceIntentV1,
)


def main() -> None:
    intent = BalancingPointKvsCandidateAcceptanceIntentV1()
    intent.accept_candidate(
        balancing_point_id="balancing-point:subleg:example",
        accepted_kvs=6.3,
    )
    assert intent.accepted_by_point_id[
        "balancing-point:subleg:example"
    ].accepted_kvs == 6.3
    assert intent.clear_candidate("balancing-point:subleg:example") is True

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "set_balancing_point_kvs_acceptance_callback" in adapter_source
    assert "set_balancing_point_kvs_candidate_acceptance" in adapter_source
    assert "resolve_balancing_point_kvs_candidate_acceptance_v1(" in adapter_source
    assert "accepted_kvs must be a current H-S47-C candidate" in adapter_source
    assert "hydronic_point_kvs_candidate_acceptance_intent" in adapter_source
    assert "set_balancing_point_kvs_acceptance_editor_rows" in panel_source
    assert "Select a current candidate…" in panel_source
    assert '"action": "accept"' in panel_source
    assert '"action": "clear"' in panel_source
    assert "Accept selected generic Kvs" in panel_source
    assert "select a valve product, size or setting" in panel_source

    # The editor must not expose product or setting choice controls.
    editor_start = panel_source.index(
        "# H-S48-B — Manual point generic-Kvs acceptance editor"
    )
    editor_end = panel_source.index(
        "# H-S27-F — Chosen-basis proportioned readiness summary",
        editor_start,
    )
    editor_source = panel_source[editor_start:editor_end]
    assert "manufacturer" not in editor_source.lower()
    assert "valve product:" not in editor_source.lower()
    assert "valve setting:" not in editor_source.lower()

    print("OK — H-S48-B manual point Kvs acceptance editor passed.")


if __name__ == "__main__":
    main()
