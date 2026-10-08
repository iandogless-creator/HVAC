"""B2 draft/Apply regression, updated for C's authoritative shared density."""
from copy import deepcopy
from dataclasses import replace
import os
from types import SimpleNamespace
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from HVAC.dev.test_hs73a_pump_duty_preview_v1 import fixture, PAYLOAD, RHO
from HVAC.gui_v3.widgets.pump_preview_widget_v1 import PumpPreviewWidgetV1
from HVAC.hydronics.pumps.pump_preview_controller_v1 import (
    pump_preview_draft_defaults_v1, apply_pump_preview_basis_v1, preview_pump_v1)


def main():
    app=QApplication.instance() or QApplication([])
    project=fixture();before=deepcopy(project.to_dict())
    defaults=pump_preview_draft_defaults_v1(project)
    assert defaults['density_kg_m3']==RHO and '70°C' in defaults['fluid_status']
    assert defaults['additional_common_loss_Pa']==defaults['head_margin_percent']==0
    assert project.to_dict()==before and not preview_pump_v1(project).ready
    empty=SimpleNamespace(hydronic_proportioned_basis_snapshot=None)
    assert 'density_kg_m3' not in pump_preview_draft_defaults_v1(empty)
    widget=PumpPreviewWidgetV1()
    def present(owner=1,basis=None,draft=defaults):
        widget.present(status='Review basis',summary=[],routes=[],basis=basis,owner_token=owner,default_basis=draft)
    present()
    assert float(widget.inputs['density_kg_m3'].text())==round(RHO, 3)
    assert widget.inputs['density_kg_m3'].isReadOnly()
    assert widget.inputs['additional_common_loss_Pa'].text()=='0'
    assert widget.inputs['head_margin_percent'].text()=='0'
    calls=[]
    widget.apply_requested.connect(lambda p:calls.append(apply_pump_preview_basis_v1(project,p)))
    widget.apply_button.click()
    assert calls==[()] and preview_pump_v1(project).ready
    assert project.hydronic_pump_duty_acceptance is None
    assert apply_pump_preview_basis_v1(project,PAYLOAD)==()
    saved=project.hydronic_pump_preview_basis.to_dict();present(basis=saved)
    widget.inputs['head_margin_percent'].setText('17');present(basis=saved)
    assert widget.inputs['head_margin_percent'].text()=='17'
    assert project.hydronic_pump_preview_basis.head_margin_percent==10
    original=project.hydronic_pump_preview_basis
    assert apply_pump_preview_basis_v1(project,{**PAYLOAD,'density_kg_m3':1000})
    assert project.hydronic_pump_preview_basis is original
    # First commit fills computed density without discarding allowance drafts.
    present(owner=2,draft=pump_preview_draft_defaults_v1(empty))
    widget.inputs['head_margin_percent'].setText('4');present(owner=2)
    assert float(widget.inputs['density_kg_m3'].text())==round(RHO, 3)
    assert widget.inputs['head_margin_percent'].text()=='4'
    project.environment.design_return_temp_c=60
    present(owner=2,draft=pump_preview_draft_defaults_v1(project))
    assert not widget.inputs['density_kg_m3'].text()
    assert 'Recommit' in widget.density_source.text()
    assert widget.inputs['head_margin_percent'].text()=='4'
    widget.close();app.processEvents()
    print('OK — B2/C inherited density, zero allowances, explicit Apply, stale gate and draft preservation.')

if __name__=='__main__':main()
