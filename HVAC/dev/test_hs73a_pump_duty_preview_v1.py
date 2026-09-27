"""Numerical, authority, persistence and real-widget tests for H-S73-A."""
from dataclasses import replace
import json
import math
import os

from HVAC.dev.test_hs54a_committed_proportioning_hydraulic_input_authority_v1 import _section
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
    CommittedProportioningHydraulicSectionV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import ProportionedBasisSnapshotV1
from HVAC.hydronics.pumps.pump_preview_controller_v1 import (
    apply_pump_preview_basis_v1, clear_pump_preview_basis_v1, preview_pump_v1,
)
from HVAC.project.project_state import ProjectState


def fixture():
    source = _section("common-main-to-leg-a-section-001", "common_main")
    values = {key: getattr(source, key) for key in
              CommittedProportioningHydraulicSectionV1.__dataclass_fields__
              if hasattr(source, key)}
    values.update(route_ids=("route-a", "route-b"), carried_flow_kg_s=0.6)
    common = CommittedProportioningHydraulicSectionV1(**values)

    def route(key, pressure):
        return CommittedProportioningHydraulicRouteV1(
            route_id=key, route_label=key.title(), basis="F&R",
            chosen_pressure_drop_Pa=pressure, controlling=pressure == 20000,
            required_added_pressure_drop_Pa=20000-pressure,
            preliminary_resistance_Pa_per_kg_s2=0,
            common_main_pressure_drop_Pa=2100, leg_entry_pressure_drop_Pa=500,
            physical_main_entry_pressure_drop_Pa=2600,
        )
    authority = CommittedProportioningHydraulicInputAuthorityV1(
        ready=True, sections=(common,), routes=(route("route-a", 20000), route("route-b", 15000)),
    )
    project = ProjectState(project_id="hs73a", name="H-S73-A pump review")
    project.hydronic_proportioned_basis_snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="F&R", hydraulic_input_authority=authority,
    )
    return project


PAYLOAD = dict(density_kg_m3="1000", additional_common_loss_Pa="5000",
               head_margin_percent="10", source_note="Test fluid: 1000 kg/m³; common plant 5 kPa; explicit 10% margin")


def engineering_tests():
    project = fixture()
    before = json.dumps(project.to_dict(), sort_keys=True)
    initial = preview_pump_v1(project)
    assert not initial.ready and initial.numbers is None
    assert initial.mass_flow_kg_s == 0.6 and initial.pipework_pressure_Pa == 20000
    assert initial.controlling_route_ids == ("route-a",)
    assert json.dumps(project.to_dict(), sort_keys=True) == before, "Read-only review mutated the project"
    assert apply_pump_preview_basis_v1(project, PAYLOAD) == ()
    result = preview_pump_v1(project)
    assert result.ready, result.blockers
    assert math.isclose(result.numbers.flow_m3_h, 2.16)
    assert math.isclose(result.numbers.pressure_Pa, 27500)
    assert math.isclose(result.numbers.head_m, 2.803261977573904)
    saved = project.to_dict()
    changed_keys = {key for key in saved if saved[key] != json.loads(before).get(key)}
    assert changed_keys == {"hydronic_pump_preview_basis"}, changed_keys
    restored = ProjectState.from_dict(json.loads(json.dumps(saved)))
    assert preview_pump_v1(restored).ready, preview_pump_v1(restored).blockers
    assert restored.hydronic_pump_preview_basis == project.hydronic_pump_preview_basis
    del saved["hydronic_pump_preview_basis"]
    assert ProjectState.from_dict(saved).hydronic_pump_preview_basis is None

    # No automatic pump sizing safety factors or efficiency defaults.
    assert not apply_pump_preview_basis_v1(project, {
        **PAYLOAD, "additional_common_loss_Pa": 0, "head_margin_percent": 0,
    })
    assert preview_pump_v1(project).numbers.pressure_Pa == 20000
    for key in ("density_kg_m3", "additional_common_loss_Pa", "head_margin_percent"):
        for bad in ("nan", "inf", "-1", "", None, True):
            existing = project.hydronic_pump_preview_basis
            assert apply_pump_preview_basis_v1(project, {**PAYLOAD, key: bad})
            assert project.hydronic_pump_preview_basis is existing
    assert apply_pump_preview_basis_v1(project, {**PAYLOAD, "density_kg_m3": 0})
    assert apply_pump_preview_basis_v1(project, {**PAYLOAD, "source_note": " "})
    assert apply_pump_preview_basis_v1(project, {
        **PAYLOAD, "additional_common_loss_Pa": 1e308, "head_margin_percent": 1e308,
    })

    snapshot = project.hydronic_proportioned_basis_snapshot
    hydraulic = snapshot.hydraulic_input_authority
    project.hydronic_proportioned_basis_snapshot = replace(snapshot,
        hydraulic_input_authority=replace(hydraulic,
            routes=(hydraulic.routes[0], replace(hydraulic.routes[1], chosen_pressure_drop_Pa=20000))))
    stale = preview_pump_v1(project)
    assert not stale.ready and stale.numbers is None
    assert stale.controlling_route_ids == ("route-a", "route-b")
    assert any("changed" in b for b in stale.blockers)
    assert not apply_pump_preview_basis_v1(project, PAYLOAD)
    assert preview_pump_v1(project).ready

    for invalid in (
        replace(hydraulic, ready=False), replace(hydraulic, sections=()),
        replace(hydraulic, sections=hydraulic.sections * 2),
        replace(hydraulic, sections=(replace(hydraulic.sections[0], route_ids=("route-a",)),)),
        replace(hydraulic, sections=(replace(hydraulic.sections[0], carried_flow_kg_s=float("nan")),)),
        replace(hydraulic, routes=hydraulic.routes * 2),
        replace(hydraulic, routes=(replace(hydraulic.routes[0], chosen_pressure_drop_Pa=-1),)),
    ):
        project.hydronic_proportioned_basis_snapshot = replace(snapshot, hydraulic_input_authority=invalid)
        assert not preview_pump_v1(project).ready
        assert preview_pump_v1(project).numbers is None
    project.hydronic_proportioned_basis_snapshot = None
    assert apply_pump_preview_basis_v1(project, PAYLOAD)
    clear_pump_preview_basis_v1(project)
    assert project.hydronic_pump_preview_basis is None


def widget_tests():
    from PySide6.QtWidgets import QApplication
    from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
    from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import HydronicsSchematicPanelAdapter
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    project = fixture()
    adapter = HydronicsSchematicPanelAdapter(panel=panel, project_state=project)
    widget = panel._pump_preview_widget_v1
    for key, value in PAYLOAD.items():
        widget.inputs[key].setText(value)
    adapter._refresh_pump_preview_v1()
    assert widget.inputs["source_note"].text() == PAYLOAD["source_note"], "Refresh discarded unfinished input"
    widget.apply_button.click()
    app.processEvents()
    assert preview_pump_v1(project).ready
    assert "Ready for preliminary" in widget.status.text()
    assert "2.16" in widget.summary.item(4, 1).text()
    assert widget.routes.rowCount() == 2
    assert widget.summary.alternatingRowColors()
    # New project must clear both saved assumptions and visible old duty.
    other = ProjectState(project_id="other", name="Other")
    adapter.set_project_state(other)
    assert not widget.inputs["density_kg_m3"].text()
    assert widget.summary.item(4, 1).text() == "—"
    adapter.set_project_state(project)
    widget.clear_button.click()
    assert project.hydronic_pump_preview_basis is None
    assert widget.summary.item(4, 1).text() == "—"
    assert not widget.inputs["density_kg_m3"].text()
    panel.close()
    app.processEvents()


if __name__ == "__main__":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    engineering_tests()
    widget_tests()
    print("OK — H-S73-A pump preview: numerical duty, explicit basis, no double counting, stale rejection, persistence and GUI wiring.")
