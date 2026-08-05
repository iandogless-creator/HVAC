# ======================================================================
# H-S66-G — Runtime handoff into H-S66-E
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_bare_heat_loss_evidence_v1 import (
    build_committed_pipe_section_bare_heat_loss_evidence_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_bare_heat_loss_runtime_handoff_v1 import (
    build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    CommittedPipeSectionThermalConditionBasisIntentV1,
    build_committed_pipe_schedule_thermal_fingerprint_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)


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


def _intent(authority, *, include_steel: bool = True):
    fingerprint = build_committed_pipe_schedule_thermal_fingerprint_v1(
        authority
    )
    intent = CommittedPipeSectionThermalConditionBasisIntentV1()
    intent.set_section_basis(
        section_id="section-copper-022",
        committed_schedule_fingerprint=fingerprint,
        thermal_basis=_basis(),
    )
    if include_steel:
        intent.set_section_basis(
            section_id="section-steel-dn32",
            committed_schedule_fingerprint=fingerprint,
            thermal_basis=_basis(surface_temperature_C=55.0),
        )
    return intent


def main() -> None:
    authority = _authority()
    intent = _intent(authority)
    before_authority = repr(authority)
    before_intent = repr(intent)

    result = build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
        committed_authority=authority,
        thermal_basis_intent=intent,
    )
    repeated = build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
        committed_authority=authority,
        thermal_basis_intent=intent,
    )
    assert result == repeated
    assert repr(authority) == before_authority
    assert repr(intent) == before_intent
    assert result.ready is True
    assert result.evidence is not None
    assert result.section_count == 2
    assert result.blockers == ()
    assert result.current_schedule_fingerprint == (
        result.persisted_schedule_fingerprint
    )
    assert result.status == (
        "Ready — fresh persisted section thermal bases handed to H-S66-E"
    )

    direct = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=authority,
        thermal_basis_by_section_id={
            section_id: entry.to_thermal_basis()
            for section_id, entry in intent.basis_by_section_id.items()
        },
    )
    assert result.evidence == direct

    inherited_intent = CommittedPipeSectionThermalConditionBasisIntentV1()
    fingerprint = build_committed_pipe_schedule_thermal_fingerprint_v1(
        authority
    )
    for section_id, surface_temperature_C in (
        ("section-copper-022", 60.0),
        ("section-steel-dn32", 55.0),
    ):
        inherited_intent.set_section_basis(
            section_id=section_id,
            committed_schedule_fingerprint=fingerprint,
            thermal_basis=_basis(
                surface_temperature_C=surface_temperature_C
            ),
            emissivity_override=None,
        )
    inherited_high = (
        build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
            committed_authority=authority,
            thermal_basis_intent=inherited_intent,
            default_pipe_emissivity=0.93,
        )
    )
    inherited_low = (
        build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
            committed_authority=authority,
            thermal_basis_intent=inherited_intent,
            default_pipe_emissivity=0.28,
        )
    )
    assert inherited_high.ready is True
    assert inherited_low.ready is True
    for high, low in zip(
        inherited_high.evidence.sections,
        inherited_low.evidence.sections,
    ):
        assert high.emissivity == 0.93
        assert low.emissivity == 0.28
        assert high.convection_heat_loss_W_per_m == (
            low.convection_heat_loss_W_per_m
        )
        assert high.radiation_heat_loss_W_per_m > (
            low.radiation_heat_loss_W_per_m
        )

    missing_intent = (
        build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
            committed_authority=authority,
            thermal_basis_intent=None,
        )
    )
    assert missing_intent.ready is False
    assert missing_intent.evidence is None
    assert missing_intent.section_count == 0
    assert missing_intent.blockers == (
        "Persisted committed-section thermal-condition basis intent "
        "is required",
    )

    partial = build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
        committed_authority=authority,
        thermal_basis_intent=_intent(authority, include_steel=False),
    )
    assert partial.ready is False
    assert partial.evidence is None
    assert partial.blockers == (
        "section-steel-dn32: explicit bare-pipe thermal-condition basis missing",
    )

    changed = replace(
        authority,
        sections=(
            replace(authority.sections[0], length_m=6.0),
            authority.sections[1],
        ),
    )
    stale = build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
        committed_authority=changed,
        thermal_basis_intent=intent,
    )
    assert stale.ready is False
    assert stale.evidence is None
    assert stale.blockers == (
        "Persisted committed-section thermal-condition basis fingerprint "
        "is stale",
    )
    assert stale.current_schedule_fingerprint != (
        stale.persisted_schedule_fingerprint
    )

    mismatched = _intent(authority)
    entry = mismatched.basis_by_section_id["section-copper-022"]
    mismatched.basis_by_section_id["section-copper-022"] = replace(
        entry,
        section_id="another-section",
    )
    mismatch_result = (
        build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
            committed_authority=authority,
            thermal_basis_intent=mismatched,
        )
    )
    assert mismatch_result.ready is False
    assert mismatch_result.evidence is None
    assert mismatch_result.blockers == (
        "section-copper-022: persisted section thermal basis identity mismatch",
    )

    malformed = _intent(authority)
    malformed.basis_by_section_id["section-copper-022"] = object()
    malformed_result = (
        build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
            committed_authority=authority,
            thermal_basis_intent=malformed,
        )
    )
    assert malformed_result.ready is False
    assert malformed_result.evidence is None
    assert malformed_result.blockers == (
        "section-copper-022: persisted section thermal basis entry is invalid",
    )

    unavailable = build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1(
        committed_authority=replace(authority, ready=False),
        thermal_basis_intent=intent,
    )
    assert unavailable.ready is False
    assert unavailable.evidence is None
    assert unavailable.blockers == (
        "Committed proportioning hydraulic-input authority is not ready",
    )

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_section_bare_heat_loss_runtime_handoff_v1.py"
    ).read_text(encoding="utf-8")
    assert "build_committed_pipe_section_bare_heat_loss_evidence_v1(" in source
    assert "compute_bare_pipe_heat_loss_v1" not in source
    assert "HVAC.gui_v3" not in source
    assert "from HVAC.project" not in source
    assert "import HVAC.project" not in source

    print(
        "OK — H-S66-G fresh persisted thermal-basis runtime handoff "
        "into H-S66-E passed."
    )


if __name__ == "__main__":
    main()
