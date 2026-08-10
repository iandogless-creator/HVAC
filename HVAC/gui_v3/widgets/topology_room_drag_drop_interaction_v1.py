from __future__ import annotations

from dataclasses import dataclass
import json

from PySide6.QtCore import QByteArray, QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


TOPOLOGY_ROOM_MIME_V1 = "application/x-hvacgooee-topology-room-v1"
TOPOLOGY_ROOM_DRAG_SCHEMA_V1 = "topology_room_drag_v1"
ASSIGNED_DRAG_SOURCE = "assigned_topology"
STAGING_DRAG_SOURCE = "unassigned_staging"


@dataclass(frozen=True, slots=True)
class TopologyRoomDragEvidenceV1:
    room_id: str
    source_disposition: str
    source_subleg_id: str = ""


@dataclass(frozen=True, slots=True)
class TopologyRoomDropIntentV1:
    ready: bool
    room_id: str = ""
    target_kind: str = ""
    target_subleg_id: str = ""
    target_order: int = 0
    blockers: tuple[str, ...] = ()


class TopologyRoomDragDropInteractionV1:
    """Stable drag/drop evidence shared by tray and topology schematic."""

    @staticmethod
    def mime_data(
        *,
        room_id: str,
        source_disposition: str,
        source_subleg_id: str = "",
    ) -> QMimeData:
        payload = {
            "schema": TOPOLOGY_ROOM_DRAG_SCHEMA_V1,
            "room_id": str(room_id or "").strip(),
            "source_disposition": str(source_disposition or "").strip(),
            "source_subleg_id": str(source_subleg_id or "").strip(),
        }
        mime_data = QMimeData()
        mime_data.setData(
            TOPOLOGY_ROOM_MIME_V1,
            QByteArray(json.dumps(payload, sort_keys=True).encode("utf-8")),
        )
        return mime_data

    @staticmethod
    def decode(mime_data: QMimeData | None) -> TopologyRoomDragEvidenceV1 | None:
        if mime_data is None or not mime_data.hasFormat(TOPOLOGY_ROOM_MIME_V1):
            return None
        try:
            payload = json.loads(
                bytes(mime_data.data(TOPOLOGY_ROOM_MIME_V1)).decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("schema") != TOPOLOGY_ROOM_DRAG_SCHEMA_V1:
            return None
        room_id = str(payload.get("room_id") or "").strip()
        source_disposition = str(
            payload.get("source_disposition") or ""
        ).strip()
        source_subleg_id = str(payload.get("source_subleg_id") or "").strip()
        if not room_id or source_disposition not in {
            ASSIGNED_DRAG_SOURCE,
            STAGING_DRAG_SOURCE,
        }:
            return None
        if source_disposition == ASSIGNED_DRAG_SOURCE and not source_subleg_id:
            return None
        return TopologyRoomDragEvidenceV1(
            room_id=room_id,
            source_disposition=source_disposition,
            source_subleg_id=source_subleg_id,
        )

    @staticmethod
    def placement_intent(
        evidence: TopologyRoomDragEvidenceV1 | None,
        *,
        target_subleg_id: str,
        target_order: int,
    ) -> TopologyRoomDropIntentV1:
        target_id = str(target_subleg_id or "").strip()
        try:
            order = int(target_order)
        except (TypeError, ValueError):
            order = 0
        if evidence is None:
            return TopologyRoomDropIntentV1(
                ready=False,
                blockers=("Recognised topology room drag evidence is required",),
            )
        if not target_id or order < 1:
            return TopologyRoomDropIntentV1(
                ready=False,
                room_id=evidence.room_id,
                blockers=("Exact target subleg and final room order are required",),
            )
        return TopologyRoomDropIntentV1(
            ready=True,
            room_id=evidence.room_id,
            target_kind="subleg_order",
            target_subleg_id=target_id,
            target_order=order,
        )

    @staticmethod
    def staging_intent(
        evidence: TopologyRoomDragEvidenceV1 | None,
    ) -> TopologyRoomDropIntentV1:
        if evidence is None:
            return TopologyRoomDropIntentV1(
                ready=False,
                blockers=("Recognised topology room drag evidence is required",),
            )
        return TopologyRoomDropIntentV1(
            ready=True,
            room_id=evidence.room_id,
            target_kind="staging",
        )

    @staticmethod
    def start_drag(
        source: QWidget,
        *,
        room_id: str,
        source_disposition: str,
        source_subleg_id: str = "",
        use_source_pixmap: bool = True,
    ) -> None:
        drag = QDrag(source)
        drag.setMimeData(
            TopologyRoomDragDropInteractionV1.mime_data(
                room_id=room_id,
                source_disposition=source_disposition,
                source_subleg_id=source_subleg_id,
            )
        )
        if use_source_pixmap:
            drag.setPixmap(source.grab())
        drag.exec(Qt.MoveAction)


class TopologyRoomDragTokenV1(QLabel):
    """One reusable draggable room token."""

    def __init__(
        self,
        *,
        room_id: str,
        room_label: str,
        source_disposition: str,
        source_subleg_id: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(str(room_label or room_id), parent)
        self.room_id = str(room_id or "")
        self.source_disposition = str(source_disposition or "")
        self.source_subleg_id = str(source_subleg_id or "")
        self._press_position = QPoint()
        self.setObjectName("topologyRoomDragToken")
        self.setToolTip("Drag this room into a subleg position")
        self.setStyleSheet(
            "QLabel { background: #f3f7fc; color: #232323; "
            "border: 1px solid #4b6487; border-radius: 5px; padding: 5px; }"
        )
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._press_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not (event.buttons() & Qt.LeftButton):
            return
        if (
            event.position().toPoint() - self._press_position
        ).manhattanLength() < QApplication.startDragDistance():
            return
        TopologyRoomDragDropInteractionV1.start_drag(
            self,
            room_id=self.room_id,
            source_disposition=self.source_disposition,
            source_subleg_id=self.source_subleg_id,
        )


class TopologyRoomStagingTrayV1(QFrame):
    """Neutral tray containing only currently unassigned rooms."""

    return_to_staging_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("topologyRoomStagingTray")
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame#topologyRoomStagingTray { background: #f7f7f4; "
            "border: 1px dashed #74746c; border-radius: 5px; }"
        )
        self._title = QLabel("Neutral room staging — drag into topology")
        self._title.setObjectName("topologyRoomStagingTitle")
        self._status = QLabel("No unassigned rooms")
        self._status.setObjectName("topologyRoomStagingStatus")
        self._tokens = QHBoxLayout()
        self._tokens.setAlignment(Qt.AlignLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(self._title)
        layout.addLayout(self._tokens)
        layout.addWidget(self._status)

    def set_rooms(self, rooms: list[dict[str, str]]) -> None:
        while self._tokens.count():
            item = self._tokens.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        for room in rooms:
            token = TopologyRoomDragTokenV1(
                room_id=str(room.get("id", "") or ""),
                room_label=str(room.get("label", "") or room.get("id", "")),
                source_disposition=STAGING_DRAG_SOURCE,
            )
            self._tokens.addWidget(token)
        self._status.setText(
            f"{len(rooms)} unassigned room(s)"
            if rooms
            else "No unassigned rooms — drop an assigned room here to stage it"
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if TopologyRoomDragDropInteractionV1.decode(event.mimeData()) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        self.dragEnterEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        intent = TopologyRoomDragDropInteractionV1.staging_intent(
            TopologyRoomDragDropInteractionV1.decode(event.mimeData())
        )
        if not intent.ready:
            event.ignore()
            return
        self.return_to_staging_requested.emit(intent.room_id)
        event.acceptProposedAction()
