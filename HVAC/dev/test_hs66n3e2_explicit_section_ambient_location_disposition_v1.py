# ======================================================================
# H-S66-N3E2 — Explicit section ambient-location disposition
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path
from types import ModuleType
import sys


ROOT = Path(__file__).resolve().parents[2]
if "HVAC.core" not in sys.modules:
    core_package = ModuleType("HVAC.core")
    core_package.__path__ = [str(ROOT / "HVAC/core")]
    sys.modules["HVAC.core"] = core_package

from HVAC.heatloss.physics.committed_pipe_section_room_mapping_intent_v1 import (
    ENVIRONMENT_AMBIENT_SCOPE_V1,
    NOT_SET_AMBIENT_SCOPE_V1,
    ROOM_AMBIENT_SCOPE_V1,
    CommittedPipeSectionRoomMappingIntentV1,
    committed_pipe_section_room_mapping_intent_from_dict_v1,
    resolve_effective_committed_pipe_section_room_mapping_v1,
    set_all_unset_committed_pipe_section_ambient_locations_v1,
    set_current_committed_pipe_section_environment_location_v1,
    set_current_committed_pipe_section_room_mapping_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)


PANEL = ROOT / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
ADAPTER = ROOT / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"


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
    sections=(_section("section-a", 0), _section("section-b", 1)),
    status="Ready — fixture",
)
rooms = ("room-a",)
intent = CommittedPipeSectionRoomMappingIntentV1()

not_set = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=rooms,
    intent=intent,
    section_id="section-a",
)
assert not_set.ambient_scope == NOT_SET_AMBIENT_SCOPE_V1
assert not not_set.explicitly_set
assert "Blocked" in not_set.status and "Not set" in not_set.status

set_current_committed_pipe_section_environment_location_v1(
    intent=intent,
    committed_authority=authority,
    section_id="section-a",
)
environment = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=rooms,
    intent=intent,
    section_id="section-a",
)
assert environment.ambient_scope == ENVIRONMENT_AMBIENT_SCOPE_V1
assert environment.explicitly_set and not environment.explicitly_mapped
assert environment.room_id is None

set_current_committed_pipe_section_room_mapping_v1(
    intent=intent,
    committed_authority=authority,
    available_room_ids=rooms,
    section_id="section-b",
    room_id="room-a",
)
room = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=rooms,
    intent=intent,
    section_id="section-b",
)
assert room.ambient_scope == ROOM_AMBIENT_SCOPE_V1
assert room.explicitly_set and room.explicitly_mapped
assert room.room_id == "room-a"

round_trip = committed_pipe_section_room_mapping_intent_from_dict_v1(
    intent.to_dict()
)
assert round_trip == intent
assert intent.clear_section_room("section-a")
cleared = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=rooms,
    intent=intent,
    section_id="section-a",
)
assert cleared.ambient_scope == NOT_SET_AMBIENT_SCOPE_V1

count = set_all_unset_committed_pipe_section_ambient_locations_v1(
    intent=intent,
    committed_authority=authority,
    available_room_ids=rooms,
    ambient_scope=ENVIRONMENT_AMBIENT_SCOPE_V1,
)
assert count == 1
assert intent.mapping_by_section_id["section-a"].ambient_scope == (
    ENVIRONMENT_AMBIENT_SCOPE_V1
)
assert intent.mapping_by_section_id["section-b"].ambient_scope == (
    ROOM_AMBIENT_SCOPE_V1
)
assert set_all_unset_committed_pipe_section_ambient_locations_v1(
    intent=intent,
    committed_authority=authority,
    available_room_ids=rooms,
    ambient_scope=ENVIRONMENT_AMBIENT_SCOPE_V1,
) == 0


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


panel = PANEL.read_text(encoding="utf-8")
for wording in (
    "Not set — unresolved",
    "Environment / general space",
    "Apply ambient location",
    "Clear selected location",
    "length-fraction allocation is deferred",
    "Apply selected location to all Not set sections",
):
    assert wording in panel

apply_handler = _function_source(
    PANEL, "_on_apply_committed_pipe_section_room_mapping_v1"
)
assert "set_environment" in apply_handler
assert "set_room" in apply_handler

adapter_handler = _function_source(
    ADAPTER, "set_committed_pipe_section_room_mapping_intent_v1"
)
assert "set_current_committed_pipe_section_environment_location_v1" in (
    adapter_handler
)
assert "set_current_committed_pipe_section_room_mapping_v1" in adapter_handler
assert "set_all_unset_committed_pipe_section_ambient_locations_v1" in (
    adapter_handler
)

print(
    "OK — H-S66-N3E2 explicitly separates Not set, Environment / general "
    "space and exact-room ambient-location dispositions."
)
