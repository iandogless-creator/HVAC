from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from HVAC.heatloss.physics.automatic_committed_pipe_thermal_basis_resolver_v1 import (
    build_automatic_committed_pipe_thermal_basis_resolution_v1,
)


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
N3C = ROOT / "HVAC/heatloss/physics/committed_pipe_section_ambient_tai_runtime_handoff_v1.py"


authority = SimpleNamespace(
    ready=True,
    sections=(SimpleNamespace(section_id="mapped-section"),),
)
convection = {
    "mapped-section": SimpleNamespace(
        section_id="mapped-section",
        ready=True,
        ambient_air_temperature_C=26.0,
        mean_surface_temperature_C=70.0,
        effective_external_convection_coefficient_W_m2K=7.5,
        source="N2D using exact mapped-room Tai",
    )
}
resolved = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=99.0,
    default_pipe_emissivity=0.2,
    external_convection_by_section_id=convection,
    ambient_air_temperature_by_section_id={"mapped-section": 26.0},
    ambient_air_temperature_source_by_section_id={
        "mapped-section": "N3A room Tai — exact room room-a"
    },
    mean_radiant_temperature_by_section_id={"mapped-section": 18.5},
    mean_radiant_temperature_source_by_section_id={
        "mapped-section": "N3D room Tri — exact room room-a"
    },
)
assert resolved.ready, resolved.blockers
row = resolved.sections[0]
assert row.complete
assert row.ambient_air_temperature_C == 26.0
assert row.mean_radiant_temperature_C == 18.5
assert row.ambient_air_temperature_C != row.mean_radiant_temperature_C
assert "room Tai" in row.ambient_air_temperature_source
assert "N3D room Tri" in row.mean_radiant_temperature_source

# A missing separate MRT authority fails closed; Tai is not copied into MRT.
blocked = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=99.0,
    default_pipe_emissivity=0.2,
    external_convection_by_section_id=convection,
    ambient_air_temperature_by_section_id={"mapped-section": 26.0},
    ambient_air_temperature_source_by_section_id={"mapped-section": "room Tai"},
    mean_radiant_temperature_by_section_id={},
    mean_radiant_temperature_source_by_section_id={},
)
assert not blocked.ready
assert blocked.sections[0].mean_radiant_temperature_C is None
assert any("mean-radiant" in value for value in blocked.blockers)


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


n3c_source = N3C.read_text(encoding="utf-8")
assert "mean_radiant_temperature_C" in n3c_source
assert "temporary MRT proxy" not in n3c_source
assert "mean_radiant_C = tri_by_room_id[room_id]" in n3c_source
assert "mean_radiant_C = tei_by_room_id[room_id]" not in n3c_source
for name in (
    "set_committed_pipe_thermal_basis_v1",
    "_push_committed_pipe_thermal_basis_editor_v1",
):
    source = _function_source(ADAPTER, name)
    assert "mean_radiant_temperature_by_section_id" in source
    assert "mean_radiant_temperature_source_by_section_id" in source

print(
    "OK — H-S66-N3C1 ambient Tai remains separate from explicitly sourced "
    "mean-radiant-temperature evidence."
)
