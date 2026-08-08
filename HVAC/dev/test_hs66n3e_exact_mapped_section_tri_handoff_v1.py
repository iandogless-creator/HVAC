# ======================================================================
# H-S66-N3E — Exact mapped-section Tri handoff into N3C
# ======================================================================

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import ModuleType
import sys


# Avoid the legacy Qt-owning HVAC.core package initialiser in headless tests.
ROOT = Path(__file__).resolve().parents[2]
if "HVAC.core" not in sys.modules:
    core_package = ModuleType("HVAC.core")
    core_package.__path__ = [str(ROOT / "HVAC/core")]
    sys.modules["HVAC.core"] = core_package

from HVAC.heatloss.physics.committed_pipe_section_ambient_tai_runtime_handoff_v1 import (
    build_committed_pipe_section_ambient_tai_runtime_handoff_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_room_mapping_intent_v1 import (
    CommittedPipeSectionRoomMappingIntentV1,
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


ADAPTER = ROOT / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"


section = CommittedProportioningHydraulicSectionV1(
    section_id="mapped-section",
    section_scope="subleg",
    route_ids=("route",),
    order=0,
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
    sections=(section,),
    status="Ready",
)
room_ids = ("room-a",)
mapping = CommittedPipeSectionRoomMappingIntentV1()
set_current_committed_pipe_section_room_mapping_v1(
    intent=mapping,
    committed_authority=authority,
    available_room_ids=room_ids,
    section_id="mapped-section",
    room_id="room-a",
)
tai = CommittedRoomCvTaiEvidenceV1(
    ready=True,
    rooms=(
        CommittedRoomCvTaiEvidenceRowV1(
            room_id="room-a",
            total_fabric_heat_loss_W=480.0,
            total_exposed_area_m2=20.0,
            tei_C=21.0,
            cv_K=5.0,
            tai_C=26.0,
            tei_source="Room Ti",
            ready=True,
            status="Ready",
        ),
    ),
    room_count=1,
    status="Ready",
)
tri = CommittedRoomMeanRadiantTemperatureAuthorityV1(
    ready=True,
    rooms=(
        CommittedRoomMeanRadiantTemperatureRowV1(
            room_id="room-a",
            mean_radiant_temperature_C=18.25,
            surface_count=6,
            radiant_view_factor_sum=1.0,
            source="N3D3 enclosure area-fraction weighting",
            ready=True,
            status="Ready",
        ),
    ),
    room_count=1,
    status="Ready",
)

resolved = build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    room_mapping_intent=mapping,
    room_cv_tai_evidence=tai,
    room_mean_radiant_authority=tri,
    environment_fallback_temperature_C=19.0,
)
assert resolved.ready, resolved.blockers
row = resolved.sections[0]
assert row.ambient_air_temperature_C == 26.0
assert row.mean_radiant_temperature_C == 18.25
assert row.ambient_air_temperature_C != row.mean_radiant_temperature_C
assert "N3A room Tai" in row.ambient_air_temperature_source
assert "N3D room Tri" in row.mean_radiant_temperature_source
assert "temporary MRT proxy" not in row.mean_radiant_temperature_source

missing_tri = build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    room_mapping_intent=mapping,
    room_cv_tai_evidence=tai,
    room_mean_radiant_authority=replace(
        tri, ready=False, rooms=(), blockers=("stale Tri",)
    ),
    environment_fallback_temperature_C=19.0,
)
assert not missing_tri.ready
assert any("fresh N3D room Tri" in value for value in missing_tri.blockers)
assert "stale Tri" in missing_tri.blockers


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


adapter_handoff = _function_source(
    ADAPTER, "_build_committed_pipe_section_ambient_tai_handoff_v1"
)
assert "build_committed_room_mean_radiant_from_project_state_v1" in (
    adapter_handoff
)
assert "room_mean_radiant_authority=room_mean_radiant_authority" in (
    adapter_handoff
)

print(
    "OK — H-S66-N3E exact mapped-section Tri replaces the temporary MRT "
    "proxy in N3C."
)
