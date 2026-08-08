from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import ModuleType
import sys


# Avoid the legacy Qt-owning HVAC.core package initialiser in headless tests.
root = Path(__file__).resolve().parents[2]
if "HVAC.core" not in sys.modules:
    core_package = ModuleType("HVAC.core")
    core_package.__path__ = [str(root / "HVAC/core")]
    sys.modules["HVAC.core"] = core_package

from HVAC.heatloss.physics.committed_pipe_section_room_mapping_intent_v1 import (
    ENVIRONMENT_AMBIENT_SCOPE_V1,
    NOT_SET_AMBIENT_SCOPE_V1,
    ROOM_AMBIENT_SCOPE_V1,
    CommittedPipeSectionRoomMappingIntentV1,
    build_committed_pipe_section_room_mapping_fingerprint_v1,
    committed_pipe_section_room_mapping_intent_from_dict_v1,
    resolve_effective_committed_pipe_section_room_mapping_v1,
    set_current_committed_pipe_section_environment_location_v1,
    set_current_committed_pipe_section_room_mapping_v1,
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


def _authority(*sections):
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        sections=tuple(sections),
        status="Ready — fixture",
    )


section_a = _section("section-a", 1)
section_b = _section("section-b", 2)
authority = _authority(section_a, section_b)
room_ids = ("room-a", "room-b")
intent = CommittedPipeSectionRoomMappingIntentV1()

# Absence is explicitly Not set and must not imply Environment authority.
inherited = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    intent=intent,
    section_id="section-a",
)
assert inherited.ambient_scope == NOT_SET_AMBIENT_SCOPE_V1
assert inherited.room_id is None
assert inherited.explicitly_mapped is False
assert inherited.explicitly_set is False
assert "No committed" in inherited.source

set_current_committed_pipe_section_room_mapping_v1(
    intent=intent,
    committed_authority=authority,
    available_room_ids=room_ids,
    section_id="section-a",
    room_id="room-a",
)
mapped = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    intent=intent,
    section_id="section-a",
)
assert mapped.ambient_scope == ROOM_AMBIENT_SCOPE_V1
assert mapped.room_id == "room-a"
assert mapped.explicitly_mapped is True

# Other exact sections remain Not set until explicitly disposed.
other = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    intent=intent,
    section_id="section-b",
)
assert other.ambient_scope == NOT_SET_AMBIENT_SCOPE_V1
assert other.room_id is None

set_current_committed_pipe_section_environment_location_v1(
    intent=intent,
    committed_authority=authority,
    section_id="section-b",
)
environment = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=authority,
    available_room_ids=room_ids,
    intent=intent,
    section_id="section-b",
)
assert environment.ambient_scope == ENVIRONMENT_AMBIENT_SCOPE_V1
assert environment.room_id is None
assert environment.explicitly_set is True
assert environment.explicitly_mapped is False

try:
    set_current_committed_pipe_section_room_mapping_v1(
        intent=intent,
        committed_authority=authority,
        available_room_ids=room_ids,
        section_id="missing-section",
        room_id="room-a",
    )
except ValueError as exc:
    assert "Exact committed pipe section" in str(exc)
else:
    raise AssertionError("Unknown committed section accepted a room mapping")

try:
    set_current_committed_pipe_section_room_mapping_v1(
        intent=intent,
        committed_authority=authority,
        available_room_ids=room_ids,
        section_id="section-b",
        room_id="missing-room",
    )
except ValueError as exc:
    assert "Exact current ProjectState room" in str(exc)
else:
    raise AssertionError("Unknown room identity was accepted")

round_trip = committed_pipe_section_room_mapping_intent_from_dict_v1(
    intent.to_dict()
)
assert round_trip == intent
project = ProjectState(project_id="project-1", name="Project")
project.hydronic_committed_pipe_section_room_mapping_intent = intent
restored = ProjectState.from_dict(project.to_dict())
assert restored.hydronic_committed_pipe_section_room_mapping_intent == intent

stale_authority = _authority(replace(section_a, length_m=4.0), section_b)
assert build_committed_pipe_section_room_mapping_fingerprint_v1(
    stale_authority
) != intent.committed_schedule_fingerprint
try:
    resolve_effective_committed_pipe_section_room_mapping_v1(
        committed_authority=stale_authority,
        available_room_ids=room_ids,
        intent=intent,
        section_id="section-a",
    )
except ValueError as exc:
    assert "stale" in str(exc)
else:
    raise AssertionError("Stale section-to-room mapping remained effective")

try:
    resolve_effective_committed_pipe_section_room_mapping_v1(
        committed_authority=authority,
        available_room_ids=("room-b",),
        intent=intent,
        section_id="section-a",
    )
except ValueError as exc:
    assert "missing ProjectState room" in str(exc)
else:
    raise AssertionError("Mapping to a deleted room remained effective")

assert intent.clear_section_room("section-a") is True
assert intent.clear_section_room("section-b") is True
assert intent.committed_schedule_fingerprint == ""
assert not intent.mapping_by_section_id
cleared = resolve_effective_committed_pipe_section_room_mapping_v1(
    committed_authority=stale_authority,
    available_room_ids=room_ids,
    intent=intent,
    section_id="section-a",
)
assert cleared.ambient_scope == NOT_SET_AMBIENT_SCOPE_V1

invalid = committed_pipe_section_room_mapping_intent_from_dict_v1(
    {
        "schema": "wrong",
        "committed_schedule_fingerprint": "fingerprint",
        "mapping_by_section_id": {
            "section-a": {"section_id": "section-a", "room_id": "room-a"}
        },
    }
)
assert not invalid.mapping_by_section_id

source = Path(
    "HVAC/heatloss/physics/committed_pipe_section_room_mapping_intent_v1.py"
).read_text(encoding="utf-8")
assert "HVAC.gui_v3" not in source
assert "compute_cv_tai" not in source
assert "ambient_air_temperature_C" not in source

print(
    "OK — H-S66-N3B persisted exact committed-section ambient-location "
    "intent distinguishes Not set, Environment and exact room."
)
