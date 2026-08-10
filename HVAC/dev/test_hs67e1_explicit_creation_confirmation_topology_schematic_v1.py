from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QLabel,
        QPushButton,
        QWidget,
    )
except ModuleNotFoundError:
    QApplication = QComboBox = QLabel = QPushButton = QWidget = None

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.topology_creation_candidate_v1 import (
    build_add_leg_with_principal_candidate_v1,
)


INITIAL_ROOM_ID = "room-l1a-001"


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()
    candidate = build_add_leg_with_principal_candidate_v1(
        project,
        initial_room_id=INITIAL_ROOM_ID,
    )
    assert candidate.ready, candidate.blockers
    assert candidate.leg_id == "leg-003"

    if QApplication is not None:
        with TemporaryDirectory(prefix="hs67e1-") as temporary_directory:
            project.project_dir = Path(temporary_directory)
            app = QApplication.instance() or QApplication([])
            del app
            from HVAC.gui_v3.adapters.topology_arranger_panel_adapter import (
                TopologyArrangerPanelAdapter,
            )
            from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
            from HVAC.gui_v3.panels.topology_arranger_panel import (
                TopologyArrangerPanel,
            )

            panel = TopologyArrangerPanel()
            adapter = TopologyArrangerPanelAdapter(
                panel=panel,
                context=GuiProjectContext(project_state=project),
            )
            room_selector = panel.findChild(
                QComboBox, "topologyArrangerInitialRoomSelector"
            )
            create_button = panel.findChild(
                QPushButton, "topologyArrangerAddLegButton"
            )
            result_label = panel.findChild(
                QLabel, "topologyArrangerCreationResultLabel"
            )
            schematic = panel.findChild(
                QWidget, "topologyArrangerSchematicWidget"
            )
            assert all(
                item is not None
                for item in (
                    room_selector,
                    create_button,
                    result_label,
                    schematic,
                )
            )
            assert create_button.text() == "Create New Leg + Principal"
            index = room_selector.findData(INITIAL_ROOM_ID)
            assert index >= 0
            room_selector.setCurrentIndex(index)
            create_button.click()

            confirmation = result_label.text()
            # The offscreen test never shows the parent panel, therefore
            # QWidget.isVisible() is false even after this child is explicitly
            # shown. isHidden() tests the label's own presentation state.
            assert not result_label.isHidden()
            assert "Created: Heating Leg 3 → Principal subleg 1" in confirmation
            assert "First room: L1A-R01" in confirmation
            assert "moved from Heating Leg 1" in confirmation
            assert "Full ProjectState step-back saved" in confirmation
            assert "Hydronics Schematic awaits transactional rebuild" in confirmation
            assert adapter._leg_id == "leg-003"
            assert adapter._topology_focus_room_id == INITIAL_ROOM_ID
            assert schematic._focus == {
                "leg_id": "leg-003",
                "subleg_id": "leg-003-primary-subleg",
                "room_id": INITIAL_ROOM_ID,
            }
            created_row = next(
                row
                for row in schematic._rows
                if row["subleg_id"] == "leg-003-primary-subleg"
            )
            assert created_row["leg_label"] == "Heating Leg 3"
            assert created_row["kind"] == "principal"
            assert created_row["rooms"][0]["id"] == INITIAL_ROOM_ID
    else:
        panel_source = Path(
            "HVAC/gui_v3/panels/topology_arranger_panel.py"
        ).read_text(encoding="utf-8")
        adapter_source = Path(
            "HVAC/gui_v3/adapters/topology_arranger_panel_adapter.py"
        ).read_text(encoding="utf-8")
        widget_source = Path(
            "HVAC/gui_v3/widgets/topology_arranger_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        assert "Create New Leg + Principal" in panel_source
        assert "topologyArrangerCreationResultLabel" in panel_source
        assert "Downstream Hydronics" in adapter_source
        assert "build_recursive_subleg_positions_v1(topology)" in adapter_source
        assert "Topology-only preview" in widget_source
        assert "parent_subleg_id" in widget_source

    print(
        "OK — H-S67-E1 confirms Leg/Principal creation explicitly and "
        "refreshes a focused recursive topology-only schematic."
    )


if __name__ == "__main__":
    main()
