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
    is_index_node: bool = False

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

        natural_width = self._natural_width()
        self.setMinimumWidth(natural_width)
        self.resize(max(self.width(), natural_width), self.height())

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
                is_index_node=getattr(node, "is_index_node", False),
            )

        return boxes

    def clear(self) -> None:
        self._schematic = None
        self.setMinimumWidth(620)
        self.update()

    def _natural_width(self) -> int:
        """
        Compute natural schematic width from node count/order.

        This allows the parent scroll area to provide horizontal scrolling
        instead of forcing the schematic to compress or clip.
        """
        if self._schematic is None:
            return 620

        nodes = list(getattr(self._schematic, "nodes", []) or [])

        if not nodes:
            return 620

        max_order = 0

        for node in nodes:
            try:
                order = int(getattr(node, "order", 0))
            except (TypeError, ValueError):
                order = 0

            max_order = max(max_order, order)

        margin_x = 24
        node_w = 132
        gap_x = 30

        # +2 gives breathing room after the final node.
        return int((margin_x * 2) + ((max_order + 2) * (node_w + gap_x)))

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

        if getattr(box, "is_index_node", False):
            self._paint_index_flag(painter, box.rect)
        painter.restore()

    def _paint_index_flag(self, painter: QPainter, rect: QRectF) -> None:
        """
        Paint a small reddish index flag attached to the node.

        Display-only annotation:
        - does not alter room label
        - does not alter route authority
        - marks current/selected index node
        """

        painter.save()

        pole_x = rect.right() - 14.0
        pole_y = rect.top() + 6.0
        pole_h = 15.0
        flag_w = 12.0
        flag_h = 8.0

        painter.setPen(QPen(Qt.darkRed, 1.0))
        painter.setBrush(QBrush(Qt.darkRed))

        painter.drawLine(
            QPointF(pole_x, pole_y),
            QPointF(pole_x, pole_y + pole_h),
        )

        flag = QPolygonF(
            [
                QPointF(pole_x, pole_y),
                QPointF(pole_x + flag_w, pole_y + 3.0),
                QPointF(pole_x, pole_y + flag_h),
            ]
        )

        painter.drawPolygon(flag)

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

        if self._is_selected_route_entry_edge(edge):
            self._paint_selected_route_entry_connector(
                painter,
                edge,
                from_box,
                to_box,
            )
            return

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

    def _is_selected_route_entry_edge(self, edge: Any) -> bool:
        """
        Return True only for the synthetic schematic connector from
        common main into the selected index route.

        This connector is projection/display only. It must not catch
        ordinary selected-index-route legs or sublegs.
        """
        edge_id = str(getattr(edge, "edge_id", "") or "")

        return edge_id == "edge-common-main-selected-route-entry"

    def _paint_selected_route_entry_connector(
        self,
        painter: QPainter,
        edge: Any,
        from_box: _NodeBox,
        to_box: _NodeBox,
    ) -> None:
        """
        Paint the selected route entry as a schematic connector.

        H-S4d visual rule:
        • the connector shows that the selected index route is fed from
          the common main
        • it is not a CAD pipe route
        • it is not a calculated branch attachment point
        """
        painter.save()

        pen = QPen(Qt.darkGreen, 1.6)
        painter.setPen(pen)

        from_rect = from_box.rect
        to_rect = to_box.rect

        start = QPointF(from_rect.center().x(), from_rect.bottom())
        drop_y = max(from_rect.bottom(), to_rect.bottom()) + 42.0

        p1 = QPointF(start.x(), drop_y)
        p2 = QPointF(to_rect.center().x(), drop_y)
        end = QPointF(to_rect.center().x(), to_rect.bottom())

        painter.drawLine(start, p1)
        painter.drawLine(p1, p2)
        painter.drawLine(p2, end)

        # Draftsman-style schematic break marker on the connector.
        break_x = (p1.x() + p2.x()) / 2.0
        painter.drawLine(
            QPointF(break_x - 10.0, drop_y - 4.0),
            QPointF(break_x - 4.0, drop_y + 4.0),
        )
        painter.drawLine(
            QPointF(break_x + 2.0, drop_y - 4.0),
            QPointF(break_x + 8.0, drop_y + 4.0),
        )

        # Arrow into the selected route node from below.
        self._paint_arrow_head(
            painter,
            QPointF(end.x(), end.y() + 16.0),
            end,
        )
        flow_label = str(getattr(edge, "flow_label", "") or "")

        if flow_label and flow_label != "—":
            mid_x = (p1.x() + p2.x()) / 2.0

            rect = QRectF(
                mid_x - 48.0,
                drop_y - 30.0,
                96.0,
                20.0,
            )

            painter.setPen(QPen(Qt.darkGray, 1.0))
            painter.drawLine(
                QPointF(rect.center().x(), rect.bottom()),
                QPointF(mid_x, drop_y),
            )

            painter.setPen(QPen(Qt.black))
            painter.setBrush(QBrush(Qt.white))
            painter.drawRoundedRect(rect, 4.0, 4.0)
            painter.drawText(
                rect.adjusted(4.0, 0.0, -4.0, 0.0),
                Qt.AlignCenter | Qt.AlignVCenter,
                flow_label,
            )

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
        """
        Paint a readable flow callout near an edge.

        H-S4c visual rule:
        • flow labels are callouts, not inline pipe text
        • the callout points to the pipe section
        • keep the drawing clean and avoid node overlap
        """
        mid_x = (start.x() + end.x()) / 2.0
        mid_y = (start.y() + end.y()) / 2.0

        painter.save()

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        metrics = painter.fontMetrics()

        padding_x = 8.0
        min_w = 96.0
        max_w = 150.0

        text_w = float(metrics.horizontalAdvance(label))
        label_w = max(min_w, min(max_w, text_w + (padding_x * 2.0)))
        label_h = 20.0

        dx = end.x() - start.x()
        dy = end.y() - start.y()

        # Horizontal pipe section:
        # label above pipe, pointer down to pipe.
        if abs(dx) >= abs(dy):
            rect = QRectF(
                mid_x - (label_w / 2.0),
                mid_y - 44.0,
                label_w,
                label_h,
            )
            pointer_start = QPointF(rect.center().x(), rect.bottom())
            pointer_end = QPointF(mid_x, mid_y - 2.0)

        # Vertical / branch section:
        # label to the side, pointer back to branch.
        else:
            rect = QRectF(
                mid_x + 12.0,
                mid_y - (label_h / 2.0),
                label_w,
                label_h,
            )
            pointer_start = QPointF(rect.left(), rect.center().y())
            pointer_end = QPointF(mid_x + 2.0, mid_y)

        painter.setPen(QPen(Qt.darkGray, 1.0))
        painter.drawLine(pointer_start, pointer_end)

        painter.setPen(QPen(Qt.black))
        painter.setBrush(QBrush(Qt.white))
        painter.drawRoundedRect(rect, 4.0, 4.0)

        text_rect = rect.adjusted(4.0, 0.0, -4.0, 0.0)
        elided = metrics.elidedText(
            label,
            Qt.ElideRight,
            int(text_rect.width()),
        )

        painter.drawText(
            text_rect,
            Qt.AlignCenter | Qt.AlignVCenter,
            elided,
        )

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