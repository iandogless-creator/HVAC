# ======================================================================
# H-S55-B — Committed route result in the Proportioned UI
# ======================================================================

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
)


def _route(route_id, label, chosen, added, controlling=False):
    return CommittedProportioningHydraulicRouteV1(
        route_id=route_id,
        route_label=label,
        basis="F&R",
        chosen_pressure_drop_Pa=chosen,
        controlling=controlling,
        required_added_pressure_drop_Pa=added,
        preliminary_resistance_Pa_per_kg_s2=1.0,
        common_main_pressure_drop_Pa=None,
        leg_entry_pressure_drop_Pa=None,
        physical_main_entry_pressure_drop_Pa=None,
    )


def main() -> None:
    authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True,
        routes=(
            _route(
                "route-one",
                "Leg 1B Branch subleg",
                38_736.2,
                0.0,
                True,
            ),
            _route(
                "route-two",
                "Leg 2B Branch subleg",
                36_862.3,
                1_873.9,
            ),
        ),
        status="Ready",
    )
    result = build_committed_basis_route_proportioning_result_v1(authority)
    assert result.ready is True, result.status

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._committed_basis_route_proportioning_result_v1 = result
    rows = adapter._build_clean_proportioned_route_output_rows_v1(
        provisional_burden_rows=[],
        valve_authority_preview=None,
    )
    assert len(rows) == 2
    assert rows[0]["route"] == "Leg 1B Branch subleg"
    assert rows[0]["route_dp"] == "38736.2 Pa"
    assert rows[0]["proportioned_dp"] == "38736.2 Pa"
    assert rows[1]["added_dp"] == "1873.9 Pa"
    assert rows[1]["target_dp"] == "38736.2 Pa"
    assert rows[1]["residual_dp"] == "0.0 Pa"
    assert rows[1]["at_target"] == "Yes"

    # H-S55-B1: harmless floating-point residue must display as 0.0 Pa,
    # never -0.0 Pa.
    adapter._committed_basis_route_proportioning_result_v1 = SimpleNamespace(
        ready=True,
        status="Ready — committed route result",
        rows=(
            SimpleNamespace(
                route_id="route-near-zero",
                route_label="Near-zero route",
                basis="F&R",
                chosen_pressure_drop_Pa=36_862.3,
                required_added_pressure_drop_Pa=1_873.9,
                proportioned_pressure_drop_Pa=38_736.2,
                controlling_target_pressure_drop_Pa=38_736.2,
                residual_to_target_Pa=-1.0e-9,
                within_tolerance=True,
                status="Ready — committed route reaches controlling target",
            ),
        ),
    )
    zero_rows = adapter._build_clean_proportioned_route_output_rows_v1(
        provisional_burden_rows=[],
        valve_authority_preview=None,
    )
    assert zero_rows[0]["residual_dp"] == "0.0 Pa"

    adapter._build_preview_proportioned_output_status_rows_v1 = (
        lambda **_kwargs: [
            {
                "item": "Accepted return basis",
                "status": (
                    "Committed basis snapshot: DIRECT_RETURN — basis only; "
                    "final hydraulics not committed"
                ),
            }
        ]
    )
    summary = adapter._build_proportioned_output_status_rows_v1(
        resolution=None,
        chosen_preview_rows=[],
        chosen_controlling_rows=[],
        readiness_rows=[],
    )
    assert "committed hydraulic route basis" in summary[0]["status"]
    assert summary[-1]["item"] == "Committed route result"
    assert "no pump" in summary[-1]["status"]

    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    table = panel._clean_proportioned_route_output_table
    headers = [
        table.horizontalHeaderItem(index).text()
        for index in range(table.columnCount())
    ]
    assert headers == [
        "Route",
        "Basis",
        "Chosen Δp",
        "Added Δp",
        "Proportioned Δp",
        "Target Δp",
        "Residual",
        "At target",
        "Status",
    ]
    panel.set_clean_proportioned_route_output_rows(rows)
    assert table.item(1, 4).text() == "38736.2 Pa"
    assert table.item(1, 7).text() == "Yes"
    panel.close()

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "build_committed_basis_route_proportioning_result_v1(" in (
        adapter_source
    )
    assert "Committed route result" in adapter_source
    assert panel_source.count('"Proportioned Δp"') == 2
    assert panel_source.count('"At target"') == 2

    print(
        "OK — H-S55-B committed route result Proportioned UI passed."
    )


if __name__ == "__main__":
    main()
