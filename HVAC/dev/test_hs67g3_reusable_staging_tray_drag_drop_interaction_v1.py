from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication, QLabel
except ModuleNotFoundError:
    QPointF = QApplication = QLabel = None

from HVAC.core.room_state import RoomGeometryV1, RoomStateV1
from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)
from HVAC.hydronics.topology.topology_unassigned_room_inventory_v1 import (
    build_topology_unassigned_room_inventory_v1,
)
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    TOPOLOGY_STEPBACK_DIRECTORY,
)


STAGED_ROOM_ID = "room-future-001"


def main() -> None:
    if QApplication is None:
        root = Path("HVAC")
        interaction_source = (
            root
            / "gui_v3/widgets/topology_room_drag_drop_interaction_v1.py"
        ).read_text(encoding="utf-8")
        schematic_source = (
            root
            / "gui_v3/widgets/topology_arranger_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        panel_source = (
            root / "gui_v3/panels/topology_arranger_panel.py"
        ).read_text(encoding="utf-8")
        adapter_source = (
            root / "gui_v3/adapters/topology_arranger_panel_adapter.py"
        ).read_text(encoding="utf-8")
        assert "class TopologyRoomDragDropInteractionV1" in interaction_source
        assert "class TopologyRoomStagingTrayV1" in interaction_source
        assert "TOPOLOGY_ROOM_MIME_V1" in interaction_source
        assert "room_placement_requested = Signal(str, str, int)" in (
            schematic_source
        )
        assert "return_room_to_staging_requested = Signal(str)" in panel_source
        assert "build_place_topology_room_candidate_v1" in adapter_source
        assert "build_return_topology_room_to_staging_candidate_v1" in (
            adapter_source
        )
        print(
            "OK — H-S67-G3 provides a reusable neutral staging tray and "
            "exact drag/drop topology interaction over transactional G2 "
            "authority (source boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.adapters.topology_arranger_panel_adapter import (
        TopologyArrangerPanelAdapter,
    )
    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.topology_arranger_panel import TopologyArrangerPanel
    from HVAC.gui_v3.widgets.topology_arranger_schematic_widget_v1 import (
        TopologyArrangerSchematicWidgetV1,
    )
    from HVAC.gui_v3.widgets.topology_room_drag_drop_interaction_v1 import (
        ASSIGNED_DRAG_SOURCE,
        STAGING_DRAG_SOURCE,
        TopologyRoomDragDropInteractionV1,
        TopologyRoomDragTokenV1,
        TopologyRoomStagingTrayV1,
    )

    app = QApplication.instance() or QApplication([])
    del app

    staged_mime = TopologyRoomDragDropInteractionV1.mime_data(
        room_id=STAGED_ROOM_ID,
        source_disposition=STAGING_DRAG_SOURCE,
    )
    staged_evidence = TopologyRoomDragDropInteractionV1.decode(staged_mime)
    assert staged_evidence is not None
    assert staged_evidence.room_id == STAGED_ROOM_ID
    placement_intent = TopologyRoomDragDropInteractionV1.placement_intent(
        staged_evidence,
        target_subleg_id="leg-001-primary-subleg",
        target_order=2,
    )
    assert placement_intent.ready
    assert placement_intent.target_order == 2

    assigned_mime = TopologyRoomDragDropInteractionV1.mime_data(
        room_id="room-l1a-001",
        source_disposition=ASSIGNED_DRAG_SOURCE,
        source_subleg_id="leg-001-primary-subleg",
    )
    assigned_evidence = TopologyRoomDragDropInteractionV1.decode(assigned_mime)
    staging_intent = TopologyRoomDragDropInteractionV1.staging_intent(
        assigned_evidence
    )
    assert staging_intent.ready and staging_intent.target_kind == "staging"

    with TemporaryDirectory(prefix="hs67g3-") as temporary_directory:
        project = build_hydronic_20_room_multileg_project_v1()
        project.project_dir = Path(temporary_directory)
        project.rooms[STAGED_ROOM_ID] = RoomStateV1(
            room_id=STAGED_ROOM_ID,
            name="Future Study",
            geometry=RoomGeometryV1(
                length_m=3.0,
                width_m=2.5,
                height_m=2.4,
            ),
        )
        panel = TopologyArrangerPanel()
        adapter = TopologyArrangerPanelAdapter(
            panel=panel,
            context=GuiProjectContext(project_state=project),
        )
        tray = panel.findChild(
            TopologyRoomStagingTrayV1,
            "topologyRoomStagingTray",
        )
        schematic = panel.findChild(
            TopologyArrangerSchematicWidgetV1,
            "topologyArrangerSchematicWidget",
        )
        result_label = panel.findChild(
            QLabel,
            "topologyArrangerCreationResultLabel",
        )
        assert tray is not None and schematic is not None and result_label is not None
        tokens = tray.findChildren(TopologyRoomDragTokenV1)
        assert [token.room_id for token in tokens] == [STAGED_ROOM_ID]

        schematic.grab()
        first_room_rect = schematic._room_hit_rects["room-l1a-001"][0]
        drop_target = schematic._drop_target_at(
            QPointF(first_room_rect.center().x() - 1, first_room_rect.center().y())
        )
        assert drop_target is not None
        assert drop_target[:2] == ("leg-001-primary-subleg", 1)

        panel.room_placement_requested.emit(
            STAGED_ROOM_ID,
            "leg-001-primary-subleg",
            2,
        )
        inventory = build_topology_unassigned_room_inventory_v1(project)
        assert inventory.require_room(STAGED_ROOM_ID).subleg_id == (
            "leg-001-primary-subleg"
        )
        assert inventory.require_room(STAGED_ROOM_ID).route_order == 2
        assert not project.hydronics_valid
        assert adapter._topology_focus_room_id == STAGED_ROOM_ID
        assert "Future Study → leg-001-primary-subleg at order 2" in (
            result_label.text()
        )
        assert not tray.findChildren(TopologyRoomDragTokenV1)

        panel.room_placement_requested.emit(
            "room-l1a-002",
            "leg-002-primary-subleg",
            1,
        )
        assert "dependent Branch" in panel._status_label.text()

        panel.return_room_to_staging_requested.emit(STAGED_ROOM_ID)
        inventory = build_topology_unassigned_room_inventory_v1(project)
        assert STAGED_ROOM_ID in inventory.staging_room_ids
        assert "Future Study → neutral room staging" in result_label.text()
        tokens = tray.findChildren(TopologyRoomDragTokenV1)
        assert [token.room_id for token in tokens] == [STAGED_ROOM_ID]

        stepback_root = Path(temporary_directory) / TOPOLOGY_STEPBACK_DIRECTORY
        assert (stepback_root / "project.stepback.1.json").is_file()
        assert (stepback_root / "project.stepback.2.json").is_file()

    print(
        "OK — H-S67-G3 provides a reusable neutral staging tray and exact "
        "drag/drop topology interaction over transactional G2 authority."
    )


if __name__ == "__main__":
    main()
