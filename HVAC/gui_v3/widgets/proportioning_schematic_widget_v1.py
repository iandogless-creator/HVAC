# ======================================================================
# HVAC/gui_v3/widgets/proportioning_schematic_widget_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


# ======================================================================
# Internal layout DTO
# ======================================================================

@dataclass(frozen=True, slots=True)
class _NodeBox:
    node_id: str
    label: str
    role: str
    rect: QRectF


# ======================================================================
# ProportioningSchematicWidgetV1
# ======================================================================

class ProportioningSchematicWidgetV1(QWidget):
    """
    Read-only proportioning schematic widget.

    Authority
    ---------
    Display only.

    It does not:
    • access ProjectState
    • mutate engineering data
    • size pipework
    • calculate pressure loss
    • select pumps
    • balance branches

    Input authority is a ProportioningSchematicV1 DTO.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._schematic: Any | None = None

        self.setMinimumHeight(260)
        self.setMinimumWidth(620)
        self.setMouseTracking(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_schematic(self, schematic: Any | None) -> None:
        """
        Replace the currently displayed schematic DTO.

        Replace-only semantics.
        No interpretation beyond presentation layout.
        """
        self._schematic = schematic
        self.update()

    def clear(self) -> None:
        self._schematic = None
        self.update()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self._paint_background(painter)

        if self._schematic is None:
            self._paint_empty(painter)
            return

        nodes = list(getattr(self._schematic, "nodes", []) or [])
        edges = list(getattr(self._schematic, "edges", []) or [])

        if not nodes:
            self._paint_empty(painter)
            return

        node_boxes = self._layout_nodes(nodes)

        self._paint_title(painter)
        self._paint_edges(painter, edges, node_boxes)
        self._paint_nodes(painter, node_boxes)
        self._paint_footer(painter)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _layout_nodes(self, nodes: list[Any]) -> dict[str, _NodeBox]:
        """
        Convert schematic nodes into presentation rectangles.

        H-S2 layout rule:
        • lane  0 = main spine
        • lane -1 = non-index branch terminals above
        • lane  1 = unresolved / no-emitter below
        """

        boxes: dict[str, _NodeBox] = {}

        margin_x = 24.0
        node_w = 132.0
        node_h = 34.0
        gap_x = 30.0

        main_y = 128.0
        lane_gap_y = 72.0

        sorted_nodes = sorted(
            nodes,
            key=lambda node: (
                int(getattr(node, "lane", 0)),
                int(getattr(node, "order", 0)),
                str(getattr(node, "label", "")),
            ),
        )

        for node in sorted_nodes:
            node_id = str(getattr(node, "node_id", ""))
            label = str(getattr(node, "label", "") or node_id)
            role = str(getattr(node, "role", "") or "")
            lane = int(getattr(node, "lane", 0))
            order = int(getattr(node, "order", 0))

            # Main spine uses order directly left-to-right.
            # Side lanes start around Common main unless later upgraded.
            if lane == 0:
                x = margin_x + (order * (node_w + gap_x))
            else:
                x = margin_x + ((order + 1) * (node_w + gap_x))

            y = main_y + (lane * lane_gap_y)

            rect = QRectF(x, y, node_w, node_h)

            boxes[node_id] = _NodeBox(
                node_id=node_id,
                label=label,
                role=role,
                rect=rect,
            )

        return boxes

    # ------------------------------------------------------------------
    # Painting helpers
    # ------------------------------------------------------------------

    def _paint_background(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QBrush(Qt.white))

    def _paint_empty(self, painter: QPainter) -> None:
        painter.setPen(QPen(Qt.gray))
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "No proportioning schematic available",
        )

    def _paint_title(self, painter: QPainter) -> None:
        title = str(
            getattr(
                self._schematic,
                "title",
                "Proportioning schematic",
            )
            or "Proportioning schematic"
        )

        painter.save()
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(Qt.black))
        painter.drawText(
            QRectF(12.0, 8.0, float(self.width()) - 24.0, 24.0),
            Qt.AlignLeft | Qt.AlignVCenter,
            title,
        )
        painter.restore()

    def _paint_nodes(
        self,
        painter: QPainter,
        node_boxes: dict[str, _NodeBox],
    ) -> None:
        for box in node_boxes.values():
            self._paint_node(painter, box)

    def _paint_node(self, painter: QPainter, box: _NodeBox) -> None:
        role = box.role

        painter.save()

        pen = QPen(Qt.black, 1.0)
        brush = QBrush(Qt.lightGray)

        if role == "HEAT_SOURCE":
            pen = QPen(Qt.darkRed, 1.3)
        elif role == "COMMON_MAIN":
            pen = QPen(Qt.darkBlue, 1.3)
        elif role == "SELECTED_INDEX_ROUTE":
            pen = QPen(Qt.darkGreen, 1.2)
        elif role == "NON_INDEX_BRANCH_TERMINAL":
            pen = QPen(Qt.darkMagenta, 1.2)
        elif role == "NO_EMITTER_UNRESOLVED":
            pen = QPen(Qt.darkYellow, 1.2)

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRoundedRect(box.rect, 6.0, 6.0)

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(Qt.black))

        painter.drawText(
            box.rect.adjusted(6.0, 2.0, -6.0, -2.0),
            Qt.AlignCenter | Qt.TextWordWrap,
            box.label,
        )

        painter.restore()

    def _paint_edges(
        self,
        painter: QPainter,
        edges: list[Any],
        node_boxes: dict[str, _NodeBox],
    ) -> None:
        for edge in edges:
            from_id = str(getattr(edge, "from_node_id", ""))
            to_id = str(getattr(edge, "to_node_id", ""))

            from_box = node_boxes.get(from_id)
            to_box = node_boxes.get(to_id)

            if from_box is None or to_box is None:
                continue

            self._paint_edge(painter, edge, from_box, to_box)

    def _paint_edge(
        self,
        painter: QPainter,
        edge: Any,
        from_box: _NodeBox,
        to_box: _NodeBox,
    ) -> None:
        role = str(getattr(edge, "role", "") or "")
        flow_label = str(getattr(edge, "flow_label", "") or "")

        start = self._edge_start(from_box.rect, to_box.rect)
        end = self._edge_end(from_box.rect, to_box.rect)

        painter.save()

        pen = QPen(Qt.darkGray, 1.6)

        if role == "COMMON_MAIN":
            pen = QPen(Qt.darkBlue, 2.0)
        elif role == "SELECTED_INDEX_ROUTE":
            pen = QPen(Qt.darkGreen, 1.8)
        elif role == "NON_INDEX_BRANCH_TERMINAL":
            pen = QPen(Qt.darkMagenta, 1.8)
        elif role == "NO_EMITTER_UNRESOLVED":
            pen = QPen(Qt.darkYellow, 1.5)

        painter.setPen(pen)
        painter.drawLine(start, end)

        self._paint_arrow_head(painter, start, end)

        if flow_label and flow_label != "—":
            self._paint_edge_label(painter, start, end, flow_label)

        painter.restore()

    def _edge_start(self, from_rect: QRectF, to_rect: QRectF) -> QPointF:
        from_center = from_rect.center()
        to_center = to_rect.center()

        if abs(to_center.y() - from_center.y()) > abs(to_center.x() - from_center.x()):
            if to_center.y() > from_center.y():
                return QPointF(from_center.x(), from_rect.bottom())
            return QPointF(from_center.x(), from_rect.top())

        if to_center.x() >= from_center.x():
            return QPointF(from_rect.right(), from_center.y())

        return QPointF(from_rect.left(), from_center.y())

    def _edge_end(self, from_rect: QRectF, to_rect: QRectF) -> QPointF:
        from_center = from_rect.center()
        to_center = to_rect.center()

        if abs(to_center.y() - from_center.y()) > abs(to_center.x() - from_center.x()):
            if to_center.y() > from_center.y():
                return QPointF(to_center.x(), to_rect.top())
            return QPointF(to_center.x(), to_rect.bottom())

        if to_center.x() >= from_center.x():
            return QPointF(to_rect.left(), to_center.y())

        return QPointF(to_rect.right(), to_center.y())

    def _paint_arrow_head(
        self,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
    ) -> None:
        dx = end.x() - start.x()
        dy = end.y() - start.y()

        if abs(dx) >= abs(dy):
            direction = 1.0 if dx >= 0 else -1.0
            points = [
                QPointF(end.x(), end.y()),
                QPointF(end.x() - (8.0 * direction), end.y() - 5.0),
                QPointF(end.x() - (8.0 * direction), end.y() + 5.0),
            ]
        else:
            direction = 1.0 if dy >= 0 else -1.0
            points = [
                QPointF(end.x(), end.y()),
                QPointF(end.x() - 5.0, end.y() - (8.0 * direction)),
                QPointF(end.x() + 5.0, end.y() - (8.0 * direction)),
            ]

        painter.setBrush(QBrush(painter.pen().color()))
        painter.drawPolygon(QPolygonF(points))

    def _paint_edge_label(
        self,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        label: str,
    ) -> None:
        mid_x = (start.x() + end.x()) / 2.0
        mid_y = (start.y() + end.y()) / 2.0

        rect = QRectF(mid_x - 42.0, mid_y - 18.0, 84.0, 16.0)

        painter.save()

        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QPen(Qt.darkGray))
        painter.drawText(rect, Qt.AlignCenter, label)

        painter.restore()

    def _paint_footer(self, painter: QPainter) -> None:
        basis = str(getattr(self._schematic, "basis", "") or "")

        if not basis:
            return

        painter.save()
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(Qt.darkGray))
        painter.drawText(
            QRectF(
                12.0,
                float(self.height()) - 28.0,
                float(self.width()) - 24.0,
                20.0,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            basis,
        )
        painter.restore()