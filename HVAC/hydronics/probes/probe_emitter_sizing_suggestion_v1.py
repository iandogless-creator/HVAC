# ======================================================================
# HVAC/hydronics/probes/probe_emitter_sizing_suggestion_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.core.room_geometry import RoomGeometryV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.sizing.emitter_sizing_suggestion_v1 import (
    build_emitter_sizing_suggestion_v1,
)


def main() -> None:
    print()
    print("Hydronics H-N6 — emitter sizing suggestion probe")
    print()

    project = ProjectState(
        project_id="DEV-HYD-HN6-001",
        name="Hydronics H-N6 Emitter Sizing Probe",
    )

    project.rooms["room-001"] = RoomStateV1(
        room_id="room-001",
        name="Kitchen",
        room_ref="R1",
        storey_index=0,
        storey_label="Ground Floor",
        geometry=RoomGeometryV1(
            length_m=4.0,
            width_m=3.0,
            height_m=2.4,
        ),
    )

    project.rooms["room-002"] = RoomStateV1(
        room_id="room-002",
        name="Bedroom 1",
        room_ref="R2",
        storey_index=1,
        storey_label="First Floor",
        geometry=RoomGeometryV1(
            length_m=4.0,
            width_m=3.0,
            height_m=2.4,
        ),
    )

    project.rooms["room-003"] = RoomStateV1(
        room_id="room-003",
        name="Bathroom",
        room_ref="R3",
        storey_index=1,
        storey_label="First Floor",
        geometry=RoomGeometryV1(
            length_m=2.0,
            width_m=3.0,
            height_m=2.4,
        ),
    )

    project.heatloss_results = {
        "fabric": {},
        "ventilation": {},
        "room_totals": {
            "room-001": {
                "q_fabric_W": 300.0,
                "q_ventilation_W": 121.6,
                "q_total_W": 421.6,
            },
            "room-002": {
                "q_fabric_W": 500.0,
                "q_ventilation_W": 100.0,
                "q_total_W": 600.0,
            },
            "room-003": {
                "q_fabric_W": 200.0,
                "q_ventilation_W": 55.7,
                "q_total_W": 255.7,
            },
        },
    }
    project.mark_heatloss_valid()

    # Kitchen: existing 500 W should satisfy 421.6 W × 1.12 = 472.192 W.
    project.emitters["emitter-rad-room-001-001"] = EmitterV1(
        emitter_id="emitter-rad-room-001-001",
        room_id="room-001",
        name="Radiator — R1 Kitchen",
        emitter_type="radiator",
        design_output_W=500.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
        room_temp_C=None,
        notes="Probe emitter",
    )

    # Bedroom: existing 500 W should be below 600 W × 1.12 = 672 W.
    project.emitters["emitter-rad-room-002-001"] = EmitterV1(
        emitter_id="emitter-rad-room-002-001",
        room_id="room-002",
        name="Radiator — R2 Bedroom 1",
        emitter_type="radiator",
        design_output_W=500.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
        room_temp_C=None,
        notes="Probe emitter",
    )

    # Bathroom: no emitter, should need selection.
    suggestion = build_emitter_sizing_suggestion_v1(
        project,
        allowance_percent=12.0,
        rounding_step_W=50.0,
    )

    print(f"Allowance: {suggestion.allowance_percent:.1f}%")
    print()
    print("Rows:")

    for row in suggestion.rows:
        print(
            f"{row.room_label:14s} | "
            f"Qt={_fmt_w(row.heat_load_W):>8s} | "
            f"allow={row.allowance_percent:>5.1f}% | "
            f"required={_fmt_w(row.required_output_W):>8s} | "
            f"rounded={_fmt_w(row.suggested_rounded_output_W):>8s} | "
            f"existing={_fmt_w(row.existing_emitter_output_W):>8s} | "
            f"status={row.status}"
        )

    kitchen = next(row for row in suggestion.rows if row.room_id == "room-001")
    bedroom = next(row for row in suggestion.rows if row.room_id == "room-002")
    bathroom = next(row for row in suggestion.rows if row.room_id == "room-003")

    assert kitchen.room_label == "R1 Kitchen"
    assert kitchen.heat_load_W == 421.6
    assert kitchen.allowance_percent == 12.0
    assert abs(kitchen.required_output_W - 472.192) < 1e-9
    assert kitchen.suggested_rounded_output_W == 500.0
    assert kitchen.existing_emitter_output_W == 500.0
    assert kitchen.status == "EMITTER_OK"

    assert bedroom.heat_load_W == 600.0
    assert abs(bedroom.required_output_W - 672.0) < 1e-9
    assert abs(bedroom.suggested_rounded_output_W - 700.0) < 1e-9
    assert bedroom.existing_emitter_output_W == 500.0
    assert bedroom.status == "EMITTER_BELOW_SUGGESTION"

    assert bathroom.heat_load_W == 255.7
    assert abs(bathroom.required_output_W - 286.384) < 1e-9
    assert bathroom.suggested_rounded_output_W == 300.0
    assert bathroom.existing_emitter_output_W is None
    assert bathroom.status == "NEEDS_EMITTER_SELECTION"

    print()
    print("OK — emitter sizing suggestion passed.")
    print()


def _fmt_w(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} W"


if __name__ == "__main__":
    main()