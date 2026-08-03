# ======================================================================
# H-S64-F2 — Manual manufacturer candidate Accept/Clear controls
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_acceptance_intent_v1 import (
    BalancingPointManufacturerValveCandidateAcceptanceIntentV1,
    build_manufacturer_valve_candidate_comparison_fingerprint_v1,
)
from HVAC.hydronics.proportioning.balancing_point_manufacturer_valve_candidate_comparison_v1 import (
    MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
)


PANEL_PATH = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py")
ADAPTER_PATH = Path(
    "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
)
POINT_ID = "balancing-point:subleg:hs64f2"
CATALOG_ID = "manufacturer-products-v1"
REVISION = "2026-08-02"
VALVE_REF = "STANDARD-20"


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


def _load_method(source: str, method_name: str, namespace=None):
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
    target = dict(namespace or {})
    exec(compile(module, "<extracted-method>", "exec"), target)
    return target[method_name]


def _candidate(*, compatible: bool = True):
    return SimpleNamespace(
        valve_ref=VALVE_REF,
        manufacturer_name="Example Standard Manufacturer",
        product_family="Example balancing valves",
        model_name="Example Standard 20",
        valve_type_id="static_balancing_valve",
        nominal_dn=20,
        connection_type="threaded",
        cost_band_id="standard",
        approved_current_kv_m3_h=10.0,
        product_kvs_m3_h=10.0,
        kvs_basis_matches=compatible,
        required_kv=6.0,
        target_kv_bracketed=compatible,
        lower_setting_value=1.0,
        lower_setting_kv_m3_h=4.0,
        upper_setting_value=2.0,
        upper_setting_kv_m3_h=7.0,
        compatible=compatible,
        status="Compatible" if compatible else "Not compatible",
        evidence_notes=(),
    )


def _row(candidate=None):
    return SimpleNamespace(
        balancing_point_id=POINT_ID,
        ready=True,
        comparison_state_id=MANUFACTURER_VALVE_COMPARISON_AVAILABLE,
        comparison_available=True,
        approved_basis_catalog_id="generic-valves-v1",
        approved_basis_valve_ref="GENERIC-KVS-10",
        approved_current_kv_m3_h=10.0,
        required_kv=6.0,
        product_catalog_id=CATALOG_ID,
        product_catalog_revision=REVISION,
        candidates=(candidate or _candidate(),),
        blockers=(),
        status="Comparison available",
    )


def _comparison(row):
    return SimpleNamespace(
        ready=True,
        rows=(row,),
        blockers=(),
        status="Ready",
    )


def main() -> None:
    panel_source = PANEL_PATH.read_text(encoding="utf-8")
    adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")

    assert "read-only comparison / " in panel_source
    assert "manual acceptance" in panel_source
    assert '"Accepted"' in panel_source
    assert "Accept selected compatible candidate" in panel_source
    assert "Clear accepted candidate for selected point" in panel_source
    assert "does not choose a preset" in panel_source
    assert "rank a cost " in panel_source
    assert "band or alter hydraulics." in panel_source
    assert "QAbstractItemView.SelectRows" in panel_source
    assert "QAbstractItemView.SingleSelection" in panel_source
    add_section_source = _method_source(panel_source, "_add_section")
    assert "read-only comparison / " in add_section_source
    assert "manual acceptance" in add_section_source
    assert "): 1175," in add_section_source

    builder_name = (
        "_build_manufacturer_valve_candidate_comparison_gui_rows_v1"
    )
    builder = _load_method(adapter_source, builder_name)
    point = _row()
    comparison = _comparison(point)
    pending = SimpleNamespace(rows=(SimpleNamespace(
        balancing_point_id=POINT_ID,
        accepted=False,
        valve_ref="",
    ),))
    pending_rows = builder(comparison, pending)
    assert pending_rows[0]["accepted"] == "No"
    assert pending_rows[0]["compatible_bool"] is True
    assert pending_rows[0]["product_catalog_id"] == CATALOG_ID
    assert pending_rows[0]["product_catalog_revision"] == REVISION

    accepted = SimpleNamespace(rows=(SimpleNamespace(
        balancing_point_id=POINT_ID,
        accepted=True,
        valve_ref=VALVE_REF,
    ),))
    accepted_rows = builder(comparison, accepted)
    assert accepted_rows[0]["accepted"] == "Yes"
    assert accepted_rows[0]["accepted_bool"] is True
    assert accepted_rows[0]["point_has_acceptance"] is True

    stale = SimpleNamespace(rows=(SimpleNamespace(
        balancing_point_id=POINT_ID,
        accepted=False,
        valve_ref=VALVE_REF,
    ),))
    stale_rows = builder(comparison, stale)
    assert stale_rows[0]["accepted"] == "Stale"
    assert stale_rows[0]["accepted_bool"] is False
    assert stale_rows[0]["point_has_acceptance"] is True

    persisted_only = BalancingPointManufacturerValveCandidateAcceptanceIntentV1()
    persisted_only.accept_candidate(
        balancing_point_id=POINT_ID,
        product_catalog_id=CATALOG_ID,
        product_catalog_revision=REVISION,
        valve_ref=VALVE_REF,
        comparison_fingerprint="a" * 64,
    )
    unavailable_rows = builder(
        SimpleNamespace(rows=(), status="Catalogue unavailable", blockers=()),
        SimpleNamespace(rows=()),
        persisted_only,
    )
    assert unavailable_rows[0]["accepted"] == "Stale"
    assert unavailable_rows[0]["point_has_acceptance"] is True
    assert unavailable_rows[0]["compatible_bool"] is False

    setter = _load_method(
        adapter_source,
        "set_manufacturer_valve_candidate_acceptance_v1",
        {
            "BalancingPointManufacturerValveCandidateAcceptanceIntentV1": (
                BalancingPointManufacturerValveCandidateAcceptanceIntentV1
            ),
            "build_manufacturer_valve_candidate_comparison_fingerprint_v1": (
                build_manufacturer_valve_candidate_comparison_fingerprint_v1
            ),
        },
    )
    project = SimpleNamespace(
        hydronic_point_manufacturer_valve_candidate_acceptance_intent=None,
        hydronics_valid=True,
    )
    refreshes = []
    adapter_stub = SimpleNamespace(
        _project_state=project,
        _context=None,
        _balancing_point_manufacturer_valve_candidate_comparison_preview_v1=(
            comparison
        ),
        refresh=lambda: refreshes.append(True),
    )
    setter(adapter_stub, {
        "action": "accept",
        "balancing_point_id": POINT_ID,
        "product_catalog_id": CATALOG_ID,
        "product_catalog_revision": REVISION,
        "valve_ref": VALVE_REF,
    })
    intent = (
        project.hydronic_point_manufacturer_valve_candidate_acceptance_intent
    )
    assert intent is not None
    entry = intent.accepted_by_point_id[POINT_ID]
    assert entry.valve_ref == VALVE_REF
    assert len(entry.comparison_fingerprint) == 64
    assert project.hydronics_valid is False
    assert refreshes

    setter(adapter_stub, {
        "action": "clear",
        "balancing_point_id": POINT_ID,
    })
    assert POINT_ID not in intent.accepted_by_point_id

    incompatible = _candidate(compatible=False)
    adapter_stub._balancing_point_manufacturer_valve_candidate_comparison_preview_v1 = (
        _comparison(_row(incompatible))
    )
    try:
        setter(adapter_stub, {
            "action": "accept",
            "balancing_point_id": POINT_ID,
            "product_catalog_id": CATALOG_ID,
            "product_catalog_revision": REVISION,
            "valve_ref": VALVE_REF,
        })
    except ValueError as exc:
        assert "Only a compatible" in str(exc)
    else:
        raise AssertionError("Incompatible manufacturer candidate accepted")

    emitted = []
    actionable_row = accepted_rows[0]
    panel_stub = SimpleNamespace(
        _manufacturer_valve_candidate_acceptance_callback_v1=emitted.append,
        _selected_manufacturer_valve_candidate_row_v1=lambda: actionable_row,
    )
    accept_handler = _load_method(
        panel_source,
        "_on_accept_manufacturer_valve_candidate_v1",
    )
    clear_handler = _load_method(
        panel_source,
        "_on_clear_manufacturer_valve_candidate_v1",
    )
    accept_handler(panel_stub)
    clear_handler(panel_stub)
    assert emitted[0] == {
        "action": "accept",
        "balancing_point_id": POINT_ID,
        "product_catalog_id": CATALOG_ID,
        "product_catalog_revision": REVISION,
        "valve_ref": VALVE_REF,
    }
    assert emitted[1] == {
        "action": "clear",
        "balancing_point_id": POINT_ID,
    }

    setter_source = _method_source(
        adapter_source,
        "set_manufacturer_valve_candidate_acceptance_v1",
    )
    assert "ProjectState(" not in setter_source
    assert "compatible" in setter_source
    assert "comparison_fingerprint" in setter_source
    assert "preset" in setter_source
    assert "hydraulics" in setter_source
    refresh_source = _method_source(
        adapter_source,
        "_refresh_effective_return_arrangement_basis_rows",
    )
    assert (
        "resolve_balancing_point_manufacturer_valve_candidate_acceptance_v1("
        in refresh_source
    )
    assert "set_manufacturer_valve_candidate_acceptance_callback_v1" in (
        adapter_source
    )

    print(
        "OK — H-S64-F2 compatible manufacturer candidate manual "
        "Accept/Clear controls passed."
    )


if __name__ == "__main__":
    main()
