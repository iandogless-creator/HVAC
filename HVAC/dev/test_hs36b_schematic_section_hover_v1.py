from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSectionEvidenceV1,
    CommonMainLegSublegSchematicWidgetV1,
)


# H-S36-B — schematic section-evidence hover.


def main() -> None:
    source = Path(
        "HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py"
    ).read_text()

    assert "H-S36-B — schematic section-evidence hover" in source
    assert "self._section_trace_hit_rects" in source
    assert "def mouseMoveEvent" in source
    assert "def leaveEvent" in source
    assert "QToolTip.showText" in source
    assert "QToolTip.hideText" in source

    evidence_1 = CommonMainLegSublegSectionEvidenceV1(
        section_id="leg-001-primary-subleg-section-0001",
        section_ordinal=1,
        trace_index=0,
        trace_room_id="11a-001",
        route_id="leg-001-primary-subleg",
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
        from_label="Common main / leg entry",
        to_label="L1A-R01",
        flow_kg_s="0.1699 kg/s",
        pipe_dn="22 mm",
        dp_per_m="222.4",
        length="5.00 m",
        k="3.80",
        section_dp="1668.6 Pa",
        iter="—",
        status=(
            "Branch-aware carried-flow basis / First-pass Haaland estimate"
        ),
    )
    evidence_2 = CommonMainLegSublegSectionEvidenceV1(
        section_id="leg-001-primary-subleg-section-0002",
        section_ordinal=2,
        trace_index=1,
        trace_room_id="11a-002",
        subleg_id="leg-001-primary-subleg",
    )
    route = CommonMainLegSublegRouteV1(
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
        subleg_label="Subleg 1A",
        room_labels=("11a-001", "11a-002"),
        section_evidence=(evidence_1, evidence_2),
    )

    assert (
        CommonMainLegSublegSchematicWidgetV1
        ._section_evidence_for_trace_index_v1(route, 0)
        is evidence_1
    )
    assert (
        CommonMainLegSublegSchematicWidgetV1
        ._section_evidence_for_trace_index_v1(route, 1)
        is evidence_2
    )
    assert (
        CommonMainLegSublegSchematicWidgetV1
        ._section_evidence_for_trace_index_v1(route, 2)
        is None
    )

    tooltip = (
        CommonMainLegSublegSchematicWidgetV1
        ._section_evidence_tooltip_text_v1(route, evidence_1)
    )

    for expected in (
        "Subleg 1A — Section 1",
        "From: Common main / leg entry",
        "To: L1A-R01",
        "Flow: 0.1699 kg/s",
        "Pipe DN: 22 mm",
        "Δp/m: 222.4",
        "Length: 5.00 m",
        "K: 3.80",
        "Section Δp: 1668.6 Pa",
        "Iter: —",
        "Status: Branch-aware carried-flow basis",
    ):
        assert expected in tooltip

    branch_method = source.split(
        "    def _paint_branch_takeoff(",
        1,
    )[1].split(
        "    def _paint_footer(",
        1,
    )[0]
    assert "_register_section_trace_hit_rect_v1" not in branch_method

    print("OK — H-S36-B schematic section-evidence hover passed.")


if __name__ == "__main__":
    main()
