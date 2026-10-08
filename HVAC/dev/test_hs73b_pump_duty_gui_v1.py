"""Actual panel/adapter signals, project swap, unsaved edits and duty acceptance."""
from dataclasses import replace
import os
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from HVAC.dev.test_hs73b_pump_duty_v1 import fixture, payload
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import HydronicsSchematicPanelAdapter
from HVAC.hydronics.pumps.pump_duty_controller_v1 import preview_pump_duty_v1
from HVAC.project.project_state import ProjectState


def fill(widget):
    data = payload()
    routes = {r['route_id']: r for r in data['routes']}
    points = {p['point_id']: p for p in data['points']}
    for i, key in enumerate(widget._route_ids):
        widget.routes.item(i, 2).setText(str(routes[key]['pressure_Pa']))
        widget.routes.item(i, 6).setText(routes[key]['source_note'])
    for i, key in enumerate(widget._point_ids):
        widget.points.item(i, 3).setText(str(points[key]['operating_kv']))
    widget.review_note.setText(data['review_note'])
    widget.reviewed.setChecked(True)


def main():
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    project = fixture()
    adapter = HydronicsSchematicPanelAdapter(panel=panel, project_state=project)
    calls = []
    adapter._context = SimpleNamespace(project_changed=SimpleNamespace(emit=lambda: calls.append(project)))
    widget = panel._pump_duty_widget_v1
    assert panel._pump_tabs_v1.count() == 2
    assert widget.routes.rowCount() == 3 and widget.points.rowCount() == 2
    assert not widget.accept_button.isEnabled()
    fill(widget)
    draft = widget.payload_v1()
    adapter._refresh_pump_preview_v1()
    assert widget.payload_v1() == draft, 'Refresh lost unsaved inputs'
    widget.apply_button.click()
    assert len(calls) == 1 and project.hydronic_pump_duty_basis is not None
    assert widget.accept_button.isEnabled()
    assert not preview_pump_duty_v1(project).accepted
    widget.accept_button.click()
    assert len(calls) == 2 and preview_pump_duty_v1(project).accepted
    assert 'Accepted required design duty' in widget.status.text()
    widget.routes.item(0, 2).setText('99')
    assert not widget.accept_button.isEnabled()
    adapter._refresh_pump_duty_v1()
    assert widget.routes.item(0, 2).text() == '99'
    assert preview_pump_duty_v1(project).accepted, 'Unapplied edit changed saved duty'
    widget.routes.item(0, 2).setText('nan')
    widget.apply_button.click()
    assert len(calls) == 2 and widget.message.text()
    assert preview_pump_duty_v1(project).accepted
    # Loading a different project must not inherit this project's draft or status.
    adapter.set_project_state(ProjectState(project_id='empty', name='Empty'))
    assert widget.routes.rowCount() == widget.points.rowCount() == 0
    assert not widget.review_note.text() and not widget.reviewed.isChecked()
    assert not widget.accept_button.isEnabled() and not widget.withdraw_button.isEnabled()
    adapter.set_project_state(project)
    assert widget.routes.item(0, 2).text() == '100.0'
    assert 'Accepted required design duty' in widget.status.text()
    widget.withdraw_button.click()
    assert len(calls) == 3 and not preview_pump_duty_v1(project).accepted
    assert widget.accept_button.isEnabled()
    widget.accept_button.click()
    # Underlying snapshot/fluid changes are rechecked even with the old button enabled.
    base = project.hydronic_pump_preview_basis
    project.hydronic_pump_preview_basis = replace(base, density_kg_m3=998)
    adapter._refresh_pump_preview_v1()
    assert not widget.accept_button.isEnabled()
    assert 'not current' in widget.status.text()
    widget.clear_button.click()
    assert project.hydronic_pump_duty_basis is None
    assert project.hydronic_pump_duty_acceptance is None
    assert not widget.review_note.text()
    panel.close()
    app.processEvents()
    print('OK — H-S73-B real panel/adapter: apply, explicit acceptance, draft preservation, invalidation, withdraw, clear and project swap.')


if __name__ == '__main__':
    main()
