# ======================================================================
# HVAC/hydronics/probes/probe_basic_hydronics_worksheet_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.room_state import RoomStateV1
from HVAC.core.room_geometry import RoomGeometryV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.worksheets.basic_hydronics_worksheet_v1 import (
    build_basic_hydronics_worksheet_v1,
)


def main() -> None:
    print()
    print("Hydronics H-N5 — basic hydronics worksheet probe")
    print()

    project = ProjectState(
        project_id="DEV-HYD-HN5-001",
        name="Hydronics H-N5 Worksheet Probe",
    )

    project.rooms["room-001"] = RoomStateV1(
        room_id="room-001",
        name="Plant Room",
        room_ref="R1",
        storey_index=-1,
        storey_label="Basement",
        geometry=RoomGeometryV1(length_m=3.0, width_m=3.0, height_m=2.4),
    )

    project.rooms["room-002"] = RoomStateV1(
        room_id="room-002",
        name="Kitchen",
        room_ref="R2",
        storey_index=0,
        storey_label="Ground Floor",
        geometry=RoomGeometryV1(length_m=4.0, width_m=3.0, height_m=2.4),
    )

    project.heatloss_results = {
        "fabric": {},
        "ventilation": {},
        "room_totals": {
            "room-001": {
                "q_fabric_W": 200.0,
                "q_ventilation_W": 100.0,
                "q_total_W": 300.0,
            },
            "room-002": {
                "q_fabric_W": 300.0,
                "q_ventilation_W": 121.6,
                "q_total_W": 421.6,
            },
        },
    }
    project.mark_heatloss_valid()

    project.emitters["emitter-rad-room-002-001"] = EmitterV1(
        emitter_id="emitter-rad-room-002-001",
        room_id="room-002",
        name="Radiator — R2 Kitchen",
        emitter_type="radiator",
        design_output_W=500.0,
        flow_temp_C=70.0,
        return_temp_C=50.0,
        room_temp_C=None,
        notes="Probe emitter",
    )

    project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1(
        basis_mode="INDEX_LENGTH",
        index_room_id="room-002",
        index_emitter_id="emitter-rad-room-002-001",
        total_index_length_m=30.0,
        nominal_pressure_gradient_Pa_per_m=50.0,
        length_source="user",
        pressure_gradient_source="user",
        notes="Probe index basis.",
    )

    worksheet = build_basic_hydronics_worksheet_v1(project)

    print("Rows:")
    for row in worksheet.rows:
        print(
            f"{row.room_label:18s} | "
            f"load={_fmt_w(row.heat_load_W):>8s} | "
            f"emitter={row.emitter_summary:10s} | "
            f"output={_fmt_w(row.emitter_output_W):>8s} | "
            f"status={row.emitter_status:22s} | "
            f"FT={_fmt_c(row.flow_temp_C):>7s} | "
            f"RT={_fmt_c(row.return_temp_C):>7s} | "
            f"dT={_fmt_k(row.water_delta_t_K):>7s} | "
            f"flow={_fmt_kg_s(row.mass_flow_kg_s):>12s}"
        )

    summary = worksheet.index_summary

    print()
    print("Basic index:")
    print(f"Basis mode:       {summary.basis_mode}")
    print(f"Index room:       {summary.index_room_label}")
    print(f"Index emitter:    {summary.index_emitter_label}")
    print(f"Index length:     {_fmt_m(summary.total_index_length_m)}")
    print(f"Nominal gradient: {_fmt_pa_m(summary.nominal_pressure_gradient_Pa_per_m)}")
    print(f"Allowance:        {_fmt_pa(summary.nominal_index_pipework_dp_Pa)}")
    print(f"Length source:    {summary.length_source}")
    print(f"Gradient source:  {summary.pressure_gradient_source}")

    kitchen_row = next(row for row in worksheet.rows if row.room_id == "room-002")

    assert kitchen_row.room_label == "R2 Kitchen"
    assert kitchen_row.heat_load_W == 421.6
    assert kitchen_row.emitter_count == 1
    assert kitchen_row.emitter_summary == "radiator"
    assert kitchen_row.emitter_output_W == 500.0
    assert kitchen_row.emitter_status == "EMITTER_OK"
    assert kitchen_row.flow_temp_C == 70.0
    assert kitchen_row.return_temp_C == 50.0
    assert kitchen_row.water_delta_t_K == 20.0

    expected_flow = 421.6 / (4180.0 * 20.0)
    assert abs(kitchen_row.mass_flow_kg_s - expected_flow) < 1e-12

    assert summary.index_room_label == "R2 Kitchen"
    assert summary.total_index_length_m == 30.0
    assert summary.nominal_pressure_gradient_Pa_per_m == 50.0
    assert summary.nominal_index_pipework_dp_Pa == 1500.0

    print()
    print("OK — basic hydronics worksheet passed.")
    print()


def _fmt_w(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} W"


def _fmt_c(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} °C"


def _fmt_k(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} K"


def _fmt_kg_s(value: float | None) -> str:
    return "—" if value is None else f"{value:.5f} kg/s"


def _fmt_m(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} m"


def _fmt_pa_m(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} Pa/m"


def _fmt_pa(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} Pa"


if __name__ == "__main__":
    main()