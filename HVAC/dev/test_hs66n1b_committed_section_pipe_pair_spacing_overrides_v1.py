from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.heatloss.physics.committed_pipe_pair_spacing_override_intent_v1 import (
    CommittedPipePairSpacingOverrideIntentV1,
    build_committed_pipe_pair_spacing_fingerprint_v1,
    committed_pipe_pair_spacing_override_intent_from_dict_v1,
    resolve_effective_committed_pipe_pair_spacing_v1,
    set_current_committed_section_pipe_pair_spacing_override_v1,
)
from HVAC.heatloss.physics.environment_pipe_pair_spacing_defaults_v1 import (
    DOUBLE_MUNSEN_RING_V1,
    MOULDED_PLASTIC_DOUBLE_CLIP_V1,
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
    default_environment_pipe_pair_spacing_defaults_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.project.project_state import ProjectState


def _section(section_id: str, *, dn: int, length_m: float = 3.0):
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="subleg",
        route_ids=("route-1",),
        order=1,
        from_label="A",
        to_label="B",
        carried_flow_kg_s=0.1,
        pipe_size_label=f"{dn} mm",
        dn=dn,
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


def _authority(*sections):
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=tuple(sections),
        status="Ready",
    )


def main() -> None:
    stacked = _section("section-stacked", dn=22)
    separate = replace(
        _section("section-separate", dn=15),
        order=2,
    )
    authority = _authority(stacked, separate)
    arrangements = {
        stacked.section_id: STACKED_FLOW_RETURN_PAIR_V1,
        separate.section_id: SEPARATE_PIPE_V1,
    }
    defaults = default_environment_pipe_pair_spacing_defaults_v1()

    inherited = resolve_effective_committed_pipe_pair_spacing_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        raw_environment_defaults=defaults,
        local_intent=None,
        section_id=stacked.section_id,
    )
    assert inherited is not None
    assert inherited.support_type == MOULDED_PLASTIC_DOUBLE_CLIP_V1
    assert inherited.centre_spacing_mm == 40.0
    assert inherited.actual_outside_diameter_mm == 22.0
    assert inherited.nominal_default_outside_diameter_mm == 22
    assert inherited.locally_overridden is False

    intent = CommittedPipePairSpacingOverrideIntentV1()
    set_current_committed_section_pipe_pair_spacing_override_v1(
        intent=intent,
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        section_id=stacked.section_id,
        support_type=DOUBLE_MUNSEN_RING_V1,
        centre_spacing_mm=47.0,
    )
    effective = resolve_effective_committed_pipe_pair_spacing_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        raw_environment_defaults=defaults,
        local_intent=intent,
        section_id=stacked.section_id,
    )
    assert effective is not None
    assert effective.support_type == DOUBLE_MUNSEN_RING_V1
    assert effective.centre_spacing_mm == 47.0
    assert effective.locally_overridden is True
    assert "exact committed-section" in effective.source

    # Separate RR ignores all stacked-pair defaults and cannot receive an override.
    assert resolve_effective_committed_pipe_pair_spacing_v1(
        committed_authority=authority,
        external_arrangement_by_section_id=arrangements,
        raw_environment_defaults=defaults,
        local_intent=intent,
        section_id=separate.section_id,
    ) is None
    try:
        set_current_committed_section_pipe_pair_spacing_override_v1(
            intent=intent,
            committed_authority=authority,
            external_arrangement_by_section_id=arrangements,
            section_id=separate.section_id,
            support_type=DOUBLE_MUNSEN_RING_V1,
            centre_spacing_mm=35.0,
        )
    except ValueError as exc:
        assert "only to a stacked" in str(exc)
    else:
        raise AssertionError("Separate RR accepted a stacked-pair override")

    # Exact catalogue OD remains the overlap guard.
    try:
        set_current_committed_section_pipe_pair_spacing_override_v1(
            intent=intent,
            committed_authority=authority,
            external_arrangement_by_section_id=arrangements,
            section_id=stacked.section_id,
            support_type=DOUBLE_MUNSEN_RING_V1,
            centre_spacing_mm=22.0,
        )
    except ValueError as exc:
        assert "exact catalogue pipe OD" in str(exc)
    else:
        raise AssertionError("Overlapping local stacked pipes were accepted")

    round_trip = committed_pipe_pair_spacing_override_intent_from_dict_v1(
        intent.to_dict()
    )
    assert round_trip == intent
    project = ProjectState(project_id="project-1", name="Project")
    project.hydronic_committed_pipe_pair_spacing_override_intent = intent
    restored = ProjectState.from_dict(project.to_dict())
    assert restored.hydronic_committed_pipe_pair_spacing_override_intent == intent

    # A changed committed schedule must not silently inherit the old override.
    stale_authority = _authority(replace(stacked, length_m=4.0), separate)
    assert build_committed_pipe_pair_spacing_fingerprint_v1(
        stale_authority
    ) != intent.committed_schedule_fingerprint
    try:
        resolve_effective_committed_pipe_pair_spacing_v1(
            committed_authority=stale_authority,
            external_arrangement_by_section_id=arrangements,
            raw_environment_defaults=defaults,
            local_intent=intent,
            section_id=stacked.section_id,
        )
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("Stale local spacing override remained effective")

    assert intent.clear_section_override(stacked.section_id) is True
    assert intent.committed_schedule_fingerprint == ""
    assert not intent.override_by_section_id

    root = Path(__file__).resolve().parents[2]
    source = (
        root / "HVAC/heatloss/physics/committed_pipe_pair_spacing_override_intent_v1.py"
    ).read_text(encoding="utf-8")
    assert "external_convection" not in source
    assert "heat_loss" not in source

    print(
        "OK — H-S66-N1B persisted exact committed-section stacked-pair "
        "support and c/c overrides passed."
    )


if __name__ == "__main__":
    main()
