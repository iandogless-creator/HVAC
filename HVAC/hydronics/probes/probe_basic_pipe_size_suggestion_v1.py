# ======================================================================
# HVAC/hydronics/probes/probe_basic_pipe_size_suggestion_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.core.room_geometry import RoomGeometryV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.sizing.basic_pipe_size_suggestion_v1 import (
    build_basic_pipe_size_suggestion_v1,
)


def main() -> None:
    print()
    print("Hydronics H-N8 — basic pipe size suggestion probe")
    print()

    project = ProjectState(
        project_id="DEV-HYD-HN8-001",
        name="Hydronics H-N8 Pipe Size Suggestion Probe",
    )

    _add_room(project, "room-001", "Plant Room", "R1")
    _add_room(project, "room-002", "Hall", "R2")
    _add_room(project, "room-003", "Kitchen", "R3")
    _add_room(project, "room-004", "Lounge", "R4")
    _add_room(project, "room-005", "Bedroom 1", "R5")
    _add_room(project, "room-006", "Bathroom", "R6")

    project.heatloss_results = {
        "fabric": {},
        "ventilation": {},
        "room_totals": {
            "room-001": {"q_total_W": 338.7},
            "room-002": {"q_total_W": 338.7},
            "room-003": {"q_total_W": 421.6},
            "room-004": {"q_total_W": 421.6},
            "room-005": {"q_total_W": 421.6},
            "room-006": {"q_total_W": 255.7},
        },
    }
    project.mark_heatloss_valid()

    _add_emitter(project, "room-001", "R1 Plant Room", 500.0)
    _add_emitter(project, "room-002", "R2 Hall", 400.0)
    _add_emitter(project, "room-003", "R3 Kitchen", 500.0)
    _add_emitter(project, "room-004", "R4 Lounge", 500.0)
    _add_emitter(project, "room-005", "R5 Bedroom 1", 500.0)
    _add_emitter(project, "room-006", "R6 Bathroom", 300.0)

    project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1(
        basis_mode="INDEX_LENGTH",
        index_room_id="room-005",
        index_emitter_id="emitter-rad-room-005-001",
        total_index_length_m=30.0,
        allowance_percent=12.0,
        nominal_pressure_gradient_Pa_per_m=50.0,
        length_source="user",
        pressure_gradient_source="user",
        notes="Probe basic pipe size suggestion.",
    )

    suggestion = build_basic_pipe_size_suggestion_v1(project)

    print(f"Basis:            {suggestion.basis}")
    print(
        "Nominal gradient: "
        f"{suggestion.nominal_pressure_gradient_Pa_per_m:.1f} Pa/m"
    )
    print()
    print("Rows:")

    for row in suggestion.rows:
        print(
            f"{row.section_index:>2d} | "
            f"{row.from_room_label:14s} → "
            f"{row.to_room_label:14s} | "
            f"flow={_fmt_kg_s(row.accumulated_mass_flow_kg_s):>13s} | "
            f"size={_fmt_mm(row.suggested_nominal_size_mm):>7s} | "
            f"capacity={_fmt_kg_s(row.capacity_mass_flow_kg_s):>13s} | "
            f"status={row.status}"
        )

    assert suggestion.basis == "BASIC_CAPACITY_TABLE"
    assert suggestion.nominal_pressure_gradient_Pa_per_m == 50.0
    assert len(suggestion.rows) == 4

    expected_sizes = [10.0, 15.0, 15.0, 15.0]

    for row, expected_size in zip(suggestion.rows, expected_sizes):
        assert row.status == "SIZE_OK"
        assert row.suggested_nominal_size_mm == expected_size

    print()
    print("OK — basic pipe size suggestion passed.")
    print()


def _add_room(
    project: ProjectState,
    room_id: str,
    name: str,
    room_ref: str,
) -> None:
    project.rooms[room_id] = RoomStateV1(
        room_id=room_id,
        name=name,
        room_ref=room_ref,
        storey_index=0,
        storey_label="Ground Floor",
        geometry=RoomGeometryV1(
            length_m=4.0,
            width_m=3.0,
            height_m=2.4,
        ),
    )


def _add_emitter(
    project: ProjectState,
    room_id: str,
    room_label: str,
    output_W: float,
) -> None:
    emitter_id = f"emitter-rad-{room_id}-001"

    project.emitters[emitter_id] = EmitterV1(
        emitter_id=emitter_id,
        room_id=room_id,
        name=f"Radiator — {room_label}",
        emitter_type="radiator",
        design_output_W=output_W,
        flow_temp_C=70.0,
        return_temp_C=50.0,
        room_temp_C=None,
        notes="Probe emitter",
    )


def _fmt_kg_s(value: float | None) -> str:
    return "—" if value is None else f"{value:.5f} kg/s"


def _fmt_mm(value: float | None) -> str:
    return "—" if value is None else f"{value:.0f} mm"


if __name__ == "__main__":
    main()