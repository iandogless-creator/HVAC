from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget
from HVAC.gui_v3.widgets.topology_room_drag_drop_interaction_v1 import (
    ASSIGNED_DRAG_SOURCE,
    TopologyRoomDragDropInteractionV1,
)


class TopologyArrangerSchematicWidgetV1(QWidget):
    """Recursive topology preview and exact room-order drop surface."""

    room_placement_requested = Signal(str, str, int)

    _ROW_PITCH = 62.0
    _TOP = 70.0
    _COMMON_X = 18.0
    _LEG_X = 160.0
    _SUBLEG_X = 330.0
    _DEPTH_GAP = 150.0
    _ROOM_GAP = 82.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: tuple[dict[str, Any], ...] = ()
        self._heat_source_label = "Boiler / Heat Source"
        self._focus: dict[str, str] = {}
        self._room_hit_rects: dict[str, tuple[QRectF, str]] = {}
        self._subleg_drop_rows: dict[str, tuple[QRectF, tuple[QRectF, ...]]] = {}
        self._pressed_room_id = ""
        self._pressed_subleg_id = ""
        self._press_position = QPoint()
        self._drop_preview: tuple[str, int, float, float] | None = None
        self.setAcceptDrops(True)
        self.setMinimumSize(900, 220)

    def set_topology(
        self,
        rows: list[dict[str, Any]],
        *,
        heat_source_label: str,
        focus: dict[str, str] | None = None,
    ) -> None:
        self._rows = tuple(dict(row) for row in rows)
        self._heat_source_label = str(
            heat_source_label or "Boiler / Heat Source"
        )
        self._focus = {
            "leg_id": str((focus or {}).get("leg_id", "") or ""),
            "subleg_id": str((focus or {}).get("subleg_id", "") or ""),
            "room_id": str((focus or {}).get("room_id", "") or ""),
        }
        maximum_depth = max(
            (int(row.get("depth", 0) or 0) for row in self._rows),
            default=0,
        )
        maximum_rooms = max(
            (len(tuple(row.get("rooms", ()) or ())) for row in self._rows),
            default=0,
        )
        width = int(
            self._SUBLEG_X
            + (maximum_depth * self._DEPTH_GAP)
            + 150
            + (maximum_rooms * self._ROOM_GAP)
            + 70
        )
        height = int(
            self._TOP
            + (max(1, len(self._rows)) * self._ROW_PITCH)
            + 50
        )
        self.setMinimumSize(max(900, width), max(220, height))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QBrush(Qt.white))
        self._room_hit_rects = {}
        self._subleg_drop_rows = {}
        if not self._rows:
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "No canonical topology available",
            )
            return

        row_y = {
            str(row.get("subleg_id", "")): self._TOP + index * self._ROW_PITCH
            for index, row in enumerate(self._rows)
        }
        subleg_rects: dict[str, QRectF] = {}
        leg_rows: dict[str, list[float]] = {}
        leg_labels: dict[str, str] = {}

        for row in self._rows:
            subleg_id = str(row.get("subleg_id", "") or "")
            leg_id = str(row.get("leg_id", "") or "")
            depth = int(row.get("depth", 0) or 0)
            y = row_y[subleg_id]
            x = self._SUBLEG_X + depth * self._DEPTH_GAP
            subleg_rects[subleg_id] = QRectF(x, y - 13, 125, 28)
            leg_rows.setdefault(leg_id, []).append(y)
            leg_labels[leg_id] = str(row.get("leg_label", "") or leg_id)

        heat_rect = QRectF(self._COMMON_X, 10, 120, 28)
        common_rect = QRectF(self._COMMON_X, 48, 120, 28)
        self._draw_node(
            painter,
            heat_rect,
            self._heat_source_label,
            fill=QColor(255, 244, 244),
            border=QColor(160, 65, 65),
        )
        self._draw_node(
            painter,
            common_rect,
            "Common main",
            fill=QColor(230, 240, 255),
            border=QColor(45, 100, 180),
        )
        painter.setPen(QPen(QColor(75, 100, 135), 1.5))
        painter.drawLine(heat_rect.center(), common_rect.center())

        leg_rects: dict[str, QRectF] = {}
        for leg_id, values in leg_rows.items():
            centre_y = (min(values) + max(values)) / 2.0
            leg_rect = QRectF(self._LEG_X, centre_y - 13, 125, 28)
            leg_rects[leg_id] = leg_rect
            focused = leg_id == self._focus.get("leg_id")
            self._draw_node(
                painter,
                leg_rect,
                leg_labels[leg_id],
                focused=focused,
            )
            painter.setPen(QPen(QColor(75, 100, 135), 1.5))
            painter.drawLine(common_rect.right(), centre_y, leg_rect.left(), centre_y)

        for row in self._rows:
            subleg_id = str(row.get("subleg_id", "") or "")
            leg_id = str(row.get("leg_id", "") or "")
            parent_id = str(row.get("parent_subleg_id", "") or "")
            rect = subleg_rects[subleg_id]
            if parent_id and parent_id in subleg_rects:
                source = subleg_rects[parent_id]
            else:
                source = leg_rects[leg_id]
            self._draw_elbow(painter, source, rect)

        for row in self._rows:
            subleg_id = str(row.get("subleg_id", "") or "")
            rect = subleg_rects[subleg_id]
            focused = subleg_id == self._focus.get("subleg_id")
            kind = str(row.get("kind", "") or "").title()
            label = str(row.get("subleg_label", "") or subleg_id)
            self._draw_node(
                painter,
                rect,
                f"{label} [{kind}]",
                focused=focused,
            )
            rooms = tuple(row.get("rooms", ()) or ())
            previous = rect
            room_rects: list[QRectF] = []
            for index, room in enumerate(rooms):
                room_id = str(room.get("id", "") or "")
                room_label = str(room.get("label", "") or room_id)
                room_rect = QRectF(
                    rect.right() + 42 + index * self._ROOM_GAP,
                    rect.top() + 3,
                    66,
                    22,
                )
                painter.setPen(QPen(QColor(85, 100, 120), 1.3))
                painter.drawLine(
                    QPointF(previous.right(), previous.center().y()),
                    QPointF(room_rect.left(), room_rect.center().y()),
                )
                self._draw_node(
                    painter,
                    room_rect,
                    room_label,
                    focused=(room_id == self._focus.get("room_id")),
                    small=True,
                )
                room_rects.append(room_rect)
                self._room_hit_rects[room_id] = (room_rect, subleg_id)
                previous = room_rect
            lane_right = max(
                rect.right() + 80,
                room_rects[-1].right() + 55 if room_rects else rect.right() + 80,
            )
            self._subleg_drop_rows[subleg_id] = (
                QRectF(
                    rect.right() + 8,
                    rect.top() - 15,
                    lane_right - rect.right(),
                    rect.height() + 30,
                ),
                tuple(room_rects),
            )

        if self._drop_preview is not None:
            _subleg_id, _order, marker_x, marker_y = self._drop_preview
            painter.setPen(QPen(QColor(225, 125, 30), 3.0))
            painter.drawLine(
                QPointF(marker_x, marker_y - 18),
                QPointF(marker_x, marker_y + 18),
            )

        painter.setPen(QPen(QColor(95, 95, 95)))
        painter.setFont(QFont("", 8))
        painter.drawText(
            QRectF(18, self.height() - 30, self.width() - 36, 20),
            Qt.AlignLeft | Qt.AlignVCenter,
            "Topology-only preview — no committed pipe or hydraulic evidence",
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._pressed_room_id = ""
        self._pressed_subleg_id = ""
        if event.button() == Qt.LeftButton:
            hit = self._room_at(event.position())
            if hit is not None:
                self._pressed_room_id, self._pressed_subleg_id = hit
                self._press_position = event.position().toPoint()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self._pressed_room_id or not (event.buttons() & Qt.LeftButton):
            return
        if (
            event.position().toPoint() - self._press_position
        ).manhattanLength() < QApplication.startDragDistance():
            return
        room_id = self._pressed_room_id
        subleg_id = self._pressed_subleg_id
        self._pressed_room_id = ""
        self._pressed_subleg_id = ""
        TopologyRoomDragDropInteractionV1.start_drag(
            self,
            room_id=room_id,
            source_disposition=ASSIGNED_DRAG_SOURCE,
            source_subleg_id=subleg_id,
            use_source_pixmap=False,
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if TopologyRoomDragDropInteractionV1.decode(event.mimeData()) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        target = self._drop_target_at(event.position())
        if (
            TopologyRoomDragDropInteractionV1.decode(event.mimeData()) is None
            or target is None
        ):
            self._drop_preview = None
            self.update()
            event.ignore()
            return
        self._drop_preview = target
        self.update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._drop_preview = None
        self.update()
        event.accept()

    def dropEvent(self, event) -> None:  # noqa: N802
        evidence = TopologyRoomDragDropInteractionV1.decode(event.mimeData())
        target = self._drop_target_at(event.position())
        self._drop_preview = None
        self.update()
        if target is None:
            event.ignore()
            return
        subleg_id, order, _marker_x, _marker_y = target
        intent = TopologyRoomDragDropInteractionV1.placement_intent(
            evidence,
            target_subleg_id=subleg_id,
            target_order=order,
        )
        if not intent.ready:
            event.ignore()
            return
        self.room_placement_requested.emit(
            intent.room_id,
            intent.target_subleg_id,
            intent.target_order,
        )
        event.acceptProposedAction()

    def _room_at(self, point: QPointF) -> tuple[str, str] | None:
        return next(
            (
                (room_id, subleg_id)
                for room_id, (rect, subleg_id) in self._room_hit_rects.items()
                if rect.contains(point)
            ),
            None,
        )

    def _drop_target_at(
        self,
        point: QPointF,
    ) -> tuple[str, int, float, float] | None:
        for subleg_id, (lane, room_rects) in self._subleg_drop_rows.items():
            if not lane.contains(point):
                continue
            for index, room_rect in enumerate(room_rects):
                if point.x() < room_rect.center().x():
                    marker_x = room_rect.left() - 10
                    return subleg_id, index + 1, marker_x, room_rect.center().y()
            if room_rects:
                marker_x = room_rects[-1].right() + 10
                marker_y = room_rects[-1].center().y()
            else:
                marker_x = lane.left() + 15
                marker_y = lane.center().y()
            return subleg_id, len(room_rects) + 1, marker_x, marker_y
        return None

    @staticmethod
    def _draw_elbow(painter: QPainter, source: QRectF, target: QRectF) -> None:
        painter.setPen(QPen(QColor(75, 100, 135), 1.5))
        start = QPointF(source.right(), source.center().y())
        end = QPointF(target.left(), target.center().y())
        middle_x = (start.x() + end.x()) / 2.0
        painter.drawLine(start, QPointF(middle_x, start.y()))
        painter.drawLine(
            QPointF(middle_x, start.y()),
            QPointF(middle_x, end.y()),
        )
        painter.drawLine(QPointF(middle_x, end.y()), end)

    @staticmethod
    def _draw_node(
        painter: QPainter,
        rect: QRectF,
        text: str,
        *,
        focused: bool = False,
        fill: QColor | None = None,
        border: QColor | None = None,
        small: bool = False,
    ) -> None:
        if focused:
            fill = QColor(246, 183, 92)
            border = QColor(105, 60, 15)
        painter.setPen(QPen(border or QColor(75, 100, 135), 2.2 if focused else 1.2))
        painter.setBrush(QBrush(fill or QColor(243, 247, 252)))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QPen(QColor(35, 35, 35)))
        painter.setFont(QFont("", 7 if small else 8))
        painter.drawText(rect.adjusted(3, 0, -3, 0), Qt.AlignCenter, text)
