"""Topology guidance: content, unchanged engineering, direct-mode parity and lifecycle."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from HVAC.dev.bootstrap_hydronic_20_room_multileg import build_hydronic_20_room_multileg_project_v1
from HVAC.education.resolver import resolve
from HVAC.education.topology_guidance_v1 import TOPOLOGY_TOPICS_V1, TOPOLOGY_STEPS_V1
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.topology_arranger_panel import TopologyArrangerPanel
from HVAC.gui_v3.adapters.topology_arranger_panel_adapter import TopologyArrangerPanelAdapter


def main():
    for topic in TOPOLOGY_TOPICS_V1:
        bodies = []
        for mode in ('beginner', 'standard', 'classical'):
            title, body = resolve(domain='topology', topic=topic, mode=mode)
            assert title.startswith('Topology —') and mode.title() in title
            assert 'No education content' not in body
            assert 200 < len(body) < 1200
            bodies.append(body)
        assert len(set(bodies)) == 3
    assert {key for key, _, _ in TOPOLOGY_STEPS_V1} <= TOPOLOGY_TOPICS_V1
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(prefix='hs74a-topology-') as temporary:
        project = build_hydronic_20_room_multileg_project_v1()
        project.project_dir = Path(temporary)
        context = GuiProjectContext(project_state=project)
        panel = TopologyArrangerPanel()
        adapter = TopologyArrangerPanelAdapter(panel=panel, context=context)
        initial = deepcopy(project.to_dict())
        enabled = tuple(button.isEnabled() for button in (
            panel._move_up_button, panel._move_down_button,
            panel._make_terminal_button, panel._set_index_button,
        ))
        panel._leg_label_edit.setText('Draft label')
        room_id = panel.selected_initial_room_id()
        mutations = []
        for name in ('add_leg_requested', 'add_principal_requested', 'add_branch_requested',
                     'move_up_requested', 'move_down_requested', 'make_terminal_requested',
                     'set_index_requested', 'room_placement_requested', 'return_room_to_staging_requested'):
            getattr(panel, name).connect(lambda *args: mutations.append(args))
        panel.set_wizard_enabled_v1(True)
        assert not panel._guide_controls_v1.isHidden()
        assert not panel._wizard_back_v1.isEnabled()
        for index in range(len(TOPOLOGY_STEPS_V1)):
            assert panel._wizard_steps_v1.currentIndex() == index
            assert panel._topology_schematic_scroll.isHidden() is False
            assert panel._principal_controls.isHidden() == (index != 1)
            assert panel._branch_controls.isHidden() == (index != 2)
            assert panel._table.isHidden() == (index not in (3, 4))
            panel._help_button_v1.click()
            panel._wizard_next_v1.click()
        assert not panel._wizard_next_v1.isEnabled()
        panel._wizard_back_v1.click()
        adapter.refresh()
        assert panel._wizard_steps_v1.currentIndex() == 3
        assert panel._leg_label_edit.text() == 'Draft label'
        panel.set_wizard_enabled_v1(False)
        assert panel._guide_controls_v1.isHidden()
        assert all(not w.isHidden() for w in (panel._principal_controls, panel._branch_controls,
            panel._staging_scroll, panel._table, panel._route_actions))
        assert panel.selected_initial_room_id() == room_id
        assert enabled == tuple(b.isEnabled() for b in (panel._move_up_button, panel._move_down_button,
            panel._make_terminal_button, panel._set_index_button))
        assert not mutations and project.to_dict() == initial
        # The SAME explicit creation action remains operational in guided mode.
        panel.set_wizard_enabled_v1(True)
        panel._wizard_steps_v1.setCurrentIndex(1)
        panel._initial_room_selector.setCurrentIndex(panel._initial_room_selector.findData('room-l1a-001'))
        panel._add_leg_button.click()
        assert len(mutations) == 1
        assert adapter._leg_id == 'leg-003'
        assert 'Created:' in panel._creation_result_label.text()
        assert 'room-l1a-001' in project.hydronic_topology.legs[-1].sublegs[0].route_room_ids
        assert panel._wizard_steps_v1.currentIndex() == 1
        # New project clears old draft labels, help position and creation status.
        panel._branch_label_edit.setText('Old project draft')
        other = build_hydronic_20_room_multileg_project_v1()
        other.project_dir = Path(temporary) / 'other'
        context.set_project_state(other)
        assert panel._wizard_checkbox_v1.isChecked()
        assert panel._wizard_steps_v1.currentIndex() == 0
        assert not panel._branch_label_edit.text()
        assert not panel._creation_result_label.text()
        panel.close()
        app.processEvents()
    print('OK — H-S74-A topology topics at all levels; guided navigation leaves engineering unchanged; direct controls, explicit creation and project lifecycle preserved.')


if __name__ == '__main__':
    main()
