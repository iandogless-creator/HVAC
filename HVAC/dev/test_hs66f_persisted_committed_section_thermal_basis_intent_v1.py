# ======================================================================
# H-S66-F — Persisted committed-section thermal-condition basis intent
# ======================================================================

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    CommittedPipeSectionThermalConditionBasisIntentV1,
    build_committed_pipe_schedule_thermal_fingerprint_v1,
    committed_pipe_section_thermal_condition_basis_intent_from_dict_v1,
    committed_pipe_section_thermal_condition_basis_intent_is_current_v1,
    committed_pipe_section_thermal_condition_basis_intent_to_dict_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.project.project_state import ProjectState


def _basis(*, surface_temperature_C: float = 60.0):
    return build_explicit_bare_pipe_thermal_condition_basis_v1(
        surface_temperature_C=surface_temperature_C,
        ambient_air_temperature_C=20.0,
        mean_radiant_temperature_C=18.0,
        emissivity=0.95,
        external_convection_coefficient_W_m2K=5.0,
    )


def _section(
        *,
        section_id: str,
        order: int,
        material_key: str,
        material_label: str,
        pipe_size_label: str,
        dn: int,
        length_m: float,
) -> CommittedProportioningHydraulicSectionV1:
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="route-exclusive",
        route_ids=("route-a",),
        order=order,
        from_label=f"{section_id}-from",
        to_label=f"{section_id}-to",
        carried_flow_kg_s=0.1,
        pipe_size_label=pipe_size_label,
        dn=dn,
        length_m=length_m,
        k_total=0.0,
        velocity_m_s=0.4,
        reynolds_number=5000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=4,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=100.0,
        straight_pressure_drop_Pa=100.0 * length_m,
        local_pressure_drop_Pa=0.0,
        section_total_pressure_drop_Pa=100.0 * length_m,
        material_key=material_key,
        material_label=material_label,
        internal_diameter_m=0.020,
        material_roughness_m=0.0000015,
    )


def _authority():
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=(
            _section(
                section_id="section-copper-022",
                order=2,
                material_key="copper",
                material_label="Copper EN1057",
                pipe_size_label="22 mm",
                dn=22,
                length_m=5.0,
            ),
            _section(
                section_id="section-steel-dn32",
                order=1,
                material_key="steel",
                material_label="Steel Medium",
                pipe_size_label="DN32",
                dn=32,
                length_m=3.0,
            ),
        ),
        routes=(),
        status="Ready — committed fixture",
        blockers=(),
    )


def main() -> None:
    authority = _authority()
    fingerprint = build_committed_pipe_schedule_thermal_fingerprint_v1(
        authority
    )
    assert len(fingerprint) == 64
    assert fingerprint == build_committed_pipe_schedule_thermal_fingerprint_v1(
        replace(authority, sections=tuple(reversed(authority.sections)))
    )

    changed_section = replace(authority.sections[0], dn=28)
    changed = replace(
        authority,
        sections=(changed_section, authority.sections[1]),
    )
    changed_fingerprint = build_committed_pipe_schedule_thermal_fingerprint_v1(
        changed
    )
    assert changed_fingerprint != fingerprint

    intent = CommittedPipeSectionThermalConditionBasisIntentV1()
    intent.set_section_basis(
        section_id="section-copper-022",
        committed_schedule_fingerprint=fingerprint,
        thermal_basis=_basis(),
    )
    intent.set_section_basis(
        section_id="section-steel-dn32",
        committed_schedule_fingerprint=fingerprint,
        thermal_basis=_basis(surface_temperature_C=55.0),
    )
    assert intent.committed_schedule_fingerprint == fingerprint
    assert tuple(sorted(intent.basis_by_section_id)) == (
        "section-copper-022",
        "section-steel-dn32",
    )
    assert intent.basis_by_section_id[
        "section-steel-dn32"
    ].surface_temperature_C == 55.0
    assert committed_pipe_section_thermal_condition_basis_intent_is_current_v1(
        intent,
        authority,
    ) is True
    assert committed_pipe_section_thermal_condition_basis_intent_is_current_v1(
        intent,
        changed,
    ) is False

    try:
        intent.set_section_basis(
            section_id="section-copper-022",
            committed_schedule_fingerprint=changed_fingerprint,
            thermal_basis=_basis(),
        )
    except ValueError as exc:
        assert "stale" in str(exc).lower()
    else:
        raise AssertionError("Expected explicit stale schedule clearance")

    payload = committed_pipe_section_thermal_condition_basis_intent_to_dict_v1(
        intent
    )
    json.dumps(payload)
    restored = (
        committed_pipe_section_thermal_condition_basis_intent_from_dict_v1(
            payload
        )
    )
    assert restored.to_dict() == payload
    assert restored.basis_by_section_id[
        "section-copper-022"
    ].to_thermal_basis() == _basis()

    project = ProjectState(project_id="project-hs66f", name="H-S66-F")
    project.hydronic_committed_pipe_section_thermal_condition_basis_intent = (
        intent
    )
    project_payload = project.to_dict()
    assert (
        project_payload[
            "hydronic_committed_pipe_section_thermal_condition_basis_intent"
        ]["committed_schedule_fingerprint"]
        == fingerprint
    )
    restored_project = ProjectState.from_dict(project_payload)
    restored_project_intent = (
        restored_project
        .hydronic_committed_pipe_section_thermal_condition_basis_intent
    )
    assert restored_project_intent is not None
    assert restored_project_intent.to_dict() == payload

    assert intent.clear_section_basis("section-copper-022") is True
    assert intent.committed_schedule_fingerprint == fingerprint
    assert intent.clear_section_basis("section-steel-dn32") is True
    assert intent.committed_schedule_fingerprint == ""
    assert intent.basis_by_section_id == {}

    malformed = dict(payload)
    malformed["committed_schedule_fingerprint"] = ""
    assert (
        committed_pipe_section_thermal_condition_basis_intent_from_dict_v1(
            malformed
        ).basis_by_section_id
        == {}
    )

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_section_thermal_condition_basis_intent_v1.py"
    ).read_text(encoding="utf-8")
    assert "HVAC.gui_v3" not in source
    assert "compute_bare_pipe_heat_loss_v1" not in source
    assert "insulation" not in source.lower()
    assert "water_temperature_decay" not in source

    print(
        "OK — H-S66-F persisted committed-section thermal-condition "
        "basis intent passed."
    )


if __name__ == "__main__":
    main()
