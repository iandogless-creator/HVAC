# ======================================================================
# HVAC/dev/test_hs24g_branch_aware_flow_reaches_pressure_and_balancing_v1.py
# H-S24-G — Confirm branch-aware flow reaches pressure and balancing preview
# ======================================================================

from __future__ import annotations

from types import SimpleNamespace

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.proportioning.balancing_point_duty_preview_v1 import (
    build_balancing_point_duty_preview_v1,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    build_preliminary_balancing_resistance_basis_v1,
)
from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.project.project_state import ProjectState


def _add_emitter(project: ProjectState, room_id: str, output_W: float) -> None:
    emitter_id = f"emitter-{room_id}"

    project.emitters[emitter_id] = EmitterV1(
        emitter_id=emitter_id,
        room_id=room_id,
        emitter_type="radiator",
        design_output_W=output_W,
    )


def _expected_flow(output_W: float) -> float:
    return output_W / (4180.0 * 10.0)


def _fmt_flow(value: float) -> str:
    return f"{value:.5f} kg/s"


def _fmt_pa(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f} Pa"


def _fmt_w(value: float) -> str:
    return f"{value:.1f} W"


def _build_project() -> ProjectState:
    project = ProjectState(
        project_id="dev-hs24g-flow-to-pressure-balancing",
        name="DEV H-S24-G Flow To Pressure And Balancing",
    )

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
        design_flow_temp_c=75.0,
        design_return_temp_c=65.0,
    )

    for room_id, output_W in {
        "room-002": 200.0,
        "room-003": 300.0,
        "room-004": 400.0,
        "room-005": 500.0,
        "room-006": 600.0,
        "room-007": 700.0,
        "room-008": 800.0,
    }.items():
        _add_emitter(project, room_id, output_W)

    primary = HydronicSublegV1(
        subleg_id="leg-001-primary-subleg",
        label="Leg 1A Common subleg",
        origin_room_id="room-001",
        route_room_ids=["room-002", "room-003", "room-004"],
        index_room_id="room-004",
    )

    true_branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-b",
        label="Leg 1B Branch subleg",
        origin_room_id="room-003",
        route_room_ids=["room-005", "room-006"],
        index_room_id="room-006",
    )

    terminal_continuation = HydronicSublegV1(
        subleg_id="leg-001-subleg-c",
        label="Leg 1C Terminal continuation",
        origin_room_id="room-004",
        route_room_ids=["room-007"],
        index_room_id="room-007",
    )

    early_branch = HydronicSublegV1(
        subleg_id="leg-001-subleg-d",
        label="Leg 1D Early riser branch",
        origin_room_id="room-002",
        route_room_ids=["room-008"],
        index_room_id="room-008",
    )

    primary.sublegs.append(true_branch)
    primary.sublegs.append(terminal_continuation)
    primary.sublegs.append(early_branch)

    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=["room-002", "room-003", "room-004"],
                index_room_id="room-004",
                sublegs=[primary],
            )
        ],
    )

    return project


def _section_rows_from_projection(projection) -> list[dict]:
    route_id = (
        f"{projection.sections_projection.leg_id}:"
        f"{projection.sections_projection.subleg_id}"
    )
    route_label = (
        f"{projection.sections_projection.leg_label} / "
        f"{projection.sections_projection.subleg_label}"
    )

    pressure_by_section = {
        row.section_id: row
        for row in projection.pressure_preview_projection.rows
    }

    rows: list[dict] = []

    for result in projection.pipe_sizing_projection.results:
        pressure = pressure_by_section[result.section_id]

        rows.append(
            {
                "section_id": result.section_id,
                "order": str(result.order),
                "from": result.from_label,
                "to": result.to_room_label,
                "route_id": route_id,
                "route": route_label,
                "leg_id": projection.sections_projection.leg_id,
                "subleg_id": projection.sections_projection.subleg_id,
                "q_carried": _fmt_w(result.carried_heat_W),
                "flow_kg_s": _fmt_flow(result.carried_flow_kg_s),
                "pipe": result.pipe_size_label,
                "velocity_m_s": f"{result.velocity_m_s:.3f}",
                "dp_per_m": _fmt_pa(result.pressure_gradient_Pa_per_m),
                "length_m": (
                    f"{pressure.section_length_m:.2f}"
                    if pressure.section_length_m is not None
                    else "—"
                ),
                "k_total": "0.00",
                "local_dp": "0.0 Pa",
                "straight_dp": _fmt_pa(pressure.section_pressure_drop_Pa),
                "section_dp": _fmt_pa(pressure.section_pressure_drop_Pa),
                "status": result.status,
            }
        )

    return rows


def main() -> None:
    project = _build_project()

    # Keep lengths simple and complete so pressure preview and route ranking
    # are complete.
    lengths = {
        "leg-001-primary-subleg-section-001": 1.0,
        "leg-001-primary-subleg-section-002": 1.0,
        "leg-001-primary-subleg-section-003": 1.0,
    }

    projection = build_basic_ps_readonly_projection_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
        section_lengths_m=lengths,
    )

    first_section = projection.sections_projection.sections[0]
    first_sizing = projection.pipe_sizing_projection.results[0]
    first_pressure = projection.pressure_preview_projection.rows[0]

    expected_first_flow = _expected_flow(3500.0)

    print()
    print("H-S24-G — Branch-aware flow reaches pressure and balancing")
    print("=========================================================")
    print("Basic PS first section Q:", first_section.carried_heat_W)
    print("Basic PS first section flow:", f"{first_section.carried_flow_kg_s:.6f}")
    print("Pipe sizing first section flow:", f"{first_sizing.carried_flow_kg_s:.6f}")
    print("Pipe sizing first section pipe:", first_sizing.pipe_size_label)
    print("Pressure gradient:", f"{first_sizing.pressure_gradient_Pa_per_m:.3f}")
    print("Section Δp:", first_pressure.section_pressure_drop_Pa)

    assert first_section.carried_heat_W == 3500.0
    assert abs(first_section.carried_flow_kg_s - expected_first_flow) < 1e-9

    # Pipe sizing must consume the same corrected branch-aware flow.
    assert first_sizing.carried_heat_W == 3500.0
    assert abs(first_sizing.carried_flow_kg_s - expected_first_flow) < 1e-9
    assert first_sizing.pressure_gradient_Pa_per_m > 0.0

    # Pressure preview must consume the pipe-sizing pressure-gradient basis.
    assert first_pressure.pressure_gradient_Pa_per_m == (
        first_sizing.pressure_gradient_Pa_per_m
    )
    assert first_pressure.section_pressure_drop_Pa == (
        first_sizing.pressure_gradient_Pa_per_m * 1.0
    )

    section_rows = _section_rows_from_projection(projection)

    route_id = "leg-001:leg-001-primary-subleg"
    route_label = "Heating Leg 1 / Leg 1A Common subleg"

    route_dp = projection.pressure_preview_projection.total_pressure_drop_Pa
    assert route_dp is not None

    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=section_rows,
        route_rows=[
            {
                "route_id": route_id,
                "route": route_label,
                "sections": str(len(section_rows)),
                "route_dp_sum": _fmt_pa(route_dp),
                "complete": "Yes",
                "controlling": "No",
                "status": "Preview only",
            }
        ],
        shortfall_rows=[],
        return_comparison_rows=[
            {
                "route": route_label,
                "status": "Dummy return comparison for H-S24-G test",
            }
        ],
    )

    print("Snapshot first section flow:", snapshot.sections[0].flow_kg_s)

    assert snapshot.sections[0].flow_kg_s == _fmt_flow(expected_first_flow)

    # Build a minimal route balancing preview object. The resistance builder
    # is duck-typed and reads the same attributes as the real preview DTOs.
    balancing_preview = SimpleNamespace(
        ready=True,
        blockers=[],
        rows=[
            SimpleNamespace(
                route_id=route_id,
                route_label=route_label,
                sections=str(len(section_rows)),
                route_dp=_fmt_pa(route_dp),
                controlling_route_dp=_fmt_pa(route_dp + 100.0),
                required_added_resistance_dp="100.0 Pa",
                controlling="No",
                status="Test balancing preview",
            )
        ],
    )

    resistance_basis = build_preliminary_balancing_resistance_basis_v1(
        snapshot=snapshot,
        balancing_preview=balancing_preview,
    )

    assert resistance_basis.ready is True
    assert len(resistance_basis.rows) == 1

    resistance_row = resistance_basis.rows[0]

    print("Resistance basis flow:", resistance_row.flow_kg_s)
    print("Resistance basis R:", resistance_row.resistance_pa_per_kg_s2)

    assert resistance_row.flow_kg_s == _fmt_flow(expected_first_flow)
    assert resistance_row.required_added_dp == "100.0 Pa"
    assert resistance_row.status == "Preliminary resistance basis calculated"

    duty = build_balancing_point_duty_preview_v1(
        route_balancing_preview=balancing_preview,
        resistance_basis=resistance_basis,
    )

    assert duty.ready is True
    assert len(duty.rows) == 1

    duty_row = duty.rows[0]

    print("Duty preview flow:", duty_row.flow_kg_s)
    print("Duty preview status:", duty_row.status)

    assert duty_row.flow_kg_s == _fmt_flow(expected_first_flow)
    assert duty_row.required_added_dp == "100.0 Pa"
    assert duty_row.status == "Balancing point duty preview calculated"

    print()
    print("OK — branch-aware flow reaches pressure and balancing preview.")


if __name__ == "__main__":
    main()
