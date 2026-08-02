# ======================================================================
# H-S64-E1 — Session manufacturer catalogue Open/Clear controls
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path


PANEL_PATH = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py")
ADAPTER_PATH = Path(
    "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
)


def _method_source(source: str, method_name: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == method_name:
                lines = source.splitlines(keepends=True)
                return "".join(lines[node.lineno - 1:node.end_lineno])
    raise AssertionError(f"Method not found: {method_name}")


def main() -> None:
    panel_source = PANEL_PATH.read_text(encoding="utf-8")
    adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")

    assert "Local manufacturer valve catalogue — session-only" in panel_source
    assert "Open manufacturer catalogue…" in panel_source
    assert "Clear catalogue" in panel_source
    assert '"project and no valve is selected."' in panel_source
    assert '"catalogue for this session. The path is not saved with the "' in (
        panel_source
    )
    assert "no valve is selected" in panel_source

    open_source = _method_source(
        panel_source,
        "_on_open_local_manufacturer_catalogue_v1",
    )
    assert "QFileDialog.getOpenFileName(" in open_source
    assert '"JSON files (*.json);;All files (*)"' in open_source
    assert "callback(source_path)" in open_source
    assert "json.load" not in open_source.lower()
    assert "read_text(" not in open_source
    assert "ProjectState" not in open_source
    assert "mark_dirty" not in open_source

    clear_source = _method_source(
        panel_source,
        "_on_clear_local_manufacturer_catalogue_v1",
    )
    assert "callback(None)" in clear_source
    assert "ProjectState" not in clear_source
    assert "mark_dirty" not in clear_source

    status_source = _method_source(
        panel_source,
        "set_local_manufacturer_catalogue_status_v1",
    )
    for evidence_name in (
        "source_path",
        "catalog_id",
        "catalog_revision",
        "product_count",
        "status",
        "blockers",
    ):
        assert evidence_name in status_source
    assert "clear_button.setEnabled(bool(source_supplied))" in status_source
    assert "label.setText(" in status_source
    assert "ProjectState" not in status_source

    init_source = _method_source(adapter_source, "__init__")
    assert "set_local_manufacturer_catalogue_path_callback_v1(" in init_source
    assert (
        "self.supply_local_manufacturer_valve_product_detail_catalogue_path_v1"
        in init_source
    )

    supply_source = _method_source(
        adapter_source,
        "supply_local_manufacturer_valve_product_detail_catalogue_path_v1",
    )
    assert "self._push_local_manufacturer_catalogue_status_v1()" in (
        supply_source
    )
    assert "self.refresh()" in supply_source
    assert "return runtime" in supply_source
    assert "self._project_state" not in supply_source
    assert "mark_dirty" not in supply_source

    status_push_source = _method_source(
        adapter_source,
        "_push_local_manufacturer_catalogue_status_v1",
    )
    assert '"set_local_manufacturer_catalogue_status_v1"' in (
        status_push_source
    )
    for runtime_field in (
        '"ready"',
        '"source_supplied"',
        '"source_path"',
        '"catalog_id"',
        '"catalog_revision"',
        '"product_count"',
        '"status"',
        '"blockers"',
    ):
        assert runtime_field in status_push_source

    assert "manufacturer valve candidate comparison" not in panel_source.lower()
    assert "load_local_manufacturer" not in panel_source

    print(
        "OK — H-S64-E1 session manufacturer catalogue Open/Clear controls "
        "and load status passed."
    )


if __name__ == "__main__":
    main()
