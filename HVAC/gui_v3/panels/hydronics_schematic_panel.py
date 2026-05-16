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
from typing import Optional
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolButton,
)

from HVAC.gui_v3.schematic.dto import (
    HydronicsSchematicDTO,
    SchematicNodeDTO,
    SchematicEdgeDTO,
    SchematicLabelDTO,
    NodeHoverDTO,
    EdgeHoverDTO,
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

# ======================================================================
# Collapsible Section
# ======================================================================

class _CollapsibleSection(QWidget):
    """
    Small GUI-only collapsible section.

    Authority
    ---------
    • No ProjectState access
    • No calculation
    • Pure presentation/layout helper
    """

    def __init__(
        self,
        title: str,
        content: QWidget,
        *,
        expanded: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._content = content

        self._toggle = QToolButton(self)
        self._toggle.setText(title)
        self._toggle.setCheckable(True)
        self._toggle.setChecked(expanded)
        self._toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._toggle.setArrowType(
            Qt.DownArrow if expanded else Qt.RightArrow
        )
        self._toggle.setStyleSheet(
            "QToolButton { font-weight: 600; padding: 6px; border: none; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toggle)
        layout.addWidget(self._content)

        self._content.setVisible(expanded)

        self._toggle.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool) -> None:
        self._toggle.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )
        self._content.setVisible(checked)

    def set_expanded(self, expanded: bool) -> None:
        self._toggle.setChecked(bool(expanded))

    def is_expanded(self) -> bool:
        return bool(self._toggle.isChecked())


# ======================================================================
# Index Route Strip Widget
# ======================================================================

class _IndexRouteStripWidget(QWidget):
    """
    H-N7c — Linear index route trace.

    Visual projection only:
    • no ProjectState access
    • no route calculation
    • no pipe sizing
    • no pressure loss
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._nodes: list[str] = []
        self._flows: list[str] = []
        self._excluded: list[str] = []
        self._basis: str = ""

        self.setMinimumHeight(130)

    def set_route(
        self,
        *,
        nodes: list[str],
        flows: list[str],
        excluded: list[str],
        basis: str,
    ) -> None:
        self._nodes = list(nodes or [])
        self._flows = list(flows or [])
        self._excluded = list(excluded or [])
        self._basis = str(basis or "")
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QBrush(Qt.white))

        if len(self._nodes) < 2:
            painter.setPen(QPen(Qt.gray))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "No index route trace available",
            )
            return

        margin_x = 24.0
        node_y = 48.0
        node_w = 118.0
        node_h = 30.0

        available_w = max(1.0, float(self.width()) - (2.0 * margin_x))
        count = len(self._nodes)

        if count <= 1:
            x_positions = [margin_x]
        else:
            step = available_w / float(count - 1)
            x_positions = [margin_x + (i * step) for i in range(count)]

        # --------------------------------------------------
        # Draw links first
        # --------------------------------------------------
        for i in range(count - 1):
            x1 = x_positions[i] + (node_w / 2.0)
            x2 = x_positions[i + 1] - (node_w / 2.0)
            y = node_y + (node_h / 2.0)

            # If the panel is narrow, allow overlap but still draw a line.
            if x2 < x1:
                x1 = x_positions[i]
                x2 = x_positions[i + 1]

            painter.setPen(QPen(Qt.darkGray, 2.0))
            painter.drawLine(QPointF(x1, y), QPointF(x2, y))

            # Arrow head
            arrow = QPolygonF(
                [
                    QPointF(x2, y),
                    QPointF(x2 - 8.0, y - 5.0),
                    QPointF(x2 - 8.0, y + 5.0),
                ]
            )
            painter.setBrush(QBrush(Qt.darkGray))
            painter.drawPolygon(arrow)

            # Flow label
            flow = self._flows[i] if i < len(self._flows) else ""
            if flow:
                painter.setPen(QPen(Qt.darkBlue))
                painter.drawText(
                    QRectF(
                        min(x1, x2),
                        y + 8.0,
                        abs(x2 - x1) + 1.0,
                        20.0,
                    ),
                    Qt.AlignCenter,
                    flow,
                )

        # --------------------------------------------------
        # Draw nodes
        # --------------------------------------------------
        painter.setFont(QFont())

        for i, label in enumerate(self._nodes):
            x = x_positions[i] - (node_w / 2.0)
            rect = QRectF(x, node_y, node_w, node_h)

            painter.setPen(QPen(Qt.black))
            painter.setBrush(QBrush(Qt.lightGray))
            painter.drawRoundedRect(rect, 6.0, 6.0)

            painter.setPen(QPen(Qt.black))
            painter.drawText(rect, Qt.AlignCenter, label)

        # --------------------------------------------------
        # Footer
        # --------------------------------------------------
        footer_y = node_y + node_h + 48.0

        footer_parts: list[str] = []

        if self._basis:
            footer_parts.append(f"Basis: {self._basis}")

        if self._excluded:
            footer_parts.append(
                "Excluded: " + ", ".join(self._excluded)
            )

        footer = "   |   ".join(footer_parts)

        if footer:
            painter.setPen(QPen(Qt.darkGray))
            painter.drawText(
                QRectF(12.0, footer_y, float(self.width()) - 24.0, 24.0),
                Qt.AlignLeft | Qt.AlignVCenter,
                footer,
            )

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

        # --------------------------------------------------
        # Title
        # --------------------------------------------------
        title = QLabel("Hydronics schematic")
        title.setStyleSheet("font-weight:600; padding:6px;")
        layout.addWidget(title)

        # --------------------------------------------------
        # Emitter demand summary
        # --------------------------------------------------
        self._emitter_demand_table = self._make_table(
            columns=["Room", "Heat Load", "Emitter", "Output", "Status"],
            stretch_columns={0},
        )
        self._add_section(
            layout,
            title="Emitter demand summary",
            table=self._emitter_demand_table,
            min_height=120,
        )

        # --------------------------------------------------
        # Hydronic skeleton
        # --------------------------------------------------
        self._hydronic_skeleton_table = self._make_table(
            columns=["Leg", "From", "To", "Type", "Length"],
            stretch_columns={1, 2},
        )
        self._add_section(
            layout,
            title="Hydronic skeleton",
            table=self._hydronic_skeleton_table,
            min_height=120,
        )

        # --------------------------------------------------
        # Pipe-run intent
        # --------------------------------------------------
        self._pipe_run_intent_table = self._make_table(
            columns=[
                "Pipe Run",
                "From",
                "To",
                "Circuit",
                "Length",
                "Material",
                "Diameter",
            ],
            stretch_columns={1, 2},
        )
        self._add_section(
            layout,
            title="Pipe-run intent",
            table=self._pipe_run_intent_table,
            min_height=120,
        )

        # --------------------------------------------------
        # Index route accumulator
        # --------------------------------------------------
        self._index_route_table = self._make_table(
            columns=[
                "Sec",
                "From",
                "To",
                "Acc. flow",
                "Included",
            ],
            stretch_columns={1, 2},
        )
        self._add_section(
            layout,
            title="Index route accumulator",
            table=self._index_route_table,
            min_height=150,
        )

        # --------------------------------------------------
        # Linear index route trace
        # --------------------------------------------------
        self._index_route_strip = _IndexRouteStripWidget(self)

        self._add_section(
            layout,
            title="Linear index route trace",
            table=self._index_route_strip,
            min_height=130,
        )

        # --------------------------------------------------
        # Basic hydronics worksheet
        # --------------------------------------------------
        self._basic_hydronics_table = self._make_table(
            columns=[
                "Room",
                "Load",
                "Required",
                "Suggested",
                "Emitter",
                "Output",
                "Status",
                "Sizing",
                "FT",
                "RT",
                "ΔT",
                "Flow",
            ],
            stretch_columns={0},
        )
        self._add_section(
            layout,
            title="Basic hydronics worksheet",
            table=self._basic_hydronics_table,
            min_height=160,
        )

        # Only one stretch, always last.
        layout.addStretch(1)

    def _make_table(
        self,
        *,
        columns: list[str],
        stretch_columns: set[int] | None = None,
    ) -> QTableWidget:
        """
        Create a standard read-only hydronics table.

        Presentation only.
        No ProjectState access.
        No calculation.
        """
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        stretch_columns = stretch_columns or set()

        header = table.horizontalHeader()
        for column_index in range(len(columns)):
            if column_index in stretch_columns:
                header.setSectionResizeMode(
                    column_index,
                    QHeaderView.Stretch,
                )
            else:
                header.setSectionResizeMode(
                    column_index,
                    QHeaderView.ResizeToContents,
                )

        return table

    def _add_section(
        self,
        layout: QVBoxLayout,
        *,
        title: str,
        table: QTableWidget,
        min_height: int,
        expanded: bool = True,
    ) -> None:
        """
        Add a table inside a collapsible hydronics section.

        Presentation only.
        """
        table.setMinimumHeight(min_height)

        layout.addWidget(
            _CollapsibleSection(
                title,
                table,
                expanded=expanded,
                parent=self,
            )
        )

    def _fit_table_height(
            self,
            table: QTableWidget,
            *,
            min_height: int = 120,
            max_height: int = 260,
    ) -> None:
        """
        Presentation-only table height helper.

        Keeps worksheet sections readable without forcing every table to
        consume excessive vertical space.
        """
        header_height = table.horizontalHeader().height()
        row_count = table.rowCount()
        row_height = table.verticalHeader().defaultSectionSize()
        frame = table.frameWidth() * 2

        wanted = header_height + frame + ((row_count + 1) * row_height)
        height = max(min_height, min(max_height, wanted))

        table.setMinimumHeight(height)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        return

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
            "No drawn topology schematic available",
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

    def set_index_route_trace(
        self,
        *,
        nodes: list[str],
        flows: list[str],
        excluded: list[str],
        basis: str,
    ) -> None:
        """
        Observer-only H-N7c linear index route trace projection.

        No ProjectState access.
        No route calculation.
        No pipe sizing.
        """
        self._index_route_strip.set_route(
            nodes=nodes,
            flows=flows,
            excluded=excluded,
            basis=basis,
        )

    def set_basic_hydronics_worksheet_rows(self, rows: list[dict]) -> None:
        """
        Read-only H-N5 basic hydronics worksheet projection.

        No authority.
        No ProjectState access.
        No calculation.
        """
        self._basic_hydronics_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("room", "—"),
                row.get("heat_load", "—"),
                row.get("required_output", "—"),
                row.get("suggested_output", "—"),
                row.get("emitter", "—"),
                row.get("output", "—"),
                row.get("status", "—"),
                row.get("sizing_status", "—"),
                row.get("flow_temp", "—"),
                row.get("return_temp", "—"),
                row.get("water_delta_t", "—"),
                row.get("mass_flow", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._basic_hydronics_table.setItem(
                    row_index,
                    col_index,
                    item,
                )
        self._fit_table_height(self._basic_hydronics_table, min_height=160, max_height=280)
        self._basic_hydronics_table.scrollToTop()

    def set_index_route_accumulator_rows(self, rows: list[dict]) -> None:
        """
        Observer-only H-N7 index route accumulator projection.

        Rows are adapter-derived display DTOs.
        The panel does not inspect ProjectState and does not calculate.
        """
        table = self._index_route_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("section", "—"),
                row.get("from", "—"),
                row.get("to", "—"),
                row.get("accumulated_flow", "—"),
                row.get("included", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=150, max_height=240)
        table.scrollToTop()

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

    def set_emitter_demand_rows(self, rows) -> None:
        """
        Observer-only hydronics demand projection.

        Rows are already derived DTOs from the adapter.
        The panel does not inspect ProjectState and does not calculate.
        """
        table = self._emitter_demand_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            heat_load = (
                "—"
                if row.design_heat_load_W is None
                else f"{row.design_heat_load_W:.1f} W"
            )

            emitter = row.emitter_summary or "—"

            output = (
                "—"
                if row.emitter_output_W is None
                else f"{row.emitter_output_W:.1f} W"
            )

            table.setItem(row_index, 0, QTableWidgetItem(row.room_name))
            table.setItem(row_index, 1, QTableWidgetItem(heat_load))
            table.setItem(row_index, 2, QTableWidgetItem(emitter))
            table.setItem(row_index, 3, QTableWidgetItem(output))
            table.setItem(row_index, 4, QTableWidgetItem(row.status))
            self._fit_table_height(table, min_height=120, max_height=220)
            table.scrollToTop()

    def set_hydronic_skeleton_rows(self, rows: list[dict]) -> None:
        """
        Observer-only hydronic skeleton projection.

        Rows are adapter-derived display DTOs.
        The panel does not inspect ProjectState and does not calculate.
        """
        table = self._hydronic_skeleton_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            length_m = row.get("length_m")
            length_text = "—" if length_m is None else f"{float(length_m):.2f} m"

            values = [
                str(row.get("leg_id", "")),
                str(row.get("from", "")),
                str(row.get("to", "")),
                str(row.get("type", "")),
                length_text,
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)
        self._fit_table_height(table, min_height=120, max_height=240)
        table.scrollToTop()

    def set_pipe_run_intent_rows(self, rows: list[dict]) -> None:
        """
        Observer-only pipe-run intent projection.

        Rows are adapter-derived display DTOs.
        The panel does not inspect ProjectState and does not calculate.
        """
        table = self._pipe_run_intent_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            length_m = row.get("length_m")
            length_text = "—" if length_m is None else f"{float(length_m):.2f} m"

            diameter_mm = row.get("nominal_diameter_mm")
            diameter_text = (
                "—"
                if diameter_mm is None
                else f"{float(diameter_mm):.0f} mm"
            )

            material_text = str(row.get("material_id") or "—")

            values = [
                str(row.get("pipe_run_id", "")),
                str(row.get("from", "")),
                str(row.get("to", "")),
                str(row.get("circuit_type", "")),
                length_text,
                material_text,
                diameter_text,
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)
        self._fit_table_height(table, min_height=120, max_height=240)
        table.scrollToTop()

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
