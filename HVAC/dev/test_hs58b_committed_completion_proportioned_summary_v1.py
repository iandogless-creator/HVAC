# ======================================================================
# H-S58-B — Committed completion status in clean Proportioned summary
# ======================================================================

from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_completion_status_v1 import (
    CommittedProportionedSystemCompletionStatusV1,
)


def _completion(*, ready=True, status=None):
    return CommittedProportionedSystemCompletionStatusV1(
        ready=ready,
        accepted_return_arrangement_basis="DIRECT_RETURN",
        controlling_target_pressure_drop_Pa=38_736.2,
        route_count=4,
        routes_at_target_count=4,
        balancing_point_count=3,
        reconciled_balancing_point_count=3,
        valve_duty_point_count=3,
        unique_section_count=24,
        route_addressable_section_count=30,
        status=(
            status
            or (
                "Ready — committed Proportioned-system completion "
                "status available"
            )
        ),
        blockers=() if ready else ("committed evidence incomplete",),
    )


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._committed_proportioned_system_completion_status_v1 = (
        _completion()
    )
    adapter._build_preview_proportioned_output_status_rows_v1 = (
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError(
                "committed summary must not read preview status rows"
            )
        )
    )

    rows = adapter._build_proportioned_output_status_rows_v1(
        resolution=None,
        chosen_preview_rows=(),
        chosen_controlling_rows=(),
        readiness_rows=(),
    )
    assert [row["item"] for row in rows] == [
        "Accepted return basis",
        "Proportioned-system status",
        "Route reconciliation",
        "Point reconciliation",
        "Section evidence",
        "Design boundary",
    ]
    assert rows[0]["status"] == (
        "Committed proportioning basis: F&R (DIRECT_RETURN)"
    )
    assert rows[1]["status"].startswith("Ready — committed")
    assert rows[2]["status"] == (
        "4 of 4 committed routes reach the 38736.2 Pa controlling target"
    )
    assert rows[3]["status"] == (
        "3 of 3 committed balancing points reconcile; "
        "3 require valve duty"
    )
    assert rows[4]["status"] == (
        "24 unique committed sections across "
        "30 route-addressable rows"
    )
    assert "No pump" in rows[5]["status"]
    assert "valve product" in rows[5]["status"]
    assert "commissioning/final balancing" in rows[5]["status"]
    for row in rows:
        assert "preview only" not in row["status"].lower()
        assert "basis only" not in row["status"].lower()

    adapter._committed_proportioned_system_completion_status_v1 = (
        _completion(
            ready=False,
            status="Blocked — committed evidence incomplete",
        )
    )
    blocked = adapter._build_proportioned_output_status_rows_v1(
        resolution=None,
        chosen_preview_rows=(),
        chosen_controlling_rows=(),
        readiness_rows=(),
    )
    assert blocked[1]["status"].startswith("Blocked")

    adapter._committed_proportioned_system_completion_status_v1 = None
    adapter._committed_basis_route_proportioning_result_v1 = None
    preview = [
        {
            "item": "Route pressure evidence",
            "status": "Chosen-basis route Δp evidence available — preview only",
        }
    ]
    adapter._build_preview_proportioned_output_status_rows_v1 = (
        lambda **kwargs: preview
    )
    assert adapter._build_proportioned_output_status_rows_v1(
        resolution=None,
        chosen_preview_rows=(),
        chosen_controlling_rows=(),
        readiness_rows=(),
    ) == preview

    source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert (
        "build_committed_proportioned_system_completion_status_v1("
        in source
    )
    assert (
        "_committed_proportioned_system_completion_status_v1"
        in source
    )
    assert (
        "_build_committed_proportioned_completion_status_rows_v1"
        in source
    )

    print(
        "OK — H-S58-B committed completion Proportioned summary passed."
    )


if __name__ == "__main__":
    main()
