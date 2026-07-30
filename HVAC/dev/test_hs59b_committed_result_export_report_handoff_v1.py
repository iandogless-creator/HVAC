# ======================================================================
# H-S59-B — Committed result export/report handoff test
# ======================================================================

from __future__ import annotations

from dataclasses import replace
import inspect
import json
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_export_payload_v1 import (
    build_committed_proportioned_system_export_payload_v1,
    committed_proportioned_system_export_payload_to_dict_v1,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_result_package_v1 import (
    CommittedProportionedSystemResultPackageV1,
)


def _package():
    return CommittedProportionedSystemResultPackageV1(
        ready=True,
        source_snapshot_schema="proportioned_basis_snapshot_v1",
        accepted_return_arrangement_basis="DIRECT_RETURN",
        route_result=SimpleNamespace(
            rows=(
                SimpleNamespace(
                    route_id="route-a",
                    route_label="Route A",
                    proportioned_pressure_drop_Pa=40_000.0,
                    ready=True,
                ),
            ),
        ),
        point_reconciliation=SimpleNamespace(
            point_rows=(
                SimpleNamespace(
                    balancing_point_id="point-a",
                    allocated_added_pressure_drop_Pa=1_000.0,
                    accepted_kvs_basis=6.3,
                    reconciled=True,
                ),
            ),
            route_rows=(
                SimpleNamespace(
                    committed_route_id="route-a",
                    reconciled=True,
                ),
            ),
        ),
        section_result=SimpleNamespace(
            rows=(
                SimpleNamespace(
                    committed_route_id="route-a",
                    section_id="section-a",
                    pipe_size_label="15 mm",
                    carried_flow_kg_s=0.1,
                ),
            ),
        ),
        completion_status=SimpleNamespace(
            ready=True,
            status="Ready",
            controlling_target_pressure_drop_Pa=40_000.0,
            route_count=1,
            routes_at_target_count=1,
            balancing_point_count=1,
            reconciled_balancing_point_count=1,
            valve_duty_point_count=1,
            unique_section_count=1,
            route_addressable_section_count=1,
        ),
        route_count=1,
        balancing_point_count=1,
        unique_section_count=1,
        route_addressable_section_count=1,
        status="Ready",
    )


def main() -> None:
    package = _package()
    before = repr(package)
    payload = build_committed_proportioned_system_export_payload_v1(
        package
    )

    assert payload.ready is True, payload.status
    assert payload.blockers == ()
    assert payload.source_package_schema == package.schema
    assert payload.accepted_return_arrangement_basis == "DIRECT_RETURN"
    assert payload.summary is not None
    assert payload.summary["route_count"] == 1
    assert payload.summary["balancing_point_count"] == 1
    assert payload.summary["unique_section_count"] == 1
    assert payload.summary["valve_duty_point_count"] == 1
    assert len(payload.committed_route_results) == 1
    assert len(payload.committed_balancing_point_results) == 1
    assert len(payload.committed_route_point_reconciliation) == 1
    assert len(payload.committed_section_results) == 1
    assert payload.committed_route_results[0]["route_id"] == "route-a"
    assert (
        payload.committed_balancing_point_results[0][
            "balancing_point_id"
        ]
        == "point-a"
    )
    assert payload.committed_section_results[0]["section_id"] == "section-a"
    assert "No PDF or CSV file written" in payload.exclusions
    assert "No ProjectState mutation" in " | ".join(payload.exclusions)
    assert repr(package) == before
    assert (
        build_committed_proportioned_system_export_payload_v1(package)
        == payload
    )

    payload_dict = (
        committed_proportioned_system_export_payload_to_dict_v1(payload)
    )
    assert payload_dict is not None
    assert payload_dict["schema"] == (
        "committed_proportioned_system_export_payload_v1"
    )
    json.dumps(payload_dict)

    blocked = build_committed_proportioned_system_export_payload_v1(
        replace(
            package,
            ready=False,
            status="Blocked",
            blockers=("package incomplete",),
        )
    )
    assert blocked.ready is False
    assert "H-S59-A: package incomplete" in blocked.blockers
    assert blocked.committed_route_results == ()

    mismatched = build_committed_proportioned_system_export_payload_v1(
        replace(package, route_count=2)
    )
    assert mismatched.ready is False
    assert "route count must match" in mismatched.status

    absent = build_committed_proportioned_system_export_payload_v1(None)
    assert absent.ready is False
    assert "H-S59-A committed" in absent.status

    source = inspect.getsource(HydronicsSchematicPanelAdapter)
    assert "build_committed_proportioned_system_result_package_v1" in source
    assert "build_committed_proportioned_system_export_payload_v1" in source
    assert "_committed_proportioned_system_result_package_v1" in source
    assert "_committed_proportioned_system_export_payload_v1" in source
    assert "_basis_only_proportioned_export_payload_preview" in source

    print(
        "OK — H-S59-B committed result export/report handoff passed."
    )


if __name__ == "__main__":
    main()
