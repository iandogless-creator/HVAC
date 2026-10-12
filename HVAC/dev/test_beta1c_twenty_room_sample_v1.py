"""Bundled sample is a fresh unsaved copy; saved design records remain unchanged."""
from pathlib import Path
import json
import tempfile
from unittest.mock import patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from HVAC.gui_v3.context import sample_project_v1 as sample
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.startup_projects_v1 import open_project_v1
from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.project_v3.persistence.loader import load


def main():
    app=QApplication.instance() or QApplication([])
    source=sample.sample_project_path_v1();original=source.read_bytes()
    baseline=load(source);project=sample.make_sample_project_state_v1()
    assert project.project_dir is None and len(project.rooms)==20
    assert project.name==sample.SAMPLE_NAME
    assert project.project_id!=baseline.project_id
    a=baseline.to_dict();b=project.to_dict()
    for key in a:
        if key not in {'name','project_id'}: assert a[key]==b[key],key
    assert project.hydronic_pump_duty_acceptance is None
    assert len(project.boundary_segments)==80
    assert all(s.adjacent_room_id is None for s in project.boundary_segments.values())
    first=next(iter(project.rooms))
    project.rooms[first].name='Edited copy'
    second=sample.make_sample_project_state_v1()
    assert second.project_id!=project.project_id
    assert second.rooms[first].name==baseline.rooms[first].name
    assert source.read_bytes()==original
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        QSettings.setPath(QSettings.NativeFormat,QSettings.UserScope,str(root/'qt'))
        invalid=root/'corrupt.json'
        data=json.loads(original);data['payload']['name']='tampered'
        invalid.write_text(json.dumps(data))
        with patch.object(sample,'sample_project_path_v1',return_value=invalid):
            try: sample.make_sample_project_state_v1()
            except ValueError: pass
            else: raise AssertionError('Invalid sample checksum accepted')
        with patch.object(Path,'home',return_value=root), patch('HVAC.gui_v3.context.project_workspace_v1.default_project_root_v1',return_value=root/'HVACprojects'):
            context=GuiProjectContext(project_state=second)
            win=MainWindowV3(context=context);win.show();app.processEvents()
            assert win._project_panel._lbl_room_count.text()=='20'
            target=root/'My example copy';target.mkdir()
            with patch.object(QFileDialog,'getExistingDirectory',return_value=''):
                win._save_project()
            assert second.project_dir is None and source.read_bytes()==original
            with patch.object(QFileDialog,'getExistingDirectory',return_value=str(target)),patch.object(QMessageBox,'information'):
                win._save_project()
            assert second.project_dir==target
            assert (target/'project.json').exists() and source.read_bytes()==original
            reopened=open_project_v1(target)
            assert len(reopened.rooms)==20 and reopened.project_id==second.project_id
            assert reopened.name=='My example copy'
            assert reopened.hydronic_pump_duty_acceptance is None
            win.close();app.processEvents()
    print('OK — 20-room sample, preserved design records, unique unsaved copies, original-file protection, checksum rejection and Save As/reopen.')


if __name__=='__main__':main()
