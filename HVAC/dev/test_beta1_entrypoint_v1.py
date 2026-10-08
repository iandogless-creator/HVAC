"""Exercise the real chooser -> splash -> event-loop startup in fresh processes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch


def case(action,home):
    from PySide6.QtCore import QTimer,QSettings
    from PySide6.QtWidgets import QApplication
    from HVAC.gui_v3.context.startup_projects_v1 import create_new_project_v1
    from HVAC.project_v3.persistence.saver import save
    from HVAC.gui_v3.widgets.startup_project_dialog_v1 import StartupProjectDialogV1
    from HVAC.gui_v3 import run_gui_v3 as runner
    target=home/'saved'
    if action=='open':save(create_new_project_v1(),target)
    class Chooser(StartupProjectDialogV1):
        def exec(self):
            QTimer.singleShot(0,self.reject if action=='cancel' else lambda:self.choose(action))
            return super().exec()
    original_window=runner.MainWindowV3;opened=[]
    class Window(original_window):
        def __init__(self,**kwargs):
            super().__init__(**kwargs)
            opened.append(kwargs['context'].project_state)
            QTimer.singleShot(100,QApplication.instance().quit)
    original_sample=runner.make_dev_bootstrap_project_state;sample_calls=[]
    def sample():
        sample_calls.append(True);return original_sample()
    QSettings.setPath(QSettings.NativeFormat,QSettings.UserScope,str(home/'qt'))
    with patch.object(Path,'home',return_value=home),patch('HVAC.gui_v3.widgets.startup_project_dialog_v1.StartupProjectDialogV1',Chooser),patch.object(runner,'MainWindowV3',Window),patch.object(runner,'make_dev_bootstrap_project_state',sample),patch('HVAC.gui_v3.widgets.startup_project_dialog_v1.QFileDialog.getExistingDirectory',return_value=str(target)):
        sys.argv=['run_hvacgooee.py']
        try:runner.main()
        except SystemExit as exc:assert exc.code==0
    assert bool(opened)==(action!='cancel')
    assert bool(sample_calls)==(action=='sample')
    if opened:
        assert (opened[0].project_dir is not None)==(action=='open')
        assert getattr(opened[0],'hydronic_pump_duty_acceptance',None) is None


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--case':
        case(sys.argv[2],Path(sys.argv[3]));return
    for action in ('new','open','sample','cancel'):
        with tempfile.TemporaryDirectory(prefix='beta1-entry-') as temporary:
            env={**os.environ,'QT_QPA_PLATFORM':'offscreen','XDG_CONFIG_HOME':temporary+'/config','XDG_DATA_HOME':temporary+'/data'}
            r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--case',action,temporary],env=env,capture_output=True,text=True,timeout=30)
            assert r.returncode==0,(action,r.stdout,r.stderr)
    print('OK — real New/Open/Sample/Cancel entry point, splash, workspace and event loop; sample only by explicit choice.')


if __name__=='__main__':main()
