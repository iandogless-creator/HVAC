# ======================================================================
# HVAC/hydronics/probes/probe_emitter_projectstate_roundtrip_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.emitter_v1 import EmitterV1


def main() -> None:
    print()
    print("Hydronics H-L — ProjectState emitter round-trip probe")
    print()

    project = ProjectState(
        project_id="PROBE-HYDRONICS-H-L",
        name="Hydronics H-L Round Trip Probe",
    )

    emitter_id = "emitter-test-room-001-001"

    project.emitters[emitter_id] = EmitterV1(
        emitter_id=emitter_id,
        room_id="room-001",
        name="Test radiator",
        emitter_type="radiator",
        design_output_W=500.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
        room_temp_C=21.0,
        notes="Round-trip persistence probe",
    )

    data = project.to_dict()
    restored = ProjectState.from_dict(data)

    restored_emitter = restored.emitters.get(emitter_id)

    print(f"Original emitters: {len(project.emitters)}")
    print(f"Restored emitters: {len(restored.emitters)}")

    if restored_emitter is None:
        raise AssertionError("Restored emitter missing")

    print(f"Emitter ID:        {restored_emitter.emitter_id}")
    print(f"Room ID:           {restored_emitter.room_id}")
    print(f"Type:              {restored_emitter.emitter_type}")
    print(f"Output W:          {restored_emitter.design_output_W}")
    print(f"Flow temp C:       {restored_emitter.flow_temp_C}")
    print(f"Return temp C:     {restored_emitter.return_temp_C}")

    assert len(restored.emitters) == 1
    assert restored_emitter.emitter_id == emitter_id
    assert restored_emitter.room_id == "room-001"
    assert restored_emitter.emitter_type == "radiator"
    assert restored_emitter.design_output_W == 500.0
    assert restored_emitter.flow_temp_C == 70.0
    assert restored_emitter.return_temp_C == 50.0
    assert restored_emitter.room_temp_C == 21.0

    print()
    print("OK — ProjectState emitter round-trip passed.")
    print()


if __name__ == "__main__":
    main()
