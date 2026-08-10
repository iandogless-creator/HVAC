from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton
except ModuleNotFoundError:
    QApplication = QComboBox = QLineEdit = QPushButton = None

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    BRANCH_SUBLEG_KIND,
    build_recursive_subleg_positions_v1,
)
from HVAC.hydronics.topology.topology_creation_candidate_v1 import (
    build_add_branch_subleg_candidate_v1,
)
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    TOPOLOGY_STEPBACK_DIRECTORY,
    commit_validated_topology_candidate_v1,
    load_latest_topology_stepback_candidate_v1,
)


PARENT_ID = "leg-001-subleg-b"
ORIGIN_ROOM_ID = "room-l1b-002"
INITIAL_ROOM_ID = "room-l2b-003"


def _select(combo, identity: str) -> None:
    index = combo.findData(identity)
    assert index >= 0, (identity, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def _commit(project, candidate, action: str) -> None:
    result = commit_validated_topology_candidate_v1(
        project,
        candidate.topology,
        action_label=action,
        focus_kind=candidate.focus_kind,
        focus_target_id=candidate.focus_target_id,
    )
    assert result.ready and result.changed, result.blockers
    assert result.focus is not None
    assert result.focus.kind == "branch_subleg"
    assert result.focus.subleg_id == candidate.created_subleg_id


def main() -> None:
    with TemporaryDirectory(prefix="hs67f-") as temporary_directory:
        project = build_hydronic_20_room_multileg_project_v1()
        project.project_dir = Path(temporary_directory)
        project.hydronics_valid = True
        original = project.hydronic_topology.to_dict()

        candidate = build_add_branch_subleg_candidate_v1(
            project,
            parent_subleg_id=PARENT_ID,
            branch_origin_room_id=ORIGIN_ROOM_ID,
            initial_room_id=INITIAL_ROOM_ID,
            branch_label="Nested east branch",
        )
        assert candidate.ready, candidate.blockers
        assert candidate.migration_applied
        assert candidate.room_reallocated
        assert candidate.parent_subleg_id == PARENT_ID
        assert candidate.branch_origin_room_id == ORIGIN_ROOM_ID
        assert candidate.created_subleg_id == (
            "leg-001-subleg-b-branch-subleg-001"
        )
        assert candidate.focus_kind == "branch_subleg"
        assert project.hydronic_topology.to_dict() == original

        same_as_origin = build_add_branch_subleg_candidate_v1(
            project,
            parent_subleg_id=PARENT_ID,
            branch_origin_room_id=ORIGIN_ROOM_ID,
            initial_room_id=ORIGIN_ROOM_ID,
        )
        assert not same_as_origin.ready
        assert "must differ" in " ".join(same_as_origin.blockers).lower()

        wrong_origin = build_add_branch_subleg_candidate_v1(
            project,
            parent_subleg_id=PARENT_ID,
            branch_origin_room_id="room-l2a-001",
            initial_room_id=INITIAL_ROOM_ID,
        )
        assert not wrong_origin.ready
        assert "immediate parent" in " ".join(wrong_origin.blockers).lower()

        if QApplication is not None:
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
            parent_selector = panel.findChild(
                QComboBox, "topologyArrangerBranchParentSelector"
            )
            origin_selector = panel.findChild(
                QComboBox, "topologyArrangerBranchOriginSelector"
            )
            room_selector = panel.findChild(
                QComboBox, "topologyArrangerBranchFirstRoomSelector"
            )
            view_selector = panel.findChild(
                QComboBox, "topologyArrangerPrincipalSelector"
            )
            branch_label = panel.findChild(
                QLineEdit, "topologyArrangerNewBranchLabel"
            )
            add_branch = panel.findChild(
                QPushButton, "topologyArrangerAddBranchButton"
            )
            assert all(
                item is not None
                for item in (
                    parent_selector,
                    origin_selector,
                    room_selector,
                    view_selector,
                    branch_label,
                    add_branch,
                )
            )

            _select(parent_selector, PARENT_ID)
            _select(origin_selector, ORIGIN_ROOM_ID)
            assert room_selector.findData(ORIGIN_ROOM_ID) < 0
            _select(room_selector, INITIAL_ROOM_ID)
            branch_label.setText("Nested east branch")
            add_branch.click()
            created_id = adapter._principal_subleg_id
            assert view_selector.currentData() == created_id
            assert "Nested east branch" in panel._title_label.text()
            assert not panel._move_up_button.isEnabled()
            assert not panel._set_index_button.isEnabled()
        else:
            _commit(project, candidate, "Create nested east branch")
            created_id = candidate.created_subleg_id

        positions = build_recursive_subleg_positions_v1(
            project.hydronic_topology
        )
        created = next(item for item in positions if item.subleg_id == created_id)
        assert created.kind == BRANCH_SUBLEG_KIND
        assert created.parent_subleg_id == PARENT_ID
        assert created.depth == 2
        assert created.subleg.origin_room_id == ORIGIN_ROOM_ID
        assert created.subleg.route_room_ids == [INITIAL_ROOM_ID]
        assert created.is_leaf
        assert not project.hydronics_valid

        restore = load_latest_topology_stepback_candidate_v1(project.project_dir)
        assert restore.ready, restore.blockers
        assert restore.project_state is not None
        assert restore.project_state.hydronic_topology.to_dict() == original
        assert restore.focus is not None
        assert restore.focus.kind == "branch_subleg"
        assert restore.focus.subleg_id == created_id

        # The newly-created Branch is itself a valid parent, proving the
        # recursive contract without introducing a special second-level type.
        deeper = build_add_branch_subleg_candidate_v1(
            project,
            parent_subleg_id=created_id,
            branch_origin_room_id=INITIAL_ROOM_ID,
            initial_room_id="room-l2b-004",
            branch_label="Nested leaf branch",
        )
        assert deeper.ready, deeper.blockers
        assert not deeper.migration_applied
        _commit(project, deeper, "Create nested leaf branch")

        deeper_position = next(
            item
            for item in build_recursive_subleg_positions_v1(
                project.hydronic_topology
            )
            if item.subleg_id == deeper.created_subleg_id
        )
        assert deeper_position.depth == 3
        assert deeper_position.parent_subleg_id == created_id
        assert deeper_position.kind == BRANCH_SUBLEG_KIND

        stepback_dir = project.project_dir / TOPOLOGY_STEPBACK_DIRECTORY
        assert (stepback_dir / "project.stepback.1.json").is_file()
        assert (stepback_dir / "project.stepback.2.json").is_file()
        assert not (stepback_dir / "project.stepback.3.json").exists()

    print(
        "OK — H-S67-F creates recursively nested Branch sublegs from exact "
        "parent/origin evidence through full-step-back transactions."
    )


if __name__ == "__main__":
    main()
