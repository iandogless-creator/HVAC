from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    FLOW_PIPE_V1,
    NOT_SET_UPPER_PIPE_ROLE_V1,
    RETURN_PIPE_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.heatloss.physics.committed_pipe_pair_vertical_order_intent_v1 import (
    CommittedPipePairVerticalOrderIntentV1,
    build_committed_pipe_pair_vertical_order_fingerprint_v1,
    committed_pipe_pair_vertical_order_intent_from_dict_v1,
    resolve_effective_committed_pipe_pair_vertical_order_v1,
    set_current_committed_section_pipe_pair_vertical_order_override_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.project.project_state import ProjectState


def _section(section_id: str, order: int, length_m: float = 3.0):
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="subleg",
        route_ids=("route",),
        order=order,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.1,
        pipe_size_label="22 mm",
        dn=22,
        length_m=length_m,
        k_total=0.0,
        velocity_m_s=0.3,
        reynolds_number=10000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=4,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=100.0,
        straight_pressure_drop_Pa=300.0,
        local_pressure_drop_Pa=0.0,
        section_total_pressure_drop_Pa=300.0,
        material_key="copper",
        material_label="Copper EN1057",
        internal_diameter_m=0.0202,
        material_roughness_m=0.0000015,
    )


def _authority(stacked, separate):
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(stacked, separate),
        status="Ready — fixture",
    )


def main() -> None:
    stacked = _section("stacked", 1)
    separate = _section("separate", 2)
    authority = _authority(stacked, separate)
    arrangements = {
        "stacked": STACKED_FLOW_RETURN_PAIR_V1,
        "separate": SEPARATE_PIPE_V1,
    }

    intent = CommittedPipePairVerticalOrderIntentV1()
    unresolved = resolve_effective_committed_pipe_pair_vertical_order_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        intent=intent,
        section_id="stacked",
    )
    assert unresolved is not None
    assert unresolved.resolved is False
    assert unresolved.effective_upper_pipe_role == NOT_SET_UPPER_PIPE_ROLE_V1

    intent.set_project_upper_pipe_role(FLOW_PIPE_V1)
    inherited = resolve_effective_committed_pipe_pair_vertical_order_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        intent=intent,
        section_id="stacked",
    )
    assert inherited is not None
    assert inherited.resolved is True
    assert inherited.effective_upper_pipe_role == FLOW_PIPE_V1
    assert inherited.locally_overridden is False

    set_current_committed_section_pipe_pair_vertical_order_override_v1(
        intent=intent,
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        section_id="stacked",
        upper_pipe_role=RETURN_PIPE_V1,
    )
    effective = resolve_effective_committed_pipe_pair_vertical_order_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        intent=intent,
        section_id="stacked",
    )
    assert effective is not None
    assert effective.effective_upper_pipe_role == RETURN_PIPE_V1
    assert effective.locally_overridden is True
    assert "exact committed-section" in effective.source

    assert resolve_effective_committed_pipe_pair_vertical_order_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        intent=intent,
        section_id="separate",
    ) is None
    try:
        set_current_committed_section_pipe_pair_vertical_order_override_v1(
            intent=intent,
            committed_authority=authority,
            external_arrangement_by_section_id=arrangements,
            section_id="separate",
            upper_pipe_role=FLOW_PIPE_V1,
        )
    except ValueError as exc:
        assert "only to a stacked" in str(exc)
    else:
        raise AssertionError("Separate RR accepted vertical-order override")

    round_trip = committed_pipe_pair_vertical_order_intent_from_dict_v1(
        intent.to_dict()
    )
    assert round_trip == intent
    project = ProjectState(project_id="project-1", name="Project")
    project.hydronic_committed_pipe_pair_vertical_order_intent = intent
    restored = ProjectState.from_dict(project.to_dict())
    assert restored.hydronic_committed_pipe_pair_vertical_order_intent == intent

    stale_authority = _authority(
        replace(stacked, length_m=4.0),
        separate,
    )
    assert build_committed_pipe_pair_vertical_order_fingerprint_v1(
        stale_authority
    ) != intent.committed_schedule_fingerprint
    try:
        resolve_effective_committed_pipe_pair_vertical_order_v1(
            committed_authority=stale_authority,
            external_arrangement_by_section_id=arrangements,
            intent=intent,
            section_id="stacked",
        )
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("Stale vertical-order override remained effective")

    assert intent.clear_section_override("stacked") is True
    assert intent.committed_schedule_fingerprint == ""
    assert intent.project_upper_pipe_role == FLOW_PIPE_V1
    after_clear = resolve_effective_committed_pipe_pair_vertical_order_v1(
        committed_authority=stale_authority,
        external_arrangement_by_section_id=arrangements,
        intent=intent,
        section_id="stacked",
    )
    assert after_clear is not None
    assert after_clear.effective_upper_pipe_role == FLOW_PIPE_V1
    assert after_clear.locally_overridden is False

    invalid = committed_pipe_pair_vertical_order_intent_from_dict_v1(
        {"schema": "wrong", "project_upper_pipe_role": "flow"}
    )
    assert invalid.project_upper_pipe_role == NOT_SET_UPPER_PIPE_ROLE_V1
    assert not invalid.override_by_section_id

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_pair_vertical_order_intent_v1.py"
    ).read_text(encoding="utf-8")
    assert "HVAC.gui_v3" not in source
    assert "churchill" not in source.lower()
    assert "nusselt" not in source.lower()
    assert "heat_loss" not in source

    print(
        "OK — H-S66-N2B1 persisted project-wide pipe-pair vertical-order "
        "intent and sparse committed-section overrides passed."
    )


if __name__ == "__main__":
    main()
