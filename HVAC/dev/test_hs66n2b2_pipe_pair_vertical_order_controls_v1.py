# ======================================================================
# H-S66-N2B2 — Project/local committed pipe-pair vertical-order controls
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

    # The visible choice is deliberate and defaults to Not set.
    assert "Stacked pipe vertical order — project and local intent" in panel
    for text in (
        "Not set",
        "Flow above return",
        "Return above flow",
        "Apply project-wide order",
        "Apply local order override",
        "Clear selected order override",
        "Clear all order overrides",
    ):
        assert text in panel
    assert "Separate RR pipework " in panel
    assert '"keeps vertical order dormant."' in panel

    # The panel emits intent only; it owns no ProjectState or physics.
    project_apply = _function_source(
        PANEL_PATH,
        "_on_apply_committed_pipe_pair_project_vertical_order_v1",
    )
    assert '"action": "set_project"' in project_apply
    assert '"upper_pipe_role"' in project_apply
    local_apply = _function_source(
        PANEL_PATH,
        "_on_apply_committed_pipe_pair_local_vertical_order_v1",
    )
    assert '"section_id"' in local_apply
    assert '"upper_pipe_role"' in local_apply
    for source in (project_apply, local_apply):
        assert "ProjectState" not in source
        assert "resolve_effective" not in source
        assert "natural_convection" not in source

    controls = _function_source(
        PANEL_PATH,
        "_refresh_committed_pipe_pair_vertical_order_controls_v1",
    )
    assert 'row.get("stacked")' in controls
    assert "not stale" in controls
    assert 'row.get("has_override")' in controls

    # Adapter persistence delegates exact-section validation to N2B1.
    handler = _function_source(
        ADAPTER_PATH,
        "set_committed_pipe_pair_vertical_order_intent_v1",
    )
    assert ".set_project_upper_pipe_role(" in handler
    assert (
        "set_current_committed_section_pipe_pair_vertical_order_override_v1"
        in handler
    )
    assert ".clear_section_override(" in handler
    assert ".clear_all_section_overrides()" in handler
    assert "project.mark_dirty()" in handler
    assert "self.refresh()" in handler
    assert "natural_convection" not in handler

    # Rows resolve local-over-project intent and preserve stale fail-closedness.
    restore = _function_source(
        ADAPTER_PATH,
        "_push_committed_pipe_pair_vertical_order_editor_v1",
    )
    assert "build_committed_pipe_pair_vertical_order_fingerprint_v1" in restore
    assert "resolve_effective_committed_pipe_pair_vertical_order_v1" in restore
    assert "SEPARATE_PIPE_V1" in restore
    assert '"project_upper_pipe_role"' in restore
    assert '"local_upper_pipe_role"' in restore
    assert '"has_override"' in restore
    assert "clear all order overrides" in restore
    assert "natural_convection" not in restore
    assert "Churchill" not in restore

    refresh = _function_source(
        ADAPTER_PATH,
        "_refresh_committed_pipe_bare_heat_loss_v1",
    )
    assert "_push_committed_pipe_pair_vertical_order_editor_v1" in refresh

    print(
        "OK — H-S66-N2B2 project-wide and exact committed-section "
        "stacked-pair vertical-order controls passed."
    )


if __name__ == "__main__":
    main()
