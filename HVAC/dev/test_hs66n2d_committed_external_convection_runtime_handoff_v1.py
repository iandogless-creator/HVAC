from __future__ import annotations

import math
from types import SimpleNamespace

from HVAC.heatloss.physics.automatic_committed_pipe_thermal_basis_resolver_v1 import (
    build_automatic_committed_pipe_thermal_basis_resolution_v1,
)
from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    CommittedFlowReturnPairingTemperatureEvidenceV1,
    CommittedFlowReturnPairingTemperatureRowV1,
    DORMANT_POSITION_V1,
    FLOW_PIPE_V1,
    LOWER_POSITION_V1,
    RETURN_PIPE_V1,
    UPPER_POSITION_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_convection_runtime_handoff_v1 import (
    build_committed_pipe_external_convection_runtime_handoff_v1,
    external_convection_mapping_from_runtime_handoff_v1,
)
from HVAC.heatloss.physics.committed_pipe_pair_spacing_override_intent_v1 import (
    EffectiveCommittedPipePairSpacingV1,
)


def _pairing_row(section_id: str, arrangement: str):
    stacked = arrangement == STACKED_FLOW_RETURN_PAIR_V1
    return CommittedFlowReturnPairingTemperatureRowV1(
        section_id=section_id,
        section_scope="route-exclusive",
        order=1 if stacked else 2,
        external_arrangement=arrangement,
        paired=stacked,
        material_key="copper",
        material_label="Copper",
        catalogue_size_key=28,
        actual_outside_diameter_mm=28.0,
        upper_pipe_role=FLOW_PIPE_V1 if stacked else None,
        lower_pipe_role=RETURN_PIPE_V1 if stacked else None,
        flow_pipe_vertical_position=(
            UPPER_POSITION_V1 if stacked else DORMANT_POSITION_V1
        ),
        return_pipe_vertical_position=(
            LOWER_POSITION_V1 if stacked else DORMANT_POSITION_V1
        ),
        flow_pipe_surface_temperature_C=75.0,
        return_pipe_surface_temperature_C=65.0,
        vertical_order_source=(
            "Project-wide explicit upper-pipe role"
            if stacked
            else "Dormant — committed separate pipework"
        ),
        temperature_source="Environment hydronic design temperatures",
        ready=True,
        status="Ready",
    )


stacked_row = _pairing_row("stacked-001", STACKED_FLOW_RETURN_PAIR_V1)
separate_row = _pairing_row("separate-001", SEPARATE_PIPE_V1)
pairing = CommittedFlowReturnPairingTemperatureEvidenceV1(
    ready=True,
    sections=(stacked_row, separate_row),
    section_count=2,
    stacked_section_count=1,
    separate_section_count=1,
    status="Ready",
    blockers=(),
)
spacing = EffectiveCommittedPipePairSpacingV1(
    section_id="stacked-001",
    external_arrangement=STACKED_FLOW_RETURN_PAIR_V1,
    actual_outside_diameter_mm=28.0,
    nominal_default_outside_diameter_mm=28,
    support_type="paired_individual_plastic_clips",
    support_label="Paired individual plastic clips",
    centre_spacing_mm=50.0,
    locally_overridden=False,
    source="Environment universal stacked-pair spacing default",
    status="Ready",
)

handoff = build_committed_pipe_external_convection_runtime_handoff_v1(
    pairing_evidence=pairing,
    effective_spacing_by_section_id={"stacked-001": spacing},
    ambient_air_temperature_C=21.0,
    pressure_Pa=101325.0,
)
assert handoff.ready, handoff.blockers
assert handoff.section_count == 2
assert handoff.stacked_section_count == 1
assert handoff.separate_section_count == 1
assert "section-resolved Tai" in handoff.note
by_id = external_convection_mapping_from_runtime_handoff_v1(handoff)
stacked = by_id["stacked-001"]
separate = by_id["separate-001"]
assert stacked.conservative_fallback is True
assert separate.conservative_fallback is False
for row in (stacked, separate):
    assert row.flow_pipe_external_convection_coefficient_W_m2K > 0.0
    assert row.return_pipe_external_convection_coefficient_W_m2K > 0.0
    assert "Tai" in row.ambient_air_temperature_source
    expected = (
        row.flow_pipe_external_convection_coefficient_W_m2K * (75.0 - 21.0)
        + row.return_pipe_external_convection_coefficient_W_m2K * (65.0 - 21.0)
    ) / (2.0 * (70.0 - 21.0))
    assert math.isclose(
        row.effective_external_convection_coefficient_W_m2K,
        expected,
    )

# N2D completes the automatic H-S66-J rows when emissivity is also available.
authority = SimpleNamespace(
    ready=True,
    sections=(
        SimpleNamespace(section_id="stacked-001"),
        SimpleNamespace(section_id="separate-001"),
    ),
)
automatic = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule-a",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=21.0,
    default_pipe_emissivity=0.20,
    external_convection_by_section_id=by_id,
)
assert automatic.ready
assert automatic.complete_section_count == 2
for row in automatic.sections:
    assert row.complete
    assert row.external_convection_coefficient_W_m2K > 0.0
    assert "N2A" in row.external_convection_source or "stacked" in row.external_convection_source.lower()
    assert "N2D external convection resolved" in row.status

# A fresh manual H-S66-F basis still has precedence over N2D.
manual = SimpleNamespace(
    surface_temperature_C=58.0,
    ambient_air_temperature_C=19.0,
    mean_radiant_temperature_C=18.0,
    emissivity=0.94,
    external_convection_coefficient_W_m2K=5.2,
)
intent = SimpleNamespace(
    committed_schedule_fingerprint="schedule-a",
    basis_by_section_id={"stacked-001": manual},
)
mixed = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule-a",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=21.0,
    default_pipe_emissivity=0.20,
    thermal_basis_intent=intent,
    external_convection_by_section_id=by_id,
)
manual_row = next(row for row in mixed.sections if row.section_id == "stacked-001")
assert manual_row.external_convection_coefficient_W_m2K == 5.2
assert manual_row.external_convection_source == "Manual H-S66-F override"

# Ta/Tai evidence cannot be combined with a different automatic air basis.
mismatched_air = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule-a",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=20.0,
    default_pipe_emissivity=0.20,
    external_convection_by_section_id=by_id,
)
assert mismatched_air.complete_section_count == 0
assert any(
    "local ambient-air temperature does not match" in blocker
    for blocker in mismatched_air.sections[0].blockers
)

# Missing stacked spacing and dormant separate spacing both fail closed.
missing_spacing = build_committed_pipe_external_convection_runtime_handoff_v1(
    pairing_evidence=pairing,
    effective_spacing_by_section_id={},
    ambient_air_temperature_C=21.0,
    pressure_Pa=101325.0,
)
assert not missing_spacing.ready
assert any("spacing is required" in value for value in missing_spacing.blockers)

dormant_spacing = build_committed_pipe_external_convection_runtime_handoff_v1(
    pairing_evidence=pairing,
    effective_spacing_by_section_id={
        "stacked-001": spacing,
        "separate-001": EffectiveCommittedPipePairSpacingV1(
            section_id="separate-001",
            external_arrangement=SEPARATE_PIPE_V1,
            actual_outside_diameter_mm=28.0,
            nominal_default_outside_diameter_mm=28,
            support_type="paired_individual_plastic_clips",
            support_label="Paired individual plastic clips",
            centre_spacing_mm=50.0,
            locally_overridden=False,
            source="invalid test evidence",
            status="invalid",
        ),
    },
    ambient_air_temperature_C=21.0,
    pressure_Pa=101325.0,
)
assert not dormant_spacing.ready
assert any("dormant" in value for value in dormant_spacing.blockers)

print(
    "OK — H-S66-N2D separate/stacked external-convection runtime handoff "
    "into the automatic thermal-basis resolver passed."
)
