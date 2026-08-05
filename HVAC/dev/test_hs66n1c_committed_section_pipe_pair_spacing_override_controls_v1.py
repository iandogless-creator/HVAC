# ======================================================================
# H-S66-N1C — Manual committed-section support/c/c override controls
# ======================================================================

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


def main() -> None:
    panel = _source(PANEL_PATH)
    adapter = _source(ADAPTER_PATH)

    # N1C is one local-over-Environment editor in Bare Pipe Heat Loss.
    assert "Committed-section stacked pipe support and spacing " in panel
    assert "— local overrides" in panel
    for text in (
        "Apply local support/c/c override",
        "Clear selected local override",
        "Clear all local spacing overrides",
    ):
        assert text in panel
    assert "Separate RR pipework ignores " in panel
    assert '"these controls."' in panel
    for support_type in (
        "moulded_plastic_double_clip",
        "paired_individual_plastic_clips",
        "double_munsen_ring",
    ):
        assert support_type in panel

    # The panel remains presentation-only and emits an exact local intent.
    apply_handler = _function_source(
        PANEL_PATH,
        "_on_apply_committed_pipe_pair_spacing_override_v1",
    )
    for key in (
        '"section_id"',
        '"support_type"',
        '"centre_spacing_mm"',
    ):
        assert key in apply_handler
    assert "ProjectState" not in apply_handler
    assert "resolve_effective" not in apply_handler
    assert "external_convection" not in apply_handler

    controls = _function_source(
        PANEL_PATH,
        "_refresh_committed_pipe_pair_spacing_controls_v1",
    )
    assert 'row.get("stacked")' in controls
    assert "not stale" in controls
    assert 'row.get("has_override")' in controls

    # Adapter alone owns persistence and delegates validation to N1B.
    handler = _function_source(
        ADAPTER_PATH,
        "set_committed_pipe_pair_spacing_override_v1",
    )
    assert (
        "set_current_committed_section_pipe_pair_spacing_override_v1"
        in handler
    )
    assert ".clear_section_override(" in handler
    assert ".clear_all()" in handler
    assert "project.mark_dirty()" in handler
    assert "self.refresh()" in handler
    assert "external_convection" not in handler

    # Rows are driven by exact H-S66-M arrangements and N1B effective evidence.
    restore = _function_source(
        ADAPTER_PATH,
        "_push_committed_pipe_pair_spacing_editor_v1",
    )
    assert "build_committed_pipe_pair_spacing_fingerprint_v1" in restore
    assert "resolve_effective_committed_pipe_pair_spacing_v1" in restore
    assert "SEPARATE_PIPE_V1" in restore
    assert '"stacked"' in restore
    assert '"actual_outside_diameter_mm"' in restore
    assert '"has_override"' in restore
    assert "clear all local spacing overrides" in restore
    assert "external_convection" not in restore

    context = _function_source(
        ADAPTER_PATH,
        "_resolve_committed_pipe_pair_spacing_context_v1",
    )
    assert "build_circuit_return_path_comparison_v1" in context
    assert (
        "build_committed_pipe_external_arrangement_runtime_handoff_v1"
        in context
    )
    assert "bare_pipe_pair_spacing_defaults_by_nominal_od_mm" in context

    refresh = _function_source(
        ADAPTER_PATH,
        "_refresh_committed_pipe_bare_heat_loss_v1",
    )
    assert "_push_committed_pipe_pair_spacing_editor_v1" in refresh

    print(
        "OK — H-S66-N1C manual exact committed-section stacked-pair "
        "support/c/c override controls passed."
    )


if __name__ == "__main__":
    main()
