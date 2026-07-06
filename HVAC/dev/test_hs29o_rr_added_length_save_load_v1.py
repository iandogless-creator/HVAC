from __future__ import annotations

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    ReturnArrangementIntentV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    intent = ReturnArrangementIntentV1()
    intent.rr_added_length_basis_mode = "manual_allowance"
    intent.rr_added_length_m = 4.30

    state = ProjectState(
        project_id="hs29o-rr-added-length-persistence",
        name="H-S29-O RR added length persistence",
    )
    state.hydronic_return_arrangement_intent = intent

    payload = state.to_dict()

    raw_intent = payload.get("hydronic_return_arrangement_intent") or {}

    assert raw_intent.get("rr_added_length_basis_mode") == "manual_allowance"
    assert abs(float(raw_intent.get("rr_added_length_m")) - 4.30) < 0.0001

    restored = ProjectState.from_dict(payload)
    restored_intent = restored.hydronic_return_arrangement_intent

    assert restored_intent is not None
    assert restored_intent.rr_added_length_basis_mode == "manual_allowance"
    assert abs(float(restored_intent.rr_added_length_m) - 4.30) < 0.0001

    assert not hasattr(restored, "rr_added_length_basis_mode")
    assert not hasattr(restored, "rr_added_length_m")

    print("OK — H-S29-O RR added length save/load persistence passed.")


if __name__ == "__main__":
    main()
