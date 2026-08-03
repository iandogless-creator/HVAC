# ======================================================================
# H-S65-A — Proportioning workspace mini-tab layout
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path


PANEL_PATH = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py")


def _method_node(source: str, method_name: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    raise AssertionError(f"Method not found: {method_name}")


def _method_source(source: str, method_name: str) -> str:
    node = _method_node(source, method_name)
    lines = source.splitlines(keepends=True)
    return "".join(lines[node.lineno - 1:node.end_lineno])


def _load_router(source: str):
    node = _method_node(
        source,
        "_proportioning_workspace_key_for_title_v1",
    )
    copied = ast.FunctionDef(
        name=node.name,
        args=node.args,
        body=node.body,
        decorator_list=[],
        returns=node.returns,
        type_comment=node.type_comment,
        type_params=getattr(node, "type_params", []),
    )
    module = ast.fix_missing_locations(ast.Module(body=[copied], type_ignores=[]))
    namespace: dict[str, object] = {}
    exec(compile(module, "<hs65a-router>", "exec"), namespace)
    return namespace[node.name]


def main() -> None:
    source = PANEL_PATH.read_text(encoding="utf-8")

    for label in (
        "Balancing & Authority",
        "Kvs Design",
        "Product Search",
        "Manufacturer Valves",
    ):
        assert source.count(f'"{label}"') == 1

    assert "_proportioning_workspace_tabs_v1 = QTabWidget(" in source
    assert "setDocumentMode(True)" in source
    assert "setWidgetResizable(True)" in _method_source(
        source,
        "_make_proportioning_workspace_tab_v1",
    )

    router = _load_router(source)
    assert router(None, "Return arrangement acceptance — user design basis") == (
        "balancing_authority"
    )
    assert router(None, "Manual point Kvs candidate acceptance — design intent") == (
        "kvs_design"
    )
    assert router(
        None,
        "Approved point valve product-search duty envelopes — read-only",
    ) == "product_search"
    assert router(
        None,
        "Valve catalogue candidate-match evidence — read-only",
    ) == "product_search"
    assert router(
        None,
        "Local manufacturer valve catalogue — session-only",
    ) == "manufacturer_valves"
    assert router(
        None,
        "Manufacturer valve candidates — premium / standard / budget labels",
    ) == "manufacturer_valves"

    add_section = _method_source(source, "_add_section")
    assert "_proportioning_workspace_key_for_title_v1(" in add_section
    assert '"hydraulic_section_title_v1"' in add_section
    assert '"hydraulic_dependency_order_v1"' in add_section
    assert "): 1175," in add_section
    assert "ProjectState" not in add_section
    assert "callback(" not in add_section

    print(
        "OK — H-S65-A Proportioning workspace mini-tab presentation "
        "layout passed."
    )


if __name__ == "__main__":
    main()
