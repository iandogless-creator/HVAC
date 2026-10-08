"""Real Environment/adapter and Pump widgets; no project-file writes."""
from copy import deepcopy
import os
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from HVAC.dev.test_hs73b_pump_duty_v1 import fixture, apply
from HVAC.gui_v3.panels.environment_panel import EnvironmentPanel
from HVAC.gui_v3.adapters.environment_panel_adapter import EnvironmentPanelAdapter
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import HydronicsSchematicPanelAdapter
from HVAC.hydronics.pumps.pump_duty_controller_v1 import preview_pump_duty_v1, accept_pump_duty_v1

class Context(QObject):
    environment_changed=Signal()
    project_state_changed=Signal()
    project_changed=Signal()
    def __init__(self,project):super().__init__();self.project_state=project


def main():
    app=QApplication.instance() or QApplication([])
    project=fixture();result=apply(project)
    assert accept_pump_duty_v1(project,result.basis_fingerprint)==()
    snapshot=project.hydronic_proportioned_basis_snapshot
    acceptance=project.hydronic_pump_duty_acceptance
    context=Context(project);environment=EnvironmentPanel()
    env_adapter=EnvironmentPanelAdapter(context=context,panel=environment);env_adapter.refresh()
    panel=HydronicsSchematicPanel()
    adapter=HydronicsSchematicPanelAdapter(panel=panel,project_state=project,context=context)
    assert '70°C' in environment._water_basis_label_v1.text()
    assert panel._pump_preview_widget_v1.inputs['density_kg_m3'].isReadOnly()
    assert preview_pump_duty_v1(project).accepted
    # Actual spinbox signal must refresh both Pump views and disable acceptance.
    environment._design_flow_temp_input.setValue(80);app.processEvents()
    assert project.environment.design_flow_temp_c==80
    assert '72.5°C' in environment._water_basis_label_v1.text()
    assert 'Recommit' in panel._pump_preview_widget_v1.status.text()
    assert not panel._pump_duty_widget_v1.accept_button.isEnabled()
    assert not preview_pump_duty_v1(project).accepted
    assert project.hydronic_proportioned_basis_snapshot is snapshot
    assert project.hydronic_pump_duty_acceptance is acceptance
    assert not project.hydronics_valid
    assert not panel._proportioned_pipe_resizing_schedule_commit_button_v1.isEnabled()
    # Invalid design pair is visible; no static-density fallback or commit.
    environment._design_return_temp_input.setValue(85);app.processEvents()
    assert 'above' in environment._water_basis_label_v1.text()
    assert not panel._commit_proportioning_button.isEnabled()
    environment.close();panel.close();app.processEvents()
    print('OK — shared water Environment display, signal-driven Pump staleness, preserved snapshot/acceptance and invalid-input gates.')

if __name__=='__main__':main()
