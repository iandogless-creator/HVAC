from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRoomEvidenceV1,
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicWidgetV1,
)


# H-S39-B — blue schematic room hover presentation.


def main() -> None:
    source = Path(
        "HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py"
    ).read_text()

    assert "H-S39-B — blue room-node hover presentation only" in source
    assert "self._hovered_room_key" in source
    assert "room_hovered" in source
    assert "QColor(35, 125, 185)" in source
    assert "room_border_width = 3.0" in source

    evidence = CommonMainLegSublegRoomEvidenceV1(room_id="room-001")
    route = CommonMainLegSublegRouteV1(
        subleg_id="leg-001-primary-subleg",
        room_labels=("room-001",),
        room_evidence=(evidence,),
    )

    key = CommonMainLegSublegSchematicWidgetV1._room_evidence_key_v1(
        route,
        evidence,
    )
    assert key == ("leg-001-primary-subleg", "room-001")

    # Presentation only: the room evidence and stable identity are unchanged.
    assert route.room_evidence == (evidence,)
    assert route.room_labels == ("room-001",)

    print("OK — H-S39-B schematic room hover highlight passed.")


if __name__ == "__main__":
    main()
