# ======================================================================
# H-S66-N3E1 — Automatic thermal-preview refresh after room mapping
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
ADAPTER = ROOT / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


panel_source = PANEL.read_text(encoding="utf-8")
assert "Automatic preview displays every resolved value immediately" in (
    panel_source
)
assert "Exact-room sections use room Tai" in panel_source
assert "N3D room Tri" in panel_source
assert "Not set is blocked" in panel_source
assert "Blank fields mean the named evidence is " in panel_source
assert '"blocked; the status reports why.' in panel_source
assert "Apply persists the displayed " in panel_source
assert '"complete basis; editing a value' in panel_source
assert "Environment air/MRT and universal pipe emissivity" not in panel_source

mapping_selection = _function_source(
    PANEL, "_on_committed_pipe_section_room_mapping_section_changed_v1"
)
assert "_select_committed_pipe_thermal_basis_section_v1(section_id)" in (
    mapping_selection
)
thermal_focus = _function_source(
    PANEL, "_select_committed_pipe_thermal_basis_section_v1"
)
assert "_committed_pipe_thermal_basis_section_combo_v1" in thermal_focus
assert "combo.findData(str(section_id))" in thermal_focus
assert "combo.setCurrentIndex(index)" in thermal_focus

mapping_callback = _function_source(
    ADAPTER, "set_committed_pipe_section_room_mapping_intent_v1"
)
assert "self.refresh()" in mapping_callback
mapping_editor = _function_source(
    ADAPTER, "_push_committed_pipe_section_room_mapping_editor_v1"
)
assert "Environment / general space" in mapping_editor
assert "Not set" in mapping_editor

print(
    "OK — H-S66-N3E1 room-mapping selection immediately focuses the "
    "automatic thermal preview with truthful guidance and blockers."
)
