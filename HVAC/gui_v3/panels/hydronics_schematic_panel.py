# ======================================================================
# HVAC/gui_v3/panels/hydronics_schematic_panel.py
# ======================================================================

"""
HVACgooee — GUI v3
Hydronics Schematic Panel — Phase D

Read-only schematic rendering driven by a schematic DTO.

• No authority
• No ProjectState access
• No physics
• Hover via floating inspector panel
"""

from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QRectF,
    QPoint,
    QPointF,
)

from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QFont,
    QPolygonF,
)

from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
)

# ======================================================================
# Floating Inspector (Phase D)
# ======================================================================

class _HoverInspector(QFrame):
    """
    Floating read-only inspector for hover payloads.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.setWindowFlags(Qt.ToolTip)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            """
            QFrame {
                background: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 6px;
            }
            QLabel {
                padding: 6px;
            }
            """
        )

        self._label = QLabel(self)
        self._label.setTextFormat(Qt.RichText)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._label)

        self.hide()

    def show_payload(self, html: str, global_pos: QPoint) -> None:
        self._label.setText(html)
        self.adjustSize()
        self.move(global_pos + QPoint(12, 12))
        self.show()

    def hide_payload(self) -> None:
        self.hide()


# ======================================================================
# HydronicsSchematicPanel
# ======================================================================

class HydronicsSchematicPanel(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._build_ui()
        self.render_empty_state()

        self.setFocusPolicy(Qt.NoFocus)
        self.setContextMenuPolicy(Qt.NoContextMenu)

        self.setMinimumSize(400, 260)

        # Current schematic DTO (or None)
        self._schematic: Optional[HydronicsSchematicDTO] = None

        # Floating inspector
        self._inspector = _HoverInspector(self)

    # ------------------------------------------------------------------
    # Adapter ingress (PRIVATE)
    # ------------------------------------------------------------------

    def _set_schematic(self, dto: HydronicsSchematicDTO) -> None:
        """
        Replace the current schematic DTO and repaint.

        Phase C/D contract:
        - Replace-only semantics
        - No validation
        - No interpretation
        """
        self._schematic = dto
        self.update()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Hydronics schematic")
        title.setStyleSheet("font-weight:600; padding:6px;")
        layout.addWidget(title)

        layout.addStretch(1)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self._paint_background(painter)

        if self._schematic is None:
            self._paint_empty(painter)
            return

        self._paint_edges(painter, self._schematic.edges)
        self._paint_nodes(painter, self._schematic.nodes)
        self._paint_labels(painter, self._schematic.annotations)

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
            "No hydronics schematic available",
        )

    def _paint_nodes(
            self,
            painter: QPainter,
            nodes: list[SchematicNodeDTO],
    ) -> None:
        pen = QPen(Qt.black)
        brush = QBrush(Qt.lightGray)

        painter.setPen(pen)
        painter.setBrush(brush)

        for node in nodes:
            shape = getattr(node, "shape", "CIRCLE")
            orientation = getattr(node, "orientation_deg", None)
            self._draw_node_shape(
                painter,
                x=node.x,
                y=node.y,
                shape=shape,
                orientation_deg=orientation,
            )


            # Label
            painter.drawText(
                QRectF(node.x - 50, node.y + 18, 100, 20),
                Qt.AlignCenter,
                node.id,
            )

    def _paint_edges(
        self,
        painter: QPainter,
        edges: list[SchematicEdgeDTO],
    ) -> None:
        pen = QPen(Qt.darkGray, 2.0)
        painter.setPen(pen)

        node_pos = {
            node.id: (node.x, node.y)
            for node in (self._schematic.nodes if self._schematic else [])
        }

        for edge in edges:
            p1 = node_pos.get(edge.from_node_id)
            p2 = node_pos.get(edge.to_node_id)
            if not p1 or not p2:
                continue

            painter.drawLine(p1[0], p1[1], p2[0], p2[1])

    def _paint_labels(
        self,
        painter: QPainter,
        labels: list[SchematicLabelDTO],
    ) -> None:
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QPen(Qt.darkBlue))

        for label in labels:
            painter.drawText(label.x, label.y, label.text)

    # ------------------------------------------------------------------
    # Shape rendering (Phase E)
    # ------------------------------------------------------------------

    def _draw_node_shape(
            self,
            painter: QPainter,
            *,
            x: float,
            y: float,
            shape: str,
            orientation_deg: float | None = None,
            size: float = 14.0,
    ) -> None:

        """
        Draw a schematic node shape.

        Phase E rules:
        - Pure rendering
        - No interpretation
        - Shape is a hint, not authority
        """

        if shape == "CIRCLE":
            # Outer pump / node body
            painter.drawEllipse(
                QRectF(x - size, y - size, size * 2, size * 2)
            )

            # Optional inner orientation marker (Phase E)
            if orientation_deg is not None:
                painter.save()
                painter.translate(x, y)
                painter.rotate(orientation_deg)

                half = size * 0.55
                points = [
                    QPointF(half, 0.0),
                    QPointF(-half * 0.6, -half),
                    QPointF(-half * 0.6, half),
                ]
                painter.drawPolygon(points)

                painter.restore()


        elif shape == "RECT":
            painter.drawRect(
                QRectF(x - size, y - size, size * 2, size * 2)
            )

        elif shape == "OBLONG":
            painter.drawRoundedRect(
                QRectF(x - size * 1.6, y - size, size * 3.2, size * 2),
                6.0,
                6.0,
            )

        elif shape == "TRIANGLE":
            half = size
            points = [
                QPointF(x, y - half),
                QPointF(x - half, y + half),
                QPointF(x + half, y + half),
            ]
            painter.drawPolygon(points)

        else:
            # Defensive fallback
            painter.drawEllipse(
                QRectF(x - size, y - size, size * 2, size * 2)
            )

    # ------------------------------------------------------------------
    # Hover formatting (presentation-only)
    # ------------------------------------------------------------------

    def _format_node_hover(self, hover: NodeHoverDTO) -> str:
        lines = [f"<b>{hover.title}</b>"]

        if hover.qf_w is not None:
            lines.append(f"Heat demand: {hover.qf_w:.0f} W")

        if hover.qt_w is not None:
            lines.append(f"Supplied heat: {hover.qt_w:.0f} W")

        if hover.flow_kg_s is not None:
            lines.append(f"Flow: {hover.flow_kg_s:.3f} kg/s")

        if hover.target_cv is not None:
            lines.append(f"Target Cv: {hover.target_cv:.2f}")

        return "<br>".join(lines)

    def _format_edge_hover(self, hover: EdgeHoverDTO) -> str:
        lines = [f"<b>{hover.pipe_ref}</b>"]

        if hover.size_mm is not None:
            lines.append(f"Size: {hover.size_mm:.0f} mm")

        if hover.length_m is not None:
            lines.append(f"Length: {hover.length_m:.1f} m")

        if hover.flow_kg_s is not None:
            lines.append(f"Flow: {hover.flow_kg_s:.3f} kg/s")

        if hover.velocity_m_s is not None:
            lines.append(f"Velocity: {hover.velocity_m_s:.2f} m/s")

        if hover.dp_pa is not None:
            lines.append(f"Δp: {hover.dp_pa:.0f} Pa")

        return "<br>".join(lines)

    # ------------------------------------------------------------------
    # Mouse hover handling (Phase D)
    # ------------------------------------------------------------------

    def mouseMoveEvent(self, event) -> None:
        if self._schematic is None:
            self._inspector.hide_payload()
            event.ignore()
            return

        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()

        # Nodes first (priority)
        for node in self._schematic.nodes:
            dx = pos.x() - node.x
            dy = pos.y() - node.y
            if dx * dx + dy * dy < 12 * 12 and node.hover:
                self._inspector.show_payload(
                    self._format_node_hover(node.hover),
                    global_pos,
                )
                return

        # Edges (Phase D: coarse)
        for edge in self._schematic.edges:
            if edge.hover:
                self._inspector.show_payload(
                    self._format_edge_hover(edge.hover),
                    global_pos,
                )
                return

        self._inspector.hide_payload()
        event.ignore()

    def render_empty_state(self) -> None:
        """
        Phase B:
        Render a safe empty schematic state.
        """
        self._schematic = None
        self.update()

    # ------------------------------------------------------------------
    # Input suppression
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def keyReleaseEvent(self, event) -> None:  # noqa: N802
        event.ignore()
