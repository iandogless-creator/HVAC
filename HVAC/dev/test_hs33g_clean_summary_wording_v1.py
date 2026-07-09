from __future__ import annotations

import inspect

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def main() -> None:
    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)

    assert panel._clean_proportioned_summary_status_v1(
        item="Accepted return basis",
        status=(
            "Committed basis snapshot: DIRECT_RETURN — basis only; "
            "final hydraulics not committed"
        ),
    ) == "Accepted basis — DIRECT_RETURN (basis only)"

    assert panel._clean_proportioned_summary_status_v1(
        item="Route pressure evidence",
        status="Chosen-basis route Δp evidence available — preview only",
    ) == "Ready — route Δp evidence available"

    assert panel._clean_proportioned_summary_status_v1(
        item="Controlling / shortfall evidence",
        status="Controlling route / shortfall evidence available — preview only",
    ) == "Ready — controlling/shortfall evidence available"

    assert panel._clean_proportioned_summary_status_v1(
        item="Chosen-basis readiness",
        status="Readiness evidence available — see readiness table",
    ) == "Ready — chosen-basis readiness evidence available"

    assert panel._clean_proportioned_summary_status_v1(
        item="Basis-only export",
        status=(
            "Ready for basis-only Proportioned output export — final "
            "hydraulics not included; pump, valve selection, final "
            "balancing, and pipe resizing not performed"
        ),
    ) == "Ready — basis-only export; final hydraulics excluded"

    authority_status = (
        "Ready with warnings — 3 calculated, 2 acceptable, "
        "1 not required, 1 low-authority warning"
    )

    assert panel._clean_proportioned_summary_status_v1(
        item="Valve authority preview",
        status=authority_status,
    ) == authority_status

    source = inspect.getsource(HydronicsSchematicPanel)

    assert "_clean_proportioned_summary_status_v1" in source
    assert "set_clean_proportioned_output_rows" in source
    assert "final hydraulics excluded" in source
    assert "Accepted basis" in source

    print("OK — H-S33-G clean summary wording passed.")


if __name__ == "__main__":
    main()
