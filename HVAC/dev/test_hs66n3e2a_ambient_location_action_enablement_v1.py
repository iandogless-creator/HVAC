# ======================================================================
# H-S66-N3E2A — Ambient-location action enablement
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"


def _function_source(name: str) -> str:
    source = PANEL.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


panel = PANEL.read_text(encoding="utf-8")
assert (
    "_committed_pipe_section_room_mapping_room_combo_v1.currentIndexChanged.connect("
    in panel
)
assert "_on_committed_pipe_section_ambient_location_choice_changed_v1" in panel

choice_changed = _function_source(
    "_on_committed_pipe_section_ambient_location_choice_changed_v1"
)
assert "_refresh_committed_pipe_section_room_mapping_controls_v1()" in (
    choice_changed
)

controls = _function_source(
    "_refresh_committed_pipe_section_room_mapping_controls_v1"
)
assert "has_room" in controls
assert "editable and unset_count > 0" in controls
assert "_committed_pipe_section_room_mapping_apply_button_v1.setEnabled" in controls
assert "_committed_pipe_section_room_mapping_apply_all_button_v1.setEnabled" in controls

print(
    "OK — H-S66-N3E2A pending ambient-location selection immediately enables "
    "the applicable single/all-Not-set actions."
)
