from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicV1,
)


# H-S36-A2 — clean schematic section-evidence mapping.


def _row(
        *,
        route: str,
        section: str,
        from_label: str,
        to_label: str,
        subleg_id: str = "",
        route_id: str = "",
) -> dict:
    return {
        "route": route,
        "section": section,
        "section_id": (
            f"{subleg_id}-section-{int(section):04d}"
            if subleg_id and section.isdigit()
            else "—"
        ),
        "route_code": "",
        "leg_id": "",
        "subleg_id": subleg_id or "—",
        "route_id": route_id or subleg_id or "—",
        "from": from_label,
        "to": to_label,
        "flow_kg_s": "0.1000 kg/s",
        "pipe_dn": "15 mm",
        "dp_per_m": "250.0",
        "length": "5.00 m",
        "k": "2.00",
        "section_dp": "1500.0 Pa",
        "iter": "—",
        "status": "First-pass Haaland estimate",
    }


def main() -> None:
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()
    widget_source = Path(
        "HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py"
    ).read_text()

    assert "H-S36-A2 — clean schematic section-evidence mapping" in panel_source
    assert "class CommonMainLegSublegSectionEvidenceV1" in widget_source
    assert "section_evidence:" in widget_source
    assert "def _clean_proportioned_schematic_with_section_evidence_v1" in panel_source
    assert "def _refresh_clean_proportioned_schematic_section_evidence_v1" in panel_source

    common_route = CommonMainLegSublegRouteV1(
        leg_id="leg-001",
        leg_label="Leg 1",
        subleg_id="leg-001-primary-subleg",
        subleg_label="Subleg 1A",
        role="Common",
        room_labels=("11a-001", "11a-002"),
    )
    branch_route = CommonMainLegSublegRouteV1(
        leg_id="leg-002",
        leg_label="Leg 2",
        subleg_id="leg-002-subleg-b",
        subleg_label="Subleg 2B",
        role="Branch",
        room_labels=("12b-001", "12b-002"),
        parent_subleg_id="leg-002-primary-subleg",
        is_branch_subleg=True,
    )
    schematic = CommonMainLegSublegSchematicV1(
        routes=(common_route, branch_route),
    )

    rows = [
        _row(
            route="Leg 1A Common subleg",
            section="1",
            from_label="Common main / leg entry",
            to_label="L1A-R01",
            subleg_id="leg-001-primary-subleg",
        ),
        _row(
            route="Leg 1A Common subleg",
            section="2",
            from_label="L1A-R01",
            to_label="L1A-R02",
            subleg_id="leg-001-primary-subleg",
        ),
        _row(
            route="Leg 2B Branch subleg",
            section="1",
            from_label="Common main / leg entry",
            to_label="L2B-R01",
            subleg_id="leg-002-subleg-b",
        ),
        # Token fallback is retained for older display evidence without IDs.
        _row(
            route="Leg 2B Branch subleg",
            section="2",
            from_label="L2B-R01",
            to_label="L2B-R02",
        ),
        # Out-of-range evidence must not be attached to a non-existent trace.
        _row(
            route="Leg 2B Branch subleg",
            section="9",
            from_label="L2B-R08",
            to_label="L2B-R09",
            subleg_id="leg-002-subleg-b",
        ),
    ]

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)
    mapped = panel._clean_proportioned_schematic_with_section_evidence_v1(
        schematic,
        rows,
    )

    assert mapped is not schematic
    assert schematic.routes[0].section_evidence == ()
    assert schematic.routes[1].section_evidence == ()

    common_evidence = mapped.routes[0].section_evidence
    branch_evidence = mapped.routes[1].section_evidence

    assert [item.section_ordinal for item in common_evidence] == [1, 2]
    assert [item.trace_index for item in common_evidence] == [0, 1]
    assert [item.trace_room_id for item in common_evidence] == [
        "11a-001",
        "11a-002",
    ]
    assert common_evidence[0].subleg_id == "leg-001-primary-subleg"
    assert common_evidence[0].to_label == "L1A-R01"
    assert common_evidence[0].pipe_dn == "15 mm"

    assert [item.section_ordinal for item in branch_evidence] == [1, 2]
    assert [item.trace_room_id for item in branch_evidence] == [
        "12b-001",
        "12b-002",
    ]
    assert branch_evidence[1].subleg_id == "leg-002-subleg-b"
    assert all(item.section_ordinal != 9 for item in branch_evidence)

    print("OK — H-S36-A2 clean schematic section-evidence mapping passed.")


if __name__ == "__main__":
    main()
