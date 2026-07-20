from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicV1,
    CommonMainLegSublegSchematicWidgetV1,
    CommonMainLegSublegSectionEvidenceV1,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])

    leg_1_entry = CommonMainLegSublegSectionEvidenceV1(
        section_id="leg-001-primary-section-001",
        section_ordinal=1,
        trace_index=0,
        flow_kg_s="0.1699 kg/s",
        pipe_dn="22 mm",
        dp_per_m="222.4",
    )
    leg_2_entry = CommonMainLegSublegSectionEvidenceV1(
        section_id="leg-002-primary-section-001",
        section_ordinal=1,
        trace_index=0,
        flow_kg_s="0.1794 kg/s",
        pipe_dn="22 mm",
        dp_per_m="244.7",
    )
    routes = (
        CommonMainLegSublegRouteV1(
            leg_id="leg-001",
            leg_label="Leg 1",
            subleg_id="leg-001-primary-subleg",
            subleg_label="Subleg 1A",
            role="Common",
            room_labels=("room-1a-001", "room-1a-002"),
            section_evidence=(leg_1_entry,),
        ),
        CommonMainLegSublegRouteV1(
            leg_id="leg-001",
            leg_label="Leg 1",
            subleg_id="leg-001-subleg-b",
            subleg_label="Subleg 1B",
            role="Branch",
            room_labels=("room-1b-001",),
            section_evidence=(
                CommonMainLegSublegSectionEvidenceV1(
                    section_id="leg-001-subleg-b-section-001",
                    section_ordinal=1,
                    trace_index=0,
                    flow_kg_s="0.0766 kg/s",
                    pipe_dn="10 mm",
                    dp_per_m="1490.9",
                ),
            ),
            parent_subleg_id="leg-001-primary-subleg",
            parent_subleg_label="Subleg 1A",
            is_branch_subleg=True,
        ),
        CommonMainLegSublegRouteV1(
            leg_id="leg-002",
            leg_label="Leg 2",
            subleg_id="leg-002-primary-subleg",
            subleg_label="Subleg 2A",
            role="Common",
            room_labels=("room-2a-001",),
            section_evidence=(leg_2_entry,),
        ),
    )
    schematic = CommonMainLegSublegSchematicV1(
        common_main_label="Common main",
        routes=routes,
        status="Read-only hierarchy evidence",
    )
    widget = CommonMainLegSublegSchematicWidgetV1()
    widget.set_schematic(schematic)

    common_text = widget._hierarchy_tooltip_text_v1(
        "common_main",
        "common_main",
    )
    assert "Scope: Common main" in common_text
    assert "Legs supplied: 2 (Leg 1, Leg 2)" in common_text
    assert "Sublegs supplied: 3" in common_text
    assert "Unique rooms supplied: 4" in common_text

    leg_text = widget._hierarchy_tooltip_text_v1("leg", "leg-001")
    assert "Scope: Leg" in leg_text
    assert "Sublegs: 2 (Subleg 1A, Subleg 1B)" in leg_text
    assert "Unique rooms: 3" in leg_text
    assert "Entry carried flow: 0.1699 kg/s" in leg_text
    assert "Entry pipe: 22 mm" in leg_text

    subleg_text = widget._hierarchy_tooltip_text_v1(
        "subleg",
        "leg-001-subleg-b",
    )
    assert "Scope: Branch" in subleg_text
    assert "Parent: Subleg 1A" in subleg_text
    assert "Rooms: 1" in subleg_text
    assert "Entry carried flow: 0.0766 kg/s" in subleg_text
    assert "Entry pipe: 10 mm" in subleg_text
    assert "Entry Δp/m: 1490.9" in subleg_text

    widget.resize(widget.minimumSize())
    pixmap = QPixmap(widget.size())
    widget.render(pixmap)
    scopes = {
        (scope, stable_id)
        for _rect, scope, stable_id in widget._hierarchy_hover_hit_rects
    }
    assert ("common_main", "common_main") in scopes
    assert ("leg", "leg-001") in scopes
    assert ("leg", "leg-002") in scopes
    assert ("subleg", "leg-001-primary-subleg") in scopes
    assert ("subleg", "leg-001-subleg-b") in scopes

    original_focus = dict(widget._focus)
    widget._hovered_hierarchy_key = ("leg", "leg-001")
    widget.render(pixmap)
    assert widget._focus == original_focus

    print("OK — H-S41-A schematic hierarchy hover summaries passed.")
    app.quit()


if __name__ == "__main__":
    main()
