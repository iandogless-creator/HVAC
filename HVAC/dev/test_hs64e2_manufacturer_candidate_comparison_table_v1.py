# ======================================================================
# H-S64-E2 — Read-only manufacturer candidate comparison table
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


PANEL_PATH = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py")
ADAPTER_PATH = Path(
    "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
)


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


def _load_method(source: str, method_name: str):
    node = _method_node(source, method_name)
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
    exec(compile(module, "<extracted-adapter-method>", "exec"), namespace)
    return namespace[method_name]


def _candidate(cost_band: str, valve_ref: str, lower: float, upper: float):
    return SimpleNamespace(
        cost_band_id=cost_band,
        manufacturer_name=f"Example {cost_band.title()} Manufacturer",
        product_family="Example balancing valves",
        model_name=f"Example {valve_ref}",
        valve_ref=valve_ref,
        valve_type_id="static_balancing_valve",
        nominal_dn=20,
        connection_type="threaded",
        approved_current_kv_m3_h=10.0,
        product_kvs_m3_h=10.0,
        kvs_basis_matches=True,
        required_kv=6.0,
        lower_setting_value=1.0,
        lower_setting_kv_m3_h=lower,
        upper_setting_value=2.0,
        upper_setting_kv_m3_h=upper,
        target_kv_bracketed=True,
        compatible=True,
        status="Compatible manufacturer candidate comparison evidence",
        evidence_notes=(
            "Approved current Kv basis matched and required Kv bracketed",
        ),
    )


def main() -> None:
    panel_source = PANEL_PATH.read_text(encoding="utf-8")
    adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")

    assert (
        "Manufacturer valve candidates — premium / standard / "
        in panel_source
    )
    assert "budget labels, no ranking — read-only" in panel_source
    assert '"Cost band"' in panel_source
    assert '"Approved Kv"' in panel_source
    assert '"Product Kvs"' in panel_source
    assert '"Lower preset"' in panel_source
    assert '"Upper preset"' in panel_source
    assert '"Compatible"' in panel_source
    assert "setAlternatingRowColors(" in panel_source

    panel_setter = _method_source(
        panel_source,
        "set_manufacturer_valve_candidate_comparison_rows_v1",
    )
    assert "QTableWidgetItem(" in panel_setter
    assert "Qt.ItemIsEditable" in panel_setter
    assert "callback" not in panel_setter
    assert "ProjectState" not in panel_setter
    assert "setCurrent" not in panel_setter

    builder_name = (
        "_build_manufacturer_valve_candidate_comparison_gui_rows_v1"
    )
    builder_source = _method_source(adapter_source, builder_name)
    assert "never rank products" in builder_source
    assert "sorted(" not in builder_source
    assert "ProjectState" not in builder_source
    builder = _load_method(adapter_source, builder_name)

    point = SimpleNamespace(
        balancing_point_id="balancing-point:test",
        approved_current_kv_m3_h=10.0,
        required_kv=6.0,
        candidates=(
            _candidate("standard", "STANDARD-20", 4.0, 7.0),
            _candidate("budget", "BUDGET-20", 2.0, 8.0),
            _candidate("premium", "PREMIUM-20", 3.0, 6.0),
        ),
        status="Manufacturer comparison available",
        blockers=(),
    )
    comparison = SimpleNamespace(
        ready=True,
        rows=(point,),
        status="Ready — supplied order retained",
        blockers=(),
    )
    rows = builder(comparison)
    assert [row["cost_band"] for row in rows] == [
        "Standard",
        "Budget",
        "Premium",
    ]
    assert [row["valve_ref"] for row in rows] == [
        "STANDARD-20",
        "BUDGET-20",
        "PREMIUM-20",
    ]
    assert all(row["nominal_dn"] == "DN20" for row in rows)
    assert all(row["approved_kv"] == "10.000" for row in rows)
    assert all(row["product_kvs"] == "10.000" for row in rows)
    assert all(row["required_kv"] == "6.000" for row in rows)
    assert all(row["kvs_match"] == "Yes" for row in rows)
    assert all(row["bracketed"] == "Yes" for row in rows)
    assert all(row["compatible"] == "Yes" for row in rows)
    assert rows[0]["lower_preset"] == "1.000 / Kv 4.000"
    assert rows[0]["upper_preset"] == "2.000 / Kv 7.000"

    blocked = builder(SimpleNamespace(
        ready=False,
        rows=(),
        status="Blocked — explicit local catalogue required",
        blockers=("Explicit local catalogue required",),
    ))
    assert len(blocked) == 1
    assert blocked[0]["status"].startswith("Blocked —")
    assert blocked[0]["evidence_notes"] == (
        "Explicit local catalogue required"
    )

    refresh_source = _method_source(
        adapter_source,
        "_refresh_effective_return_arrangement_basis_rows",
    )
    build_index = refresh_source.index(
        "build_balancing_point_manufacturer_valve_candidate_comparison_v1("
    )
    push_index = refresh_source.index(
        "set_manufacturer_valve_candidate_comparison_rows_v1("
    )
    assert build_index < push_index
    assert builder_name + "(" in refresh_source[push_index:push_index + 500]

    print(
        "OK — H-S64-E2 read-only premium/standard/budget manufacturer "
        "candidate comparison table passed."
    )


if __name__ == "__main__":
    main()
