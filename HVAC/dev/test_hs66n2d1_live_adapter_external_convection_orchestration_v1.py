from __future__ import annotations

import ast
from pathlib import Path


root = Path(__file__).resolve().parents[2]
adapter_path = root / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
source = adapter_path.read_text(encoding="utf-8")
tree = ast.parse(source)


def _method(name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Adapter method missing: {name}")


def _calls(node: ast.AST) -> set[str]:
    result: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        function = child.func
        if isinstance(function, ast.Name):
            result.add(function.id)
        elif isinstance(function, ast.Attribute):
            result.add(function.attr)
    return result


orchestrator = _method(
    "_build_committed_pipe_external_convection_mapping_v1"
)
orchestrator_calls = _calls(orchestrator)
assert "_resolve_committed_pipe_external_arrangement_authority_v1" in orchestrator_calls
assert "build_committed_flow_return_pairing_temperature_evidence_v1" in orchestrator_calls
assert "resolve_effective_committed_pipe_pair_spacing_v1" in orchestrator_calls
assert "build_committed_pipe_external_convection_runtime_handoff_v1" in orchestrator_calls
assert "external_convection_mapping_from_runtime_handoff_v1" in orchestrator_calls

orchestrator_source = ast.get_source_segment(source, orchestrator) or ""
assert "hydronic_committed_pipe_pair_vertical_order_intent" in orchestrator_source
assert "hydronic_committed_pipe_pair_spacing_override_intent" in orchestrator_source
assert "committed_schedule_fingerprint" in orchestrator_source
assert "pressure_Pa=101325.0" in orchestrator_source
assert "v1 local Tai" in orchestrator_source
assert "if not pairing_row.paired" in orchestrator_source

automatic_editor = _method("_push_committed_pipe_thermal_basis_editor_v1")
automatic_calls = _calls(automatic_editor)
assert "_build_committed_pipe_external_convection_mapping_v1" in automatic_calls
assert "build_automatic_committed_pipe_thermal_basis_resolution_v1" in automatic_calls
automatic_source = ast.get_source_segment(source, automatic_editor) or ""
assert "external_convection_by_section_id=" in automatic_source
assert "automatic external h conv is resolved from N2D" in automatic_source
assert "automatic external h conv is blocked" in automatic_source

arrangement_authority = _method(
    "_resolve_committed_pipe_external_arrangement_authority_v1"
)
assert "build_committed_pipe_external_arrangement_runtime_handoff_v1" in _calls(
    arrangement_authority
)

print(
    "OK — H-S66-N2D1 live adapter orchestration into N2D/H-S66-J passed."
)
