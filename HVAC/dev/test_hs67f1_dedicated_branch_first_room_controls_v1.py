from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QPushButton
except ModuleNotFoundError:
    QApplication = QComboBox = QLabel = QPushButton = None

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.topology_creation_candidate_v1 import (
    build_add_branch_subleg_candidate_v1,
)


PARENT_ID = "leg-001-subleg-b"
ORIGIN_ROOM_ID = "room-l1b-002"
BLOCKED_FIRST_ROOM_ID = "room-l1a-002"
VALID_FIRST_ROOM_ID = "room-l2b-003"


def _select(combo, identity: str) -> None:
    index = combo.findData(identity)
    assert index >= 0, (identity, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()

    same_room = build_add_branch_subleg_candidate_v1(
        project,
        parent_subleg_id=PARENT_ID,
        branch_origin_room_id=ORIGIN_ROOM_ID,
        initial_room_id=ORIGIN_ROOM_ID,
    )
    assert not same_room.ready
    assert "take-off room" in " ".join(same_room.blockers).lower()

    if QApplication is not None:
        with TemporaryDirectory(prefix="hs67f1-") as temporary_directory:
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
            parent = panel.findChild(
                QComboBox, "topologyArrangerBranchParentSelector"
            )
            origin = panel.findChild(
                QComboBox, "topologyArrangerBranchOriginSelector"
            )
            branch_first = panel.findChild(
                QComboBox, "topologyArrangerBranchFirstRoomSelector"
            )
            shared_initial = panel.findChild(
                QComboBox, "topologyArrangerInitialRoomSelector"
            )
            add_branch = panel.findChild(
                QPushButton, "topologyArrangerAddBranchButton"
            )
            status = panel.findChild(QLabel, "topologyArrangerStatusLabel")
            assert all(
                item is not None
                for item in (
                    parent,
                    origin,
                    branch_first,
                    shared_initial,
                    add_branch,
                    status,
                )
            )
            assert branch_first is not shared_initial

            _select(parent, PARENT_ID)
            _select(origin, ORIGIN_ROOM_ID)
            assert branch_first.findData(ORIGIN_ROOM_ID) < 0
            assert shared_initial.findData(ORIGIN_ROOM_ID) >= 0

            _select(branch_first, BLOCKED_FIRST_ROOM_ID)
            add_branch.click()
            assert status.text().startswith("Blocked —")

            _select(branch_first, VALID_FIRST_ROOM_ID)
            assert adapter._last_transaction_status == ""
            assert not status.text().startswith("Blocked —")
            assert origin.currentData() == ORIGIN_ROOM_ID
            assert branch_first.findData(ORIGIN_ROOM_ID) < 0
    else:
        panel_source = Path(
            "HVAC/gui_v3/panels/topology_arranger_panel.py"
        ).read_text(encoding="utf-8")
        adapter_source = Path(
            "HVAC/gui_v3/adapters/topology_arranger_panel_adapter.py"
        ).read_text(encoding="utf-8")
        assert "topologyArrangerBranchFirstRoomSelector" in panel_source
        assert "branch_first_room_selection_requested" in panel_source
        assert "room_id != self._branch_origin_room_id" in adapter_source
        assert "def _on_branch_origin_selection_requested" in adapter_source
        assert "def _on_branch_first_room_selection_requested" in adapter_source

    print(
        "OK — H-S67-F1 gives Branch creation a dedicated first-room selector, "
        "excludes the take-off room and clears obsolete blockers live."
    )


if __name__ == "__main__":
    main()
