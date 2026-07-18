from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRoomEvidenceV1,
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSectionEvidenceV1,
    CommonMainLegSublegSchematicWidgetV1,
)


# H-S39-A — shared schematic room authority-evidence hover.


def main() -> None:
    widget_source = Path(
        "HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py"
    ).read_text()

    assert "H-S39-A" in widget_source
    assert "self._room_hover_hit_rects" in widget_source
    assert "Emitter design flow:" in widget_source
    assert "Incoming Basic PS pipe:" in widget_source

    room_evidence = CommonMainLegSublegRoomEvidenceV1(
        room_id="room-001",
        room_label="Lounge",
        design_heat_loss_W="1200.0 W",
        emitter_summary="Lounge radiator",
        emitter_output_W="1300.0 W",
        emitter_flow_kg_s="0.0311 kg/s",
        flow_basis="Existing branch-aware carried-flow basis",
        status="Read-only room design evidence",
    )
    section_evidence = CommonMainLegSublegSectionEvidenceV1(
        section_ordinal=1,
        trace_index=0,
        flow_kg_s="0.0311 kg/s",
        pipe_dn="10 mm",
    )
    route = CommonMainLegSublegRouteV1(
        subleg_id="leg-001-primary-subleg",
        subleg_label="Subleg 1A",
        room_labels=("room-001",),
        room_evidence=(room_evidence,),
        section_evidence=(section_evidence,),
    )

    assert (
        CommonMainLegSublegSchematicWidgetV1
        ._room_evidence_for_room_id_v1(route, "room-001")
        is room_evidence
    )
    tooltip = (
        CommonMainLegSublegSchematicWidgetV1
        ._room_evidence_tooltip_text_v1(
            route,
            room_evidence,
            section_evidence,
        )
    )
    assert "Design heat loss: 1200.0 W" in tooltip
    assert "Emitter design output: 1300.0 W" in tooltip
    assert "Emitter design flow: 0.0311 kg/s" in tooltip
    assert "Incoming Basic PS pipe: 10 mm" in tooltip

    emitter = SimpleNamespace(
        emitter_id="emitter-001",
        room_id="room-001",
        name="Lounge radiator",
        design_output_W=1300.0,
        mass_flow_kg_s=0.0311,
        design_mass_flow_kg_s=0.0311,
        flow_kg_s=0.0311,
    )
    project = SimpleNamespace(
        rooms={"room-001": SimpleNamespace(name="Lounge")},
        emitters={"emitter-001": emitter},
        heatloss_valid=True,
        environment=SimpleNamespace(
            design_flow_temperature_C=75.0,
            design_return_temperature_C=65.0,
            hydronic_design_flow_temperature_C=75.0,
            hydronic_design_return_temperature_C=65.0,
        ),
        get_room_heatloss_totals=lambda room_id: (800.0, 400.0, 1200.0),
    )
    adapter = object.__new__(HydronicsSchematicPanelAdapter)
    adapter._project_state = project
    built = adapter._build_schematic_room_evidence_v1("room-001")

    assert built.room_id == "room-001"
    assert built.room_label == "Lounge"
    assert built.design_heat_loss_W == "1200.0 W"
    assert built.emitter_summary == "Lounge radiator"
    assert built.emitter_output_W == "1300.0 W"
    assert built.emitter_flow_kg_s.endswith(" kg/s")
    assert built.flow_basis == "Existing branch-aware carried-flow basis"

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "_room_flow_kg_s(project, stable_room_id)" in adapter_source
    assert "room_evidence=room_evidence" in adapter_source

    print("OK — H-S39-A schematic room authority-evidence hover passed.")


if __name__ == "__main__":
    main()
