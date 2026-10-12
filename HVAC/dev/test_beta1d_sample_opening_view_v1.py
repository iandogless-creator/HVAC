"""Sample startup reuses existing presentation without engineering changes."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
from PySide6.QtCore import QSettings, QRect
from PySide6.QtWidgets import QApplication
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.sample_project_v1 import make_sample_project_state_v1
from HVAC.gui_v3.main_window import MainWindowV3


def main():
    app=QApplication.instance() or QApplication([])
    def settle():
        for _ in range(10):app.processEvents()
    with TemporaryDirectory() as temporary:
        root=Path(temporary);settings=GuiSettings(root/'gui')
        custom=settings.create_workspace_view_v2(name='My rooms view',panels={'dock_rooms':'main'})
        settings.set_last_workspace_view_v2(view_id=custom,mode='main')
        layout={'docks':{'dock_heat_loss':{'screen_name':app.primaryScreen().name(),'x':30,'y':40,'width':640,'height':620}}}
        assert settings.set_named_workspace_layout_v1('heat_loss:exploded',layout)
        saved_heat=settings.named_workspace_layout_v1('heat_loss:exploded')
        definitions=settings.workspace_views_v2();settings.save()
        qt=QSettings(str(root/'gui.ini'),QSettings.IniFormat)
        geometry={'screen_name':app.primaryScreen().name(),'x':70,'y':80,'width':520,'height':170}
        qt.setValue('workspace/navigation_placement_v1',json.dumps({'floating':True,'visible':False,'geometry':geometry}))
        with patch('HVAC.gui_v3.main_window.GuiSettings',return_value=settings),patch('HVAC.gui_v3.main_window.QSettings',return_value=qt),patch('HVAC.gui_v3.context.project_workspace_v1.default_project_root_v1',return_value=root/'HVACprojects'),patch.object(Path,'home',return_value=root):
            project=make_sample_project_state_v1();context=GuiProjectContext(project_state=project)
            win=MainWindowV3(context=context,startup_sample_view_v1=True)
            before=project.to_dict();win.show();settle()
            assert settings.last_workspace_view_v2()=={'view_id':'heat_loss','mode':'floating'}
            assert win._active_exploded_workspace_view_id_v1=='heat_loss:exploded'
            for dock in (win._dock_rooms,win._dock_heat_loss,win._dock_environment):
                assert dock.isVisible() and dock.isFloating()
            nav=win._dock_navigation
            assert nav.isVisible() and nav.isFloating()
            assert nav.geometry()==QRect(70,80,520,170),nav.geometry()
            assert win._dock_heat_loss.geometry().topLeft().x()==30
            assert win._dock_heat_loss.geometry().topLeft().y()==40
            assert settings.workspace_views_v2()==definitions
            assert settings.named_workspace_layout_v1('heat_loss:exploded')==saved_heat
            assert project.to_dict()==before
            assert not win._startup_sample_view_v1
            win._apply_named_workspace_main_view_v2(custom);settle()
            win._restore_workspace_and_navigation_v1();settle()
            assert settings.last_workspace_view_v2()=={'view_id':custom,'mode':'main'}
            win.close();settle()
            ordinary=MainWindowV3(context=GuiProjectContext(project_state=make_sample_project_state_v1()))
            ordinary.show();settle()
            assert settings.last_workspace_view_v2()=={'view_id':custom,'mode':'main'}
            assert ordinary._active_named_workspace_view_id_v2==custom
            ordinary.close();settle()
    print('OK — Sample-only Heat Loss opening, saved panel/Navigation placement, one-shot override, normal restoration and unchanged engineering.')


if __name__=='__main__':main()
