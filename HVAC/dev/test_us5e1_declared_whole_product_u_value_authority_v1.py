from __future__ import annotations

from dataclasses import replace

from HVAC.constructions.physics.declared_whole_product_u_value_authority_v1 import (
    DeclaredWholeProductUValueAcceptanceIntentV1,
    DeclaredWholeProductUValueEvidenceV1,
    build_declared_whole_product_u_value_acceptance_intent_v1,
    resolve_accepted_declared_whole_product_u_value_v1,
)
from HVAC.core.construction_v1 import ConstructionV1
from HVAC.project.project_state import ProjectState


def _accepted(evidence: DeclaredWholeProductUValueEvidenceV1):
    intent = build_declared_whole_product_u_value_acceptance_intent_v1(
        evidence,
        accepted=True,
    )
    return intent, resolve_accepted_declared_whole_product_u_value_v1(
        evidence,
        intent,
    )


def main() -> None:
    window = DeclaredWholeProductUValueEvidenceV1(
        construction_id="USR-WINDOW-DECLARED-001",
        opening_type="WINDOW",
        declared_u_value_W_m2K=1.4,
        source_kind="manufacturer_declaration",
        source_ref="Example window declaration",
        source_version="2026-08",
        notes="Whole-window Uw, not centre-pane Ug",
    )
    window_intent, accepted_window = _accepted(window)
    assert accepted_window.ready
    assert accepted_window.opening_type == "WINDOW"
    assert accepted_window.accepted_u_value_W_m2K == 1.4

    door = DeclaredWholeProductUValueEvidenceV1(
        construction_id="USR-DOOR-DECLARED-001",
        opening_type="door",
        declared_u_value_W_m2K=1.6,
        source_kind="product_schedule",
        source_ref="Example external door schedule",
        source_version="v1",
    )
    door_intent, accepted_door = _accepted(door)
    assert accepted_door.ready
    assert accepted_door.opening_type == "DOOR"
    assert accepted_door.accepted_u_value_W_m2K == 1.6

    invalid = replace(window, declared_u_value_W_m2K=0.0)
    invalid_intent = build_declared_whole_product_u_value_acceptance_intent_v1(
        invalid,
        accepted=True,
    )
    assert not resolve_accepted_declared_whole_product_u_value_v1(
        invalid,
        invalid_intent,
    ).ready

    unsupported = replace(window, opening_type="ROOFLIGHT")
    unsupported_intent = build_declared_whole_product_u_value_acceptance_intent_v1(
        unsupported,
        accepted=True,
    )
    assert not resolve_accepted_declared_whole_product_u_value_v1(
        unsupported,
        unsupported_intent,
    ).ready

    not_accepted = build_declared_whole_product_u_value_acceptance_intent_v1(
        window,
        accepted=False,
    )
    assert not resolve_accepted_declared_whole_product_u_value_v1(
        window,
        not_accepted,
    ).ready

    changed_after_acceptance = replace(window, declared_u_value_W_m2K=1.2)
    stale = resolve_accepted_declared_whole_product_u_value_v1(
        changed_after_acceptance,
        window_intent,
    )
    assert not stale.ready
    assert any("stale" in blocker for blocker in stale.blockers)

    wrong_identity = replace(
        window_intent,
        construction_id="ANOTHER-CONSTRUCTION",
    )
    assert not resolve_accepted_declared_whole_product_u_value_v1(
        window,
        wrong_identity,
    ).ready

    evidence_round_trip = DeclaredWholeProductUValueEvidenceV1.from_dict(
        window.to_dict()
    )
    intent_round_trip = DeclaredWholeProductUValueAcceptanceIntentV1.from_dict(
        window_intent.to_dict()
    )
    assert resolve_accepted_declared_whole_product_u_value_v1(
        evidence_round_trip,
        intent_round_trip,
    ).ready

    construction = ConstructionV1(
        construction_id=window.construction_id,
        name="Example declared whole window",
        u_value_W_m2K=float(accepted_window.accepted_u_value_W_m2K),
        declared_whole_product_u_value_evidence=window.to_dict(),
        declared_whole_product_u_value_acceptance=window_intent.to_dict(),
    )
    project = ProjectState(project_id="us5e1", name="U-S5E1")
    project.constructions = {construction.construction_id: construction}
    restored = ProjectState.from_dict(project.to_dict())
    restored_construction = restored.constructions[construction.construction_id]
    assert restored_construction.u_value_W_m2K == 1.4
    assert (
        restored_construction.declared_whole_product_u_value_evidence
        == window.to_dict()
    )
    assert (
        restored_construction.declared_whole_product_u_value_acceptance
        == window_intent.to_dict()
    )

    legacy = ConstructionV1(
        construction_id="LEGACY-WINDOW",
        name="Legacy compatible window",
        u_value_W_m2K=2.8,
    )
    assert legacy.declared_whole_product_u_value_evidence is None
    assert legacy.declared_whole_product_u_value_acceptance is None

    print(
        "OK — U-S5E1 declared whole-window Uw and whole-door Ud "
        "acceptance authority and persistence passed."
    )


if __name__ == "__main__":
    main()
