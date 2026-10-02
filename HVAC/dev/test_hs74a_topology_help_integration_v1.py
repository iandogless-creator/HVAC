"""Real MainWindow help routing, floating placement and fresh-process preference."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QSettings, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.main_window import MainWindowV3
from HVAC.gui_v3.run_gui_v3 import make_dev_bootstrap_project_state


def window_at(root):
    settings = GuiSettings(root)
    qt = QSettings(str(root / 'gui.ini'), QSettings.IniFormat)
    with patch('HVAC.gui_v3.main_window.GuiSettings', return_value=settings), patch(
            'HVAC.gui_v3.main_window.QSettings', return_value=qt):
        window = MainWindowV3(context=GuiProjectContext(project_state=make_dev_bootstrap_project_state()))
    return window


def main():
    app = QApplication.instance() or QApplication([])
    def settle():
        for _ in range(6): app.processEvents()
    if len(sys.argv) == 4 and sys.argv[1] == '--probe':
        window = window_at(Path(sys.argv[2]))
        assert window._topology_arranger_panel._wizard_checkbox_v1.isChecked() == (sys.argv[3] == 'true')
        assert window._topology_arranger_panel._wizard_steps_v1.currentIndex() == 0
        window.close(); settle()
        return
    with TemporaryDirectory(prefix='hs74a-help-') as directory:
        root = Path(directory)
        window = window_at(root)
        window.show(); settle()
        panel = window._topology_arranger_panel
        arranger = window._docks['dock_topology_arranger']
        arranger.setFloating(True); arranger.resize(900, 720); arranger.show()
        education = window._dock_education
        education.setFloating(True); education.show()
        navigation = window._dock_navigation
        navigation.setFloating(True); navigation.show()
        settle()
        education.setGeometry(QRect(90, 100, 560, 380))
        navigation.setGeometry(QRect(50, 50, 440, 180))
        settle()
        edu_geometry = education.geometry()
        nav_geometry = navigation.geometry()
        before = deepcopy(window._context.project_state.to_dict())
        assert not panel._wizard_checkbox_v1.isChecked()
        QTest.mouseClick(panel._wizard_checkbox_v1, Qt.LeftButton)
        panel._wizard_steps_v1.setCurrentIndex(2)
        settle()
        assert 'Branches' in window._education_panel._title.text()
        # Real focus event walks from an input to its field-level topic.
        QTest.mouseClick(panel._branch_origin_selector, Qt.LeftButton)
        panel._branch_origin_selector.hidePopup()
        window._update_education_from_event_object_v1(panel._branch_origin_selector)
        assert 'Branch origin' in window._education_panel._title.text()
        education.hide()
        QTest.mouseClick(panel._help_button_v1, Qt.LeftButton)
        settle()
        assert education.isVisible() and education.isFloating()
        assert education.geometry() == edu_geometry
        assert 'Branch origin' in window._education_panel._title.text()
        for button, mode in ((window._education_panel._btn_beginner, 'Beginner'),
                             (window._education_panel._btn_classical, 'Classical')):
            QTest.mouseClick(button, Qt.LeftButton); settle()
            assert 'Branch origin' in window._education_panel._title.text()
            assert mode in window._education_panel._title.text()
        # Reading or scrolling Education must not replace the chosen subject.
        window._update_education_from_event_object_v1(window._education_panel._body.viewport())
        assert 'Branch origin' in window._education_panel._title.text()
        assert navigation.isFloating() and navigation.geometry() == nav_geometry
        assert window._context.project_state.to_dict() == before
        window.close(); settle()
        for expected in ('true', 'false'):
            if expected == 'false':
                reopened = window_at(root)
                reopened._topology_arranger_panel.set_wizard_enabled_v1(False)
                reopened.close(); settle()
            result = subprocess.run([sys.executable, __file__, '--probe', str(root), expected],
                                    capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stdout + result.stderr
    print('OK — H-S74-A field help and Education levels retain topic; help preserves floating Education/Navigation placement; Wizard on/off persists in fresh processes.')


if __name__ == '__main__':
    main()
