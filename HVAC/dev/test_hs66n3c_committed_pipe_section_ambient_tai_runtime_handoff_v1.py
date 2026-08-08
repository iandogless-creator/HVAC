from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys


# Avoid the legacy Qt-owning HVAC.core package initialiser in headless tests.
ROOT = Path(__file__).resolve().parents[2]
if "HVAC.core" not in sys.modules:
    core_package = ModuleType("HVAC.core")
    core_package.__path__ = [str(ROOT / "HVAC/core")]
    sys.modules["HVAC.core"] = core_package

from HVAC.heatloss.physics.automatic_committed_pipe_thermal_basis_resolver_v1 import (
    build_automatic_committed_pipe_thermal_basis_resolution_v1,
)
from HVAC.heatloss.physics.committed_flow_return_pairing_temperature_evidence_v1 import (
    CommittedFlowReturnPairingTemperatureEvidenceV1,
    CommittedFlowReturnPairingTemperatureRowV1,
    DORMANT_POSITION_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    SEPARATE_PIPE_V1,
)
from HVAC.heatloss.physics.committed_pipe_external_convection_runtime_handoff_v1 import (
    build_committed_pipe_external_convection_runtime_handoff_v1,
    external_convection_mapping_from_runtime_handoff_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_ambient_tai_runtime_handoff_v1 import (
    ambient_temperature_mapping_from_handoff_v1,
    ambient_temperature_source_mapping_from_handoff_v1,
    build_committed_pipe_section_ambient_tai_runtime_handoff_v1,
    mean_radiant_temperature_mapping_from_handoff_v1,
    mean_radiant_temperature_source_mapping_from_handoff_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_room_mapping_intent_v1 import (
    CommittedPipeSectionRoomMappingIntentV1,
    set_current_committed_pipe_section_environment_location_v1,
    set_current_committed_pipe_section_room_mapping_v1,
)
from HVAC.heatloss.physics.committed_room_cv_tai_evidence_v1 import (
    CommittedRoomCvTaiEvidenceRowV1,
    CommittedRoomCvTaiEvidenceV1,
)
from HVAC.heatloss.physics.committed_room_mean_radiant_temperature_authority_v1 import (
    CommittedRoomMeanRadiantTemperatureAuthorityV1,
    CommittedRoomMeanRadiantTemperatureRowV1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)


ADAPTER_PATH = ROOT / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"


def _section(section_id: str, order: int):
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
        length_m=3.0,
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


authority = CommittedProportioningHydraulicInputAuthorityV1(
    ready=True,
    sections=(_section("section-room", 0), _section("section-env", 1)),
    status="Ready — fixture",
)
room_ids = ("room-a", "room-b")
mapping_intent = CommittedPipeSectionRoomMappingIntentV1()
set_current_committed_pipe_section_room_mapping_v1(
    intent=mapping_intent,
    committed_authority=authority,
    available_room_ids=room_ids,
    section_id="section-room",
    room_id="room-a",
)
set_current_committed_pipe_section_environment_location_v1(
    intent=mapping_intent,
    committed_authority=authority,
    section_id="section-env",
)
room_evidence = CommittedRoomCvTaiEvidenceV1(
    ready=True,
    rooms=(
        CommittedRoomCvTaiEvidenceRowV1(
            room_id="room-a",
            total_fabric_heat_loss_W=480.0,
            total_exposed_area_m2=20.0,
            tei_C=21.0,
            cv_K=5.0,
            tai_C=26.0,
            tei_source="Room internal design temperature (Ti/Tei)",
            ready=True,
            status="Ready",
        ),
        CommittedRoomCvTaiEvidenceRowV1(
            room_id="room-b",
            total_fabric_heat_loss_W=240.0,
            total_exposed_area_m2=20.0,
            tei_C=20.0,
            cv_K=2.5,
            tai_C=22.5,
            tei_source="Room internal design temperature (Ti/Tei)",
            ready=True,
            status="Ready",
        ),
    ),
    room_count=2,
    status="Ready",
    blockers=(),
)
room_mrt = CommittedRoomMeanRadiantTemperatureAuthorityV1(
    ready=True,
    rooms=(
        CommittedRoomMeanRadiantTemperatureRowV1(
            room_id="room-a",
            mean_radiant_temperature_C=18.5,
            surface_count=6,
            radiant_view_factor_sum=1.0,
            source="N3D3 accepted-enclosure area-fraction weighting",
            ready=True,
            status="Ready",
        ),
        CommittedRoomMeanRadiantTemperatureRowV1(
            room_id="room-b",
            mean_radiant_temperature_C=17.5,
            surface_count=6,
            radiant_view_factor_sum=1.0,
            source="N3D3 accepted-enclosure area-fraction weighting",
            ready=True,
            status="Ready",
        ),
    ),
    room_count=2,
    status="Ready",
    blockers=(),
)

handoff = build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    room_mapping_intent=mapping_intent,
    room_cv_tai_evidence=room_evidence,
    room_mean_radiant_authority=room_mrt,
    environment_fallback_temperature_C=19.0,
)
assert handoff.ready, handoff.blockers
assert handoff.section_count == 2
assert handoff.room_mapped_section_count == 1
assert handoff.environment_fallback_section_count == 1
ambient = ambient_temperature_mapping_from_handoff_v1(handoff)
sources = ambient_temperature_source_mapping_from_handoff_v1(handoff)
mrt = mean_radiant_temperature_mapping_from_handoff_v1(handoff)
mrt_sources = mean_radiant_temperature_source_mapping_from_handoff_v1(handoff)
assert ambient == {"section-room": 26.0, "section-env": 19.0}
assert mrt == {"section-room": 18.5, "section-env": 19.0}
assert "room-a" in sources["section-room"]
assert "Environment" in sources["section-env"]
assert "N3D room Tri" in mrt_sources["section-room"]


def _pairing_row(section_id: str, order: int):
    return CommittedFlowReturnPairingTemperatureRowV1(
        section_id=section_id,
        section_scope="route-exclusive",
        order=order,
        external_arrangement=SEPARATE_PIPE_V1,
        paired=False,
        material_key="copper",
        material_label="Copper",
        catalogue_size_key=22,
        actual_outside_diameter_mm=22.0,
        upper_pipe_role=None,
        lower_pipe_role=None,
        flow_pipe_vertical_position=DORMANT_POSITION_V1,
        return_pipe_vertical_position=DORMANT_POSITION_V1,
        flow_pipe_surface_temperature_C=75.0,
        return_pipe_surface_temperature_C=65.0,
        vertical_order_source="Dormant — committed separate pipework",
        temperature_source="Environment hydronic design temperatures",
        ready=True,
        status="Ready",
    )


pairing = CommittedFlowReturnPairingTemperatureEvidenceV1(
    ready=True,
    sections=(
        _pairing_row("section-room", 0),
        _pairing_row("section-env", 1),
    ),
    section_count=2,
    stacked_section_count=0,
    separate_section_count=2,
    status="Ready",
    blockers=(),
)
convection_handoff = build_committed_pipe_external_convection_runtime_handoff_v1(
    pairing_evidence=pairing,
    effective_spacing_by_section_id={},
    ambient_air_temperature_C=None,
    pressure_Pa=101325.0,
    ambient_air_temperature_by_section_id=ambient,
    ambient_air_temperature_source_by_section_id=sources,
)
assert convection_handoff.ready, convection_handoff.blockers
convection = external_convection_mapping_from_runtime_handoff_v1(
    convection_handoff
)
assert convection["section-room"].ambient_air_temperature_C == 26.0
assert convection["section-env"].ambient_air_temperature_C == 19.0

automatic = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint=(
        mapping_intent.committed_schedule_fingerprint
    ),
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=99.0,
    default_pipe_emissivity=0.2,
    external_convection_by_section_id=convection,
    ambient_air_temperature_by_section_id=ambient,
    ambient_air_temperature_source_by_section_id=sources,
    mean_radiant_temperature_by_section_id=mrt,
    mean_radiant_temperature_source_by_section_id=mrt_sources,
)
assert automatic.ready, automatic.blockers
assert automatic.complete_section_count == 2
automatic_by_id = {row.section_id: row for row in automatic.sections}
assert automatic_by_id["section-room"].ambient_air_temperature_C == 26.0
assert automatic_by_id["section-room"].mean_radiant_temperature_C == 18.5
assert "room-a" in automatic_by_id["section-room"].ambient_air_temperature_source
assert "N3D room Tri" in automatic_by_id["section-room"].mean_radiant_temperature_source
assert automatic_by_id["section-env"].ambient_air_temperature_C == 19.0
assert "Environment" in automatic_by_id["section-env"].ambient_air_temperature_source
assert all("99" not in row.status for row in automatic.sections)

# A mapped section fails closed when its fresh room Tai authority is absent.
blocked = build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    room_mapping_intent=mapping_intent,
    room_cv_tai_evidence=replace(
        room_evidence, ready=False, rooms=(), blockers=("stale",)
    ),
    room_mean_radiant_authority=room_mrt,
    environment_fallback_temperature_C=19.0,
)
assert not blocked.ready
assert any("fresh N3A room Tai" in value for value in blocked.blockers)

# A mapped section also fails closed when fresh room Tri is unavailable.
blocked_mrt = build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    room_mapping_intent=mapping_intent,
    room_cv_tai_evidence=room_evidence,
    room_mean_radiant_authority=replace(
        room_mrt, ready=False, rooms=(), blockers=("stale Tri",)
    ),
    environment_fallback_temperature_C=19.0,
)
assert not blocked_mrt.ready
assert any("fresh N3D room Tri" in value for value in blocked_mrt.blockers)

# Absence is Not set and blocks instead of silently falling back.
not_set = build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    room_mapping_intent=CommittedPipeSectionRoomMappingIntentV1(),
    room_cv_tai_evidence=replace(
        room_evidence, ready=False, rooms=(), blockers=("stale",)
    ),
    room_mean_radiant_authority=replace(
        room_mrt, ready=False, rooms=(), blockers=("stale Tri",)
    ),
    environment_fallback_temperature_C=19.0,
)
assert not not_set.ready
assert any("Not set" in value for value in not_set.blockers)

# Exact mappings only: missing or extra section ambient evidence blocks N2D/J.
missing_ambient = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=21.0,
    ambient_air_temperature_by_section_id={"section-room": 26.0},
    ambient_air_temperature_source_by_section_id={"section-room": "room"},
)
assert not missing_ambient.ready
assert any("section-env" in value for value in missing_ambient.blockers)


def _function_source(function_name: str) -> str:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {function_name}")


adapter_handoff = _function_source(
    "_build_committed_pipe_section_ambient_tai_handoff_v1"
)
assert "build_committed_room_cv_tai_from_project_state_v1" in adapter_handoff
assert "build_committed_room_mean_radiant_from_project_state_v1" in adapter_handoff
assert "build_committed_pipe_section_ambient_tai_runtime_handoff_v1" in adapter_handoff
adapter_convection = _function_source(
    "_build_committed_pipe_external_convection_mapping_v1"
)
assert "ambient_air_temperature_by_section_id" in adapter_convection
bulk = _function_source("set_committed_pipe_thermal_basis_v1")
preview = _function_source("_push_committed_pipe_thermal_basis_editor_v1")
for source in (bulk, preview):
    assert "ambient_air_temperature_by_section_id" in source
    assert "ambient_air_temperature_source_by_section_id" in source

print(
    "OK — H-S66-N3C exact mapped-room Tai and explicit Environment choice "
    "hand off through N2D into the automatic thermal-basis resolver."
)
