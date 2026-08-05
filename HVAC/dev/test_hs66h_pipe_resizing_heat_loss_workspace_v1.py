# ======================================================================
# H-S66-H — Pipe Resizing mini-tabs and read-only heat-loss table
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
    module = ast.fix_missing_locations(
        ast.Module(body=[copied], type_ignores=[])
    )
    namespace: dict[str, object] = {}
    exec(compile(module, "<hs66h-method>", "exec"), namespace)
    return namespace[method_name]


def main() -> None:
    panel_source = PANEL_PATH.read_text(encoding="utf-8")
    adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")

    assert panel_source.count('"Schedule && Commit"') == 1
    assert panel_source.count('"Bare Pipe Heat Loss"') == 1
    assert "_pipe_resizing_workspace_tabs_v1 = QTabWidget(" in panel_source
    assert "setDocumentMode(True)" in panel_source
    assert "Committed section bare-pipe heat loss — read-only" in panel_source
    for heading in (
        "Pipe / OD",
        "Convection W/m",
        "Radiation W/m",
        "Total W/m",
        "Total W",
    ):
        assert f'"{heading}"' in panel_source

    maker = _method_source(
        panel_source,
        "_make_pipe_resizing_workspace_tab_v1",
    )
    assert "setWidgetResizable(True)" in maker

    setter = _method_source(
        panel_source,
        "set_committed_pipe_bare_heat_loss_rows_v1",
    )
    assert "QTableWidgetItem" not in setter
    assert "_set_resized_pipe_review_rows_v1(" in setter
    assert "ProjectState" not in setter
    assert "callback" not in setter

    builder_name = "_build_committed_pipe_bare_heat_loss_rows_v1"
    builder_source = _method_source(adapter_source, builder_name)
    assert "heat_loss_W_per_m" in builder_source
    assert "pipe_radiation_engine" not in builder_source
    assert "build_bare_pipe" not in builder_source
    builder = _load_method(adapter_source, builder_name)

    section = SimpleNamespace(
        section_id="section-001",
        section_scope="route-exclusive",
        route_ids=("route-a",),
        material_label="Steel Medium",
        pipe_size_label="DN20",
        actual_outside_diameter_mm=26.9,
        length_m=5.5,
        surface_temperature_C=60.0,
        ambient_air_temperature_C=20.0,
        mean_radiant_temperature_C=18.0,
        emissivity=0.95,
        external_convection_coefficient_W_m2K=5.0,
        convection_heat_loss_W_per_m=16.9,
        radiation_heat_loss_W_per_m=18.4,
        total_heat_loss_W_per_m=35.3,
        total_heat_loss_W=194.15,
        status="Bare-pipe section heat loss calculated",
    )
    handoff = SimpleNamespace(
        ready=True,
        evidence=SimpleNamespace(sections=(section,)),
    )
    rows = builder(None, handoff)
    assert len(rows) == 1
    row = rows[0]
    assert row["section"] == "section-001"
    assert row["pipe_od"] == "Steel Medium | DN20 | OD 26.9 mm"
    assert row["length"] == "5.50 m"
    assert row["emissivity"] == "0.950"
    assert row["convection_per_m"] == "16.90 W/m"
    assert row["radiation_per_m"] == "18.40 W/m"
    assert row["total_per_m"] == "35.30 W/m"
    assert row["total"] == "194.2 W"
    assert builder(None, SimpleNamespace(ready=False, evidence=None)) == []

    refresh = _method_source(
        adapter_source,
        "_refresh_committed_pipe_bare_heat_loss_v1",
    )
    assert (
        "build_committed_pipe_section_bare_heat_loss_runtime_handoff_v1("
        in refresh
    )
    assert (
        "hydronic_committed_pipe_section_thermal_condition_basis_intent"
        in refresh
    )
    assert "set_committed_pipe_bare_heat_loss_state_v1(" in refresh
    assert "set_committed_pipe_bare_heat_loss_rows_v1(" in refresh
    assert "ProjectState" not in refresh

    print(
        "OK — H-S66-H Pipe Resizing mini-tabs and read-only committed "
        "bare-pipe heat-loss table passed."
    )


if __name__ == "__main__":
    main()
