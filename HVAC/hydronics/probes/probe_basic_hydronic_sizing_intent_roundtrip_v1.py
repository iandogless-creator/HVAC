# ======================================================================
# HVAC/hydronics/probes/probe_basic_hydronic_sizing_intent_roundtrip_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)


# ======================================================================
# Probe
# ======================================================================

def main() -> None:
    print()
    print("Hydronics H-N3 — basic hydronic sizing intent round-trip probe")
    print()

    # --------------------------------------------------
    # Original ProjectState
    # --------------------------------------------------
    project = ProjectState(
        project_id="DEV-HYD-HN3-001",
        name="Hydronics H-N3 Probe Project",
    )

    project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1(
        basis_mode="INDEX_LENGTH",
        index_room_id="room-001",
        index_emitter_id="emitter-rad-room-001-001",
        total_index_length_m=30.0,
        nominal_pressure_gradient_Pa_per_m=250.0,
        length_source="user",
        pressure_gradient_source="default",
        notes="Probe intent only — no pipe sizing.",
    )

    # --------------------------------------------------
    # Round trip
    # --------------------------------------------------
    data = project.to_dict()
    restored = ProjectState.from_dict(data)

    intent = restored.basic_hydronic_sizing_intent

    if intent is None:
        raise AssertionError("basic_hydronic_sizing_intent was not restored")

    print(f"Project ID:          {restored.project_id}")
    print(f"Project name:        {restored.name}")
    print()
    print(f"Basis mode:          {intent.basis_mode}")
    print(f"Index room ID:       {intent.index_room_id}")
    print(f"Index emitter ID:    {intent.index_emitter_id}")
    print(f"Total index length:  {intent.total_index_length_m} m")
    print(f"Nominal gradient:    {intent.nominal_pressure_gradient_Pa_per_m} Pa/m")
    print(f"Length source:       {intent.length_source}")
    print(f"Gradient source:     {intent.pressure_gradient_source}")
    print(f"Notes:               {intent.notes}")

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------
    assert intent.basis_mode == "INDEX_LENGTH"
    assert intent.index_room_id == "room-001"
    assert intent.index_emitter_id == "emitter-rad-room-001-001"
    assert intent.total_index_length_m == 30.0
    assert intent.nominal_pressure_gradient_Pa_per_m == 250.0
    assert intent.length_source == "user"
    assert intent.pressure_gradient_source == "default"
    assert intent.notes == "Probe intent only — no pipe sizing."

    print()
    print("OK — basic hydronic sizing intent round-trip passed.")
    print()


if __name__ == "__main__":
    main()