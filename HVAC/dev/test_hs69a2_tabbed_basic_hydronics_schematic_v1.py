from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.basic_hydronics_panel import BasicHydronicsPanel
from HVAC.hydronics.sizing.basic_ps_schematic_projection_v1 import (
    build_basic_ps_schematic_projection_v1,
)


def main() -> None:
    section = SimpleNamespace(
        section_id="sl-1-section-001",
        leg_id="leg-1",
        subleg_id="sl-1",
        order=1,
        from_label="Common main / leg entry",
        to_room_id="room-1",
        to_room_label="R1 Kitchen",
        carried_flow_kg_s=0.0500,
    )
    sizing = SimpleNamespace(
        section_id=section.section_id,
        carried_flow_kg_s=0.0500,
        pipe_size_label="15 mm",
        velocity_m_s=0.42,
        pressure_gradient_Pa_per_m=120.0,
        status="First-pass Haaland estimate",
    )
    pressure = SimpleNamespace(
        section_id=section.section_id,
        section_length_m=3.0,
        section_pressure_drop_Pa=360.0,
        status="Preview only",
    )
    projection = SimpleNamespace(
        sections_projection=SimpleNamespace(
            leg_id="leg-1",
            leg_label="Leg 1",
            subleg_id="sl-1",
            subleg_label="Primary",
            sections=(section,),
        ),
        pipe_sizing_projection=SimpleNamespace(results=(sizing,)),
        pressure_preview_projection=SimpleNamespace(rows=(pressure,)),
    )
    project = SimpleNamespace(
        rooms={"room-1": SimpleNamespace(name="Kitchen")},
        hydronic_topology=SimpleNamespace(heat_source_room_id=""),
    )

    schematic = build_basic_ps_schematic_projection_v1(project, projection)
    assert schematic.heat_source_label == "Remote Heat Source"
    assert len(schematic.routes) == 1
    evidence = schematic.routes[0].section_evidence[0]
    assert evidence.pipe_dn == "15 mm"
    assert evidence.flow_kg_s == "0.0500 kg/s"
    assert evidence.dp_per_m == "120.0 Pa/m"
    assert evidence.length == "3.00 m"
    assert evidence.section_dp == "360.0 Pa"
    assert evidence.k == "Not included in Basic PS v1"

    app = QApplication.instance() or QApplication([])
    panel = BasicHydronicsPanel()
    tab_names = [
        panel._workspace_tabs.tabText(index)
        for index in range(panel._workspace_tabs.count())
    ]
    assert tab_names == [
        "Setup",
        "Sections",
        "Schematic",
        "Pressure",
        "Candidates",
    ]
    assert panel._basis_mode.count() == 1
    assert panel._basis_mode.currentText() == "INDEX_LENGTH"
    assert panel._commit_button.text() == "Apply"
    assert panel._pass_to_proportioning_button.text() == (
        "Pass to Proportioning"
    )
    assert "#d9ead3" in panel._commit_button.styleSheet().lower()
    assert "#dbe9f6" in (
        panel._pass_to_proportioning_button.styleSheet().lower()
    )
    panel.set_basic_ps_schematic(schematic)
    assert panel._basic_ps_schematic_widget._schematic is schematic

    panel.close()
    app.processEvents()
    print(
        "OK — H-S69-A2 provides compact tabbed Basic Hydronics and a fresh "
        "read-only shared schematic with existing Basic PS evidence."
    )


if __name__ == "__main__":
    main()
