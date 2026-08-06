# ======================================================================
# H-S66-N2B — Committed flow/return pairing, order and temperature evidence
# ======================================================================

from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    DORMANT_POSITION_V1,
    FLOW_PIPE_V1,
    LOWER_POSITION_V1,
    NOT_SET_UPPER_PIPE_ROLE_V1,
    RETURN_PIPE_V1,
    UPPER_POSITION_V1,
    build_committed_flow_return_pairing_temperature_evidence_v1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    CommittedPipeExternalArrangementAuthorityV1,
    CommittedPipeExternalArrangementRowV1,
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)


def _section(
        section_id: str,
        order: int,
        material_key: str,
        dn: int,
) -> CommittedProportioningHydraulicSectionV1:
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="route-exclusive",
        route_ids=("route",),
        order=order,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.1,
        pipe_size_label=f"{dn} mm",
        dn=dn,
        length_m=3.0,
        k_total=0.0,
        velocity_m_s=0.4,
        reynolds_number=5000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=4,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=100.0,
        straight_pressure_drop_Pa=300.0,
        local_pressure_drop_Pa=0.0,
        section_total_pressure_drop_Pa=300.0,
        material_key=material_key,
        material_label=material_key,
        internal_diameter_m=0.02,
        material_roughness_m=0.0000015,
    )


def _arrangement_row(
        section_id: str,
        order: int,
        arrangement: str,
) -> CommittedPipeExternalArrangementRowV1:
    return CommittedPipeExternalArrangementRowV1(
        section_id=section_id,
        section_scope="route-exclusive",
        route_ids=("route",),
        route_bases=("F&R",),
        rr_added_length_basis_modes=(),
        order=order,
        external_arrangement=arrangement,
        external_arrangement_label=arrangement,
        source="fixture",
        ready=True,
        status="Ready — fixture",
    )


def _authorities():
    committed = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(
            _section("copper-stacked", 1, "copper", 22),
            _section("steel-stacked", 2, "steel", 32),
            _section("mlcp-separate", 3, "mlcp", 26),
        ),
        routes=(),
        status="Ready — fixture",
    )
    arrangement = CommittedPipeExternalArrangementAuthorityV1(
        ready=True,
        sections=(
            _arrangement_row(
                "copper-stacked", 1, STACKED_FLOW_RETURN_PAIR_V1
            ),
            _arrangement_row(
                "steel-stacked", 2, STACKED_FLOW_RETURN_PAIR_V1
            ),
            _arrangement_row("mlcp-separate", 3, SEPARATE_PIPE_V1),
        ),
        section_count=3,
        status="Ready — fixture",
    )
    return committed, arrangement


def _build(**overrides):
    committed, arrangement = _authorities()
    inputs = {
        "committed_authority": committed,
        "external_arrangement_authority": arrangement,
        "design_flow_temperature_C": 75.0,
        "design_return_temperature_C": 65.0,
        "project_upper_pipe_role": "flow",
        "upper_pipe_role_override_by_section_id": {
            "steel-stacked": "return",
        },
    }
    inputs.update(overrides)
    return build_committed_flow_return_pairing_temperature_evidence_v1(
        **inputs
    )


def main() -> None:
    committed, arrangement = _authorities()
    committed_before = repr(committed)
    arrangement_before = repr(arrangement)
    result = _build(
        committed_authority=committed,
        external_arrangement_authority=arrangement,
    )
    repeated = _build(
        committed_authority=committed,
        external_arrangement_authority=arrangement,
    )

    assert result == repeated
    assert repr(committed) == committed_before
    assert repr(arrangement) == arrangement_before
    assert result.ready is True, result.status
    assert result.section_count == 3
    assert result.stacked_section_count == 2
    assert result.separate_section_count == 1
    assert result.blockers == ()
    assert [row.section_id for row in result.sections] == [
        "copper-stacked",
        "steel-stacked",
        "mlcp-separate",
    ]

    by_id = {row.section_id: row for row in result.sections}
    copper = by_id["copper-stacked"]
    assert copper.paired is True
    assert copper.upper_pipe_role == FLOW_PIPE_V1
    assert copper.lower_pipe_role == RETURN_PIPE_V1
    assert copper.flow_pipe_vertical_position == UPPER_POSITION_V1
    assert copper.return_pipe_vertical_position == LOWER_POSITION_V1
    assert copper.vertical_order_source == (
        "Project-wide explicit upper-pipe role"
    )
    assert copper.flow_pipe_surface_temperature_C == 75.0
    assert copper.return_pipe_surface_temperature_C == 65.0
    assert math.isclose(copper.actual_outside_diameter_mm, 22.0)

    steel = by_id["steel-stacked"]
    assert steel.upper_pipe_role == RETURN_PIPE_V1
    assert steel.lower_pipe_role == FLOW_PIPE_V1
    assert steel.flow_pipe_vertical_position == LOWER_POSITION_V1
    assert steel.return_pipe_vertical_position == UPPER_POSITION_V1
    assert steel.vertical_order_source == (
        "Exact committed-section upper-pipe role override"
    )
    assert steel.catalogue_size_key == 32
    assert math.isclose(steel.actual_outside_diameter_mm, 42.4)

    separate = by_id["mlcp-separate"]
    assert separate.paired is False
    assert separate.upper_pipe_role is None
    assert separate.lower_pipe_role is None
    assert separate.flow_pipe_vertical_position == DORMANT_POSITION_V1
    assert separate.return_pipe_vertical_position == DORMANT_POSITION_V1
    assert "separate" in separate.status.lower()

    not_set = _build(
        project_upper_pipe_role=NOT_SET_UPPER_PIPE_ROLE_V1,
        upper_pipe_role_override_by_section_id={},
    )
    assert not_set.ready is False
    assert "project upper-pipe role is not set" in not_set.status

    all_local = _build(
        project_upper_pipe_role=NOT_SET_UPPER_PIPE_ROLE_V1,
        upper_pipe_role_override_by_section_id={
            "copper-stacked": "return",
            "steel-stacked": "flow",
        },
    )
    assert all_local.ready is True, all_local.status
    assert all(
        "override" in row.vertical_order_source.lower()
        for row in all_local.sections
        if row.paired
    )

    separate_order = _build(
        upper_pipe_role_override_by_section_id={
            "steel-stacked": "return",
            "mlcp-separate": "flow",
        }
    )
    assert separate_order.ready is False
    assert "dormant for separate pipework" in separate_order.status

    invalid_order = _build(
        upper_pipe_role_override_by_section_id={
            "copper-stacked": "side-by-side",
        }
    )
    assert invalid_order.ready is False
    assert "must be flow or return" in invalid_order.status

    blank_identity = _build(
        upper_pipe_role_override_by_section_id={
            "steel-stacked": "return",
            "": "flow",
        }
    )
    assert blank_identity.ready is False
    assert "requires section_id" in blank_identity.status

    invalid_project = _build(project_upper_pipe_role="guess")
    assert invalid_project.ready is False
    assert "must be not_set, flow or return" in invalid_project.status

    mismatched = replace(
        arrangement,
        sections=arrangement.sections[:-1],
        section_count=2,
    )
    missing_arrangement = _build(
        external_arrangement_authority=mismatched
    )
    assert missing_arrangement.ready is False
    assert "mlcp-separate: committed external arrangement is required" in (
        missing_arrangement.blockers
    )

    stale_order = _build(
        external_arrangement_authority=replace(
            arrangement,
            sections=(
                replace(arrangement.sections[0], order=99),
                *arrangement.sections[1:],
            ),
        )
    )
    assert stale_order.ready is False
    assert "external-arrangement order is stale" in stale_order.status

    invalid_temperature = _build(design_flow_temperature_C=60.0)
    assert invalid_temperature.ready is False
    assert "flow temperature must exceed return" in invalid_temperature.status

    unavailable = _build(committed_authority=replace(committed, ready=False))
    assert unavailable.ready is False
    assert unavailable.sections == ()
    assert "hydraulic-input authority is not ready" in unavailable.status

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_flow_return_pairing_temperature_evidence_v1.py"
    ).read_text(encoding="utf-8")
    assert "HVAC.gui_v3" not in source
    assert "from HVAC.project" not in source
    assert "project_state" not in source.lower()
    assert "churchill" not in source.lower()
    assert "nusselt" not in source.lower()
    assert "h_conv" not in source
    assert "centre_spacing" not in source

    print(
        "OK — H-S66-N2B committed flow/return pairing, vertical order "
        "and individual pipe-temperature evidence passed."
    )


if __name__ == "__main__":
    main()
