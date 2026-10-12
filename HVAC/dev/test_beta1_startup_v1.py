"""Beta 1 chooser, shared lifecycle, checksum protection and real workspace."""
from pathlib import Path
import math
import tempfile
from unittest.mock import patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication,QDialog,QPushButton
from HVAC.gui_v3.widgets.startup_project_dialog_v1 import StartupProjectDialogV1
from HVAC.gui_v3.context.startup_projects_v1 import create_new_project_v1,open_project_v1
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.gui_v3.run_gui_v3 import make_sample_project_state_v1
from HVAC.project_v3.persistence.saver import save


def main():
    app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory, patch.object(Path,'home',return_value=Path(directory)), patch('HVAC.gui_v3.context.project_workspace_v1.default_project_root_v1',return_value=Path(directory)/'HVACprojects'):
        home=Path(directory)
        QSettings.setPath(QSettings.NativeFormat,QSettings.UserScope,str(home/'settings'))
        for action in ('new','sample'):
            d=StartupProjectDialogV1()
            target_new=home/('startup-'+action);target_new.mkdir()
            with patch('HVAC.gui_v3.widgets.new_project_folder_v1.QFileDialog.getExistingDirectory',return_value=str(target_new)):
                d.findChild(QPushButton,f'startup_{action}').click()
            assert d.action==action and d.result()==QDialog.Accepted
            d.close()
        d=StartupProjectDialogV1()
        with patch('HVAC.gui_v3.widgets.startup_project_dialog_v1.QFileDialog.getExistingDirectory',return_value=''):
            d.choose('open')
        assert d.action is None and d.result()!=QDialog.Accepted
        d.reject();assert d.result()==QDialog.Rejected
        p=create_new_project_v1()
        assert p.name=='Untitled Project' and len(p.rooms)==1 and p.boundary_segments
        assert p.project_dir is None
        assert getattr(p,'hydronic_pump_duty_acceptance',None) is None
        target=home/'saved';save(p,target)
        before=(target/'project.json').read_bytes()
        with patch('HVAC.gui_v3.widgets.startup_project_dialog_v1.QFileDialog.getExistingDirectory',return_value=str(target)):
            d.choose('open')
        assert d.action=='open' and d.project_dir==target
        restored=open_project_v1(target)
        assert (target/'project.json').read_bytes()==before
        assert restored.project_id==p.project_id and len(restored.rooms)==1
        context=GuiProjectContext(project_state=restored)
        assert context.workspace_root==home/'HVACprojects'
        window=MainWindowV3(context=context);window.show();app.processEvents()
        job=home/'Menu new job';job.mkdir()
        with patch('HVAC.gui_v3.widgets.new_project_folder_v1.QFileDialog.getExistingDirectory',return_value=str(job)):
            window.new_project()
        assert context.project_state.project_dir==job
        assert context.project_dir==job and context.project_state.name=='Menu new job'
        assert (job/'project.json').is_file()
        window._run_heatloss_for_current_project()
        computed=context.project_state
        assert computed.heatloss_valid
        # Independent arithmetic for the unchanged 4 x 3 x 2.4 m starter defaults.
        expected_fabric=(2*(4+3)*2.4*0.26+12*0.18+12*0.16)*24
        expected_ventilation=0.33*0.5*(4*3*2.4)*24
        assert math.isclose(computed.heatloss_results['result'].project_total_W,
                            expected_fabric+expected_ventilation,rel_tol=1e-10)
        save(computed,home/'calculated')
        reopened=open_project_v1(home/'calculated')
        assert math.isclose(reopened.heatloss_results['result']['project_total_W'],
                            expected_fabric+expected_ventilation,rel_tol=1e-10)
        window.close();app.processEvents()
        invalid=home/'invalid';invalid.mkdir();(invalid/'project.json').write_text('{}')
        try:open_project_v1(invalid)
        except ValueError:pass
        else:raise AssertionError('Invalid project accepted')
        assert (target/'project.json').read_bytes()==before
        demo=make_sample_project_state_v1()
        assert len(demo.rooms)==20 and demo.project_dir is None
        assert demo.name=="HVACgooee — 20-room example"
        assert getattr(demo,'hydronic_pump_duty_acceptance',None) is None
    print('OK — Beta 1 explicit startup choices, cancel, shared New/Open, saved-file preservation, invalid-file rejection, sample and real workspace.')


if __name__=='__main__':main()
