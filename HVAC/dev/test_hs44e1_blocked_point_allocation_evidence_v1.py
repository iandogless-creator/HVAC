from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


def main() -> None:
    adapter = object.__new__(HydronicsSchematicPanelAdapter)
    allocation = SimpleNamespace(
        ready=False,
        status="H-S44-B allocation blocked — route burden not conserved",
        blockers=(
            "leg-001-primary-subleg: unallocated residual 1968.300 Pa",
        ),
        rows=(
            SimpleNamespace(
                balancing_point_id="balancing-point:subleg:leg-001-primary-subleg",
                point_scope="subleg",
                point_role="common",
                label="Heating Leg 1 / Subleg 1A entry",
                downstream_route_ids=(
                    "leg-001-primary-subleg",
                    "leg-001-subleg-b",
                ),
                is_shared=True,
                is_route_exclusive=False,
                point_flow_kg_s=0.1699,
                allocated_added_dp_pa=0.0,
                allocated_resistance_pa_per_kg_s2=0.0,
                status="No residual burden allocated at this point",
            ),
        ),
        route_conservation=(
            SimpleNamespace(
                route_id="leg-001-primary-subleg",
                difference_pa=1968.3,
                conserved=False,
            ),
            SimpleNamespace(
                route_id="leg-001-subleg-b",
                difference_pa=0.0,
                conserved=True,
            ),
        ),
    )

    rows = adapter._build_blocked_balancing_point_allocation_gui_rows_v1(
        allocation
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["topology"] == "Shared"
    assert row["point_flow"] == "0.16990 kg/s"
    assert row["allocated_dp"] == "0.0 Pa"
    assert row["method"] == "Unavailable — allocation not conserved"
    assert row["valve_duty"] == "Unavailable — allocation not conserved"
    assert row["ready"] == "No"
    assert "unallocated residual 1968.3 Pa" in row["blockers"]
    assert "H-S44-C/D blocked" in row["status"]

    source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "point_display_rows" in source
    assert "_build_blocked_balancing_point_allocation_gui_rows_v1" in source
    assert "point_display_rows and" not in source

    print(
        "OK — H-S44-E1 blocked point allocations and conservation "
        "evidence remain visible in the GUI."
    )


if __name__ == "__main__":
    main()
