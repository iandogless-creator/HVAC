from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = ROOT / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
ADAPTER_PATH = ROOT / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_source(path: Path, function_name: str) -> str:
    source = _source(path)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {function_name}")


panel = _source(PANEL_PATH)
adapter = _source(ADAPTER_PATH)

for text in (
    "Committed-section ambient location — room mapping",
    "Effective ambient location:",
    "Apply room mapping",
    "Clear selected mapping",
    "Clear all room mappings",
    "Unmapped sections retain the Environment",
):
    assert text in panel

apply_handler = _function_source(
    PANEL_PATH, "_on_apply_committed_pipe_section_room_mapping_v1"
)
assert '"action": "set"' in apply_handler
assert '"section_id"' in apply_handler
assert '"room_id"' in apply_handler
assert "ProjectState" not in apply_handler
assert "resolve_effective" not in apply_handler
assert "compute_cv_tai" not in apply_handler

controls = _function_source(
    PANEL_PATH, "_refresh_committed_pipe_section_room_mapping_controls_v1"
)
assert "not stale" in controls
assert 'row.get("explicitly_mapped")' in controls

handler = _function_source(
    ADAPTER_PATH, "set_committed_pipe_section_room_mapping_intent_v1"
)
assert "set_current_committed_pipe_section_room_mapping_v1" in handler
assert ".clear_section_room(" in handler
assert ".clear_all()" in handler
assert "project.mark_dirty()" in handler
assert "self.refresh()" in handler
assert "compute_cv_tai" not in handler
assert "external_convection" not in handler

restore = _function_source(
    ADAPTER_PATH, "_push_committed_pipe_section_room_mapping_editor_v1"
)
assert "build_committed_pipe_section_room_mapping_fingerprint_v1" in restore
assert "resolve_effective_committed_pipe_section_room_mapping_v1" in restore
assert '"available_rooms"' not in restore
assert "available_rooms=available_rooms" in restore
assert '"explicitly_mapped"' in restore
assert "Environment ambient fallback" in restore
assert "clear all room mappings" in restore
assert "compute_cv_tai" not in restore
assert "external_convection" not in restore

refresh = _function_source(
    ADAPTER_PATH, "_refresh_committed_pipe_bare_heat_loss_v1"
)
assert "_push_committed_pipe_section_room_mapping_editor_v1" in refresh

print(
    "OK — H-S66-N3B1 manual exact committed-section room mapping "
    "controls passed."
)
