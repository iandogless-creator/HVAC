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
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {function_name}")


def main() -> None:
    panel = _source(PANEL_PATH)
    adapter = _source(ADAPTER_PATH)

    # H-S66-I belongs beside H-S66-H in the Bare Pipe Heat Loss mini-tab.
    assert "Committed-section thermal-condition basis — manual intent" in panel
    assert "Apply basis to selected section" in panel
    assert "Clear selected section basis" in panel
    assert "Clear all section bases" in panel
    for label in (
        "Surface temperature:",
        "Ambient air:",
        "Mean radiant:",
        "Emissivity:",
        "External h conv:",
    ):
        assert label in panel

    # The panel collects literal user text and delegates validation/persistence.
    payload = _function_source(
        PANEL_PATH,
        "_committed_pipe_thermal_basis_payload_v1",
    )
    for key in (
        '"section_id"',
        '"surface_temperature_C"',
        '"ambient_air_temperature_C"',
        '"mean_radiant_temperature_C"',
        '"emissivity"',
        '"external_convection_coefficient_W_m2K"',
    ):
        assert key in payload
    assert "ProjectState" not in payload
    assert "build_explicit_bare_pipe_thermal_condition_basis_v1" not in payload

    # Adapter is the sole callback boundary and reuses H-S66-C/F authority.
    handler = _function_source(
        ADAPTER_PATH,
        "set_committed_pipe_thermal_basis_v1",
    )
    assert "build_committed_pipe_schedule_thermal_fingerprint_v1" in handler
    assert "build_explicit_bare_pipe_thermal_condition_basis_v1" in handler
    assert ".set_section_basis(" in handler
    assert ".clear_section_basis(" in handler
    assert ".clear_all(" in handler
    assert "project.mark_dirty()" in handler
    assert "self.refresh()" in handler
    assert "hydronics_valid" not in handler

    # The editor is restored before H-S66-G is rebuilt, so Apply/Clear produces
    # immediate read-only evidence while a stale intent remains fail-closed.
    refresh = _function_source(
        ADAPTER_PATH,
        "_refresh_committed_pipe_bare_heat_loss_v1",
    )
    editor_call = refresh.index("_push_committed_pipe_thermal_basis_editor_v1")
    handoff_call = refresh.index(
        "build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1"
    )
    assert editor_call < handoff_call

    restore = _function_source(
        ADAPTER_PATH,
        "_push_committed_pipe_thermal_basis_editor_v1",
    )
    assert "stored_fingerprint != fingerprint" in restore
    assert "clear all section " in restore
    assert '"bases before recording' in restore
    assert '"has_basis"' in restore

    # No hidden thermal assumptions are populated into the editor.
    editor_init = panel[
        panel.index("# H-S66-I"):
        panel.index("self._committed_pipe_bare_heat_loss_status_label_v1")
    ]
    assert ".setText(" not in editor_init
    assert "20.0" not in editor_init
    assert "50.0" not in editor_init
    assert "0.9" not in editor_init

    print(
        "OK — H-S66-I manual committed-section thermal-condition basis "
        "editor passed."
    )


if __name__ == "__main__":
    main()
