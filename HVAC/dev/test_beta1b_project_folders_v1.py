"""New job folder wiring, cancellation, preservation and checksummed reopen."""
from pathlib import Path
import tempfile
from unittest.mock import patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QDialog
from HVAC.gui_v3.context import project_workspace_v1 as workspace
from HVAC.gui_v3.widgets import new_project_folder_v1 as folders
from HVAC.gui_v3.widgets.startup_project_dialog_v1 import StartupProjectDialogV1
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.startup_projects_v1 import open_project_v1
from HVAC.gui_v3.main_window import MainWindowV3


def main():
    app=QApplication.instance() or QApplication([])
    import runpy
    provider=runpy.run_path(workspace.__file__)['default_project_root_v1']
    assert provider()==Path(workspace.__file__).resolve().parents[2]/'HVACprojects'
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)/'HVACprojects';root.mkdir()
        QSettings.setPath(QSettings.NativeFormat,QSettings.UserScope,str(Path(temporary)/'qt'))
        with patch.object(Path,'home',return_value=Path(temporary)), patch.object(workspace,'default_project_root_v1',return_value=root), patch.object(folders.QMessageBox,'warning') as warning:
            dialog=StartupProjectDialogV1()
            with patch.object(folders.QFileDialog,'getExistingDirectory',return_value='') as picker:
                dialog.choose('new')
            assert dialog.action is None and dialog.result()!=QDialog.Accepted
            assert picker.call_args.args[2]==str(root)
            assert not list(root.iterdir())
            job=root/'New boiler job';job.mkdir()
            with patch.object(folders.QFileDialog,'getExistingDirectory',return_value=str(job)):
                dialog.choose('new')
            assert dialog.result()==QDialog.Accepted and dialog.action=='new'
            p=dialog.project_state
            assert p.project_dir==job and p.name==job.name and len(p.rooms)==1
            assert getattr(p,'hydronic_pump_duty_acceptance',None) is None
            original=(job/'project.json').read_bytes()
            restored=open_project_v1(job)
            assert restored.project_id==p.project_id and restored.name==job.name
            assert (job/'project.json').read_bytes()==original
            note=root/'Notes';note.mkdir();(note/'notes.txt').write_text('Keep me')
            for target in (job,root,note):
                with patch.object(folders.QFileDialog,'getExistingDirectory',return_value=str(target)):
                    assert folders.choose_new_project_v1() is None
            assert (job/'project.json').read_bytes()==original
            assert (note/'notes.txt').read_text()=='Keep me'
            assert not (root/'project.json').exists()
            ctx=GuiProjectContext(project_state=restored)
            ctx.project_dir=job
            win=MainWindowV3(context=ctx);win.show();app.processEvents()
            for target in ('',str(job)):
                with patch.object(folders.QFileDialog,'getExistingDirectory',return_value=target): win.new_project()
                assert ctx.project_state is restored and ctx.project_dir==job
            failed=root/'Failed';failed.mkdir()
            with patch.object(folders.QFileDialog,'getExistingDirectory',return_value=str(failed)), patch.object(folders,'save_project',side_effect=OSError('test disk failure')):
                win.new_project()
            assert ctx.project_state is restored and ctx.project_dir==job
            assert not (failed/'project.json').exists()
            new=root/'Menu job';new.mkdir()
            with patch.object(folders.QFileDialog,'getExistingDirectory',return_value=str(new)):
                win.new_project()
            assert ctx.project_state is not restored and ctx.project_dir==new
            assert ctx.project_state.name=='Menu job'
            reopened=open_project_v1(new)
            assert reopened.project_id==ctx.project_state.project_id
            for action in (win._open_project,win._save_project_as):
                with patch.object(folders.QFileDialog,'getExistingDirectory',return_value='') as picker:
                    action()
                assert picker.call_args.args[2]==str(root)
                assert ctx.project_dir==new
            assert (job/'project.json').read_bytes()==original
            assert warning.call_count>=5
            win.close();dialog.close();app.processEvents()
    print('OK — shared HVACprojects root, explicit fresh job folders, startup/menu New, checksum reopen, cancel, existing-job protection and save failure.')


if __name__=='__main__':main()
