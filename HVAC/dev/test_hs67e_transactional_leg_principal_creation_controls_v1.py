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
from HVAC.hydronics.topology.topology_creation_candidate_v1 import (
    build_add_leg_with_principal_candidate_v1,
    build_add_principal_subleg_candidate_v1,
    topology_creation_room_ids_v1,
)
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    FOCUS_PRINCIPAL_SUBLEG,
    TOPOLOGY_STEPBACK_DIRECTORY,
    commit_validated_topology_candidate_v1,
)


def _select(combo, identity: str) -> None:
    index = combo.findData(identity)
    assert index >= 0, (identity, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def main() -> None:
    with TemporaryDirectory(prefix="hs67e-") as temporary_directory:
        project = build_hydronic_20_room_multileg_project_v1()
        project.project_dir = Path(temporary_directory)
        project.hydronics_valid = True
        original = project.hydronic_topology.to_dict()

        room_ids = topology_creation_room_ids_v1(project)
        assert len(room_ids) == 20
        assert project.hydronic_topology.heat_source_room_id not in room_ids

        # Candidate construction is non-mutating and includes the safe C
        # migration plus an explicit seed-room move when all rooms are allocated.
        candidate = build_add_leg_with_principal_candidate_v1(
            project,
            initial_room_id="room-l1a-003",
            leg_label="Second upstairs circuit",
            principal_label="North principal",
        )
        assert candidate.ready, candidate.blockers
        assert candidate.migration_applied
        assert candidate.room_reallocated
        assert candidate.leg_id == "leg-003"
        assert candidate.principal_subleg_id == "leg-003-primary-subleg"
        assert project.hydronic_topology.to_dict() == original

        branch_origin = build_add_leg_with_principal_candidate_v1(
            project,
            initial_room_id="room-l1a-002",
        )
        assert not branch_origin.ready
        assert "branch origin" in " ".join(branch_origin.blockers).lower()

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

            context = GuiProjectContext(project_state=project)
            panel = TopologyArrangerPanel()
            adapter = TopologyArrangerPanelAdapter(panel=panel, context=context)

            leg_selector = panel.findChild(
                QComboBox, "topologyArrangerLegSelector"
            )
            principal_selector = panel.findChild(
                QComboBox, "topologyArrangerPrincipalSelector"
            )
            room_selector = panel.findChild(
                QComboBox, "topologyArrangerInitialRoomSelector"
            )
            leg_label = panel.findChild(
                QLineEdit, "topologyArrangerNewLegLabel"
            )
            principal_label = panel.findChild(
                QLineEdit, "topologyArrangerNewPrincipalLabel"
            )
            add_leg = panel.findChild(
                QPushButton, "topologyArrangerAddLegButton"
            )
            add_principal = panel.findChild(
                QPushButton, "topologyArrangerAddPrincipalButton"
            )
            assert all(
                item is not None
                for item in (
                    leg_selector,
                    principal_selector,
                    room_selector,
                    leg_label,
                    principal_label,
                    add_leg,
                    add_principal,
                )
            )

            _select(room_selector, "room-l1a-003")
            leg_label.setText("Second upstairs circuit")
            principal_label.setText("North principal")
            add_leg.click()
        else:
            installed = commit_validated_topology_candidate_v1(
                project,
                candidate.topology,
                action_label="Migrate legacy topology and create leg",
                focus_kind=FOCUS_PRINCIPAL_SUBLEG,
                focus_target_id=candidate.principal_subleg_id,
            )
            assert installed.ready, installed.blockers

        topology = project.hydronic_topology
        assert len(topology.legs) == 3
        created_leg = topology.legs[-1]
        assert created_leg.leg_id == "leg-003"
        assert created_leg.label == "Second upstairs circuit"
        assert len(created_leg.sublegs) == 1
        assert created_leg.sublegs[0].route_room_ids == ["room-l1a-003"]
        if QApplication is not None:
            assert adapter._leg_id == "leg-003"
            assert adapter._principal_subleg_id == "leg-003-primary-subleg"
            assert leg_selector.currentData() == "leg-003"
            assert principal_selector.currentData() == "leg-003-primary-subleg"
            assert "North principal" in panel._title_label.text()
        assert not project.hydronics_valid

        if QApplication is not None:
            _select(room_selector, "room-l2a-003")
            principal_label.setText("South principal")
            add_principal.click()
        else:
            second_candidate = build_add_principal_subleg_candidate_v1(
                project,
                leg_id="leg-003",
                initial_room_id="room-l2a-003",
                principal_label="South principal",
            )
            assert second_candidate.ready, second_candidate.blockers
            installed = commit_validated_topology_candidate_v1(
                project,
                second_candidate.topology,
                action_label="Create principal subleg",
                focus_kind=FOCUS_PRINCIPAL_SUBLEG,
                focus_target_id=second_candidate.principal_subleg_id,
            )
            assert installed.ready, installed.blockers

        # Adapter transaction replaces the topology object, so reacquire it.
        created_leg = project.hydronic_topology.legs[-1]
        assert len(created_leg.sublegs) == 2
        second_principal = created_leg.sublegs[-1]
        assert second_principal.subleg_id == "leg-003-principal-subleg-002"
        assert second_principal.label == "South principal"
        assert second_principal.route_room_ids == ["room-l2a-003"]
        if QApplication is not None:
            assert principal_selector.currentData() == second_principal.subleg_id
            assert "South principal" in panel._title_label.text()

        stepback_dir = project.project_dir / TOPOLOGY_STEPBACK_DIRECTORY
        assert (stepback_dir / "project.stepback.1.json").is_file()
        assert (stepback_dir / "project.stepback.2.json").is_file()
        assert not (stepback_dir / "project.stepback.3.json").exists()

        only_room_blocked = build_add_principal_subleg_candidate_v1(
            project,
            leg_id="leg-003",
            initial_room_id="room-l1a-003",
        )
        assert not only_room_blocked.ready
        assert "only room" in " ".join(only_room_blocked.blockers).lower()

    print(
        "OK — H-S67-E Topology Arranger creates complete Legs and "
        "Principals through validated full-step-back transactions."
    )


if __name__ == "__main__":
    main()
