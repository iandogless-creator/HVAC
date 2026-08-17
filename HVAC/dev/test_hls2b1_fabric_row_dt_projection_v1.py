from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.gui_v3.adapters.heat_loss_panel_adapter import HeatLossPanelAdapter
from HVAC.heatloss.dto.fabric_surface_row_v1 import FabricSurfaceRowV1


def _row(*, element: str, segment=None) -> FabricSurfaceRowV1:
    return FabricSurfaceRowV1(
        surface_id=f"row-{element}",
        room_id="ROOM-1",
        element=element,
        area_m2=1.0,
        u_value_W_m2K=1.0,
        delta_t_K=24.0,
        qf_W=24.0,
        construction_id="TEST",
        _segment=segment,
    )


def main() -> None:
    adapter = HeatLossPanelAdapter.__new__(HeatLossPanelAdapter)

    external = _row(
        element="external_wall",
        segment=SimpleNamespace(
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        ),
    )
    adjacent = _row(
        element="internal_partition",
        segment=SimpleNamespace(
            boundary_kind="INTER_ROOM",
            adjacent_room_id="ROOM-2",
        ),
    )
    window = _row(element="window")
    door = _row(element="external_door")

    assert adapter._format_dt(external) == "24.0 → ext"
    assert adapter._format_dt(adjacent) == "24.0 → ROOM-2"
    assert adapter._format_dt(window) == "24.0 → ext"
    assert adapter._format_dt(door) == "24.0 → ext"

    print(
        "OK — HL-S2B1 canonical fabric rows project external and adjacent "
        "ΔT labels without old-row attributes."
    )


if __name__ == "__main__":
    main()
