# ======================================================================
# HVAC/gui_v3/panels/hydronics_schematic_panel.py
# ======================================================================

"""
HVACgooee — GUI v3
Hydronics Schematic Panel

Read-only hydronics projection panel.

Authority
---------
• No ProjectState access
• No physics
• No pipe sizing
• No mutation

The panel displays adapter-derived rows only.

H-R2 layout
-----------
The panel is split into three tabs:

Overview
    • Emitter demand summary
    • Index route accumulator
    • Basic overview — calculation trace: index → boiler
   • Legacy route capacity suggestion — not Basic PS Haaland

Authority
    • Hydronic skeleton
    • Pipe-run intent
    • Pipe authority summary
    • Basic hydronics worksheet

Proportioning
    • Branch / proportioning summary
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
    QColor,
    QBrush,
)

from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolButton,
    QScrollArea,
    QTabWidget,
)

from HVAC.gui_v3.schematic.dto import (
    HydronicsSchematicDTO,
    SchematicNodeDTO,
    SchematicEdgeDTO,
    SchematicLabelDTO,
    NodeHoverDTO,
    EdgeHoverDTO,
)
from HVAC.gui_v3.widgets.proportioning_schematic_widget_v1 import (
    ProportioningSchematicWidgetV1,
)
from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegSchematicWidgetV1,
)

# ======================================================================
# Floating Inspector
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
    Basic overview — calculation trace: index → boiler.

    Visual projection only:
    • no ProjectState access
    • no route calculation
    • no pipe sizing
    • no pressure loss
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._nodes: list[str] = []
        self._link_labels: list[str] = []
        self._excluded: list[str] = []
        self._basis: str = ""

        self.setMinimumHeight(170)

    def set_route(
        self,
        *,
        nodes: list[str],
        link_labels: list[str],
        excluded: list[str],
        basis: str,
    ) -> None:
        self._nodes = list(nodes or [])
        self._link_labels = list(link_labels or [])
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
        node_y = 28.0
        node_w = 118.0
        node_h = 30.0

        count = len(self._nodes)

        left_x = margin_x + (node_w / 2.0)
        right_x = max(
            left_x,
            float(self.width()) - margin_x - (node_w / 2.0),
        )

        available_w = max(1.0, right_x - left_x)

        if count <= 1:
            x_positions = [left_x]
        else:
            step = available_w / float(count - 1)
            x_positions = [left_x + (i * step) for i in range(count)]

        # --------------------------------------------------
        # Links
        # --------------------------------------------------
        for i in range(count - 1):
            y = node_y + (node_h / 2.0)

            x1 = x_positions[i] + (node_w / 2.0)
            x2 = x_positions[i + 1] - (node_w / 2.0)

            if x2 < x1:
                x1 = x_positions[i]
                x2 = x_positions[i + 1]

            painter.setPen(QPen(Qt.darkGray, 2.0))
            painter.drawLine(QPointF(x1, y), QPointF(x2, y))

            arrow = QPolygonF(
                [
                    QPointF(x2, y),
                    QPointF(x2 - 8.0, y - 5.0),
                    QPointF(x2 - 8.0, y + 5.0),
                ]
            )
            painter.setBrush(QBrush(Qt.darkGray))
            painter.drawPolygon(arrow)

            link_label = (
                self._link_labels[i]
                if i < len(self._link_labels)
                else ""
            )

            if link_label:
                painter.setPen(QPen(Qt.darkBlue))
                painter.drawText(
                    QRectF(
                        min(x1, x2),
                        y + 14.0,
                        abs(x2 - x1) + 1.0,
                        44.0,
                    ),
                    Qt.AlignCenter | Qt.TextWordWrap,
                    link_label,
                )

        # --------------------------------------------------
        # Nodes
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

            # H-S8-F:
            # Basic overview trace is index → boiler.
            # Therefore the first node is the Basic terminal/index target.
            # Red flag is schematic-only; tables stay text-coloured.
            if i == 0:
                self._paint_index_flag(painter, rect)

        # --------------------------------------------------
        # Footer
        # --------------------------------------------------
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
                QRectF(
                    12.0,
                    node_y + node_h + 66.0,
                    float(self.width()) - 24.0,
                    24.0,
                ),
                Qt.AlignLeft | Qt.AlignVCenter,
                footer,
            )

    def _paint_index_flag(self, painter: QPainter, rect: QRectF) -> None:
        """
        Paint a small red schematic-only index flag.

        H-S8-F visual rule:
        • red flag is schematic-only
        • red flag marks the Basic terminal/index target
        • table index/terminal markers remain plain text
        """
        pole_x = rect.left() + 8.0
        pole_y = rect.top() - 18.0
        pole_h = 18.0
        flag_w = 12.0
        flag_h = 8.0

        painter.setPen(QPen(Qt.darkRed, 1.4))
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

        painter.setPen(QPen(Qt.darkRed, 1.0))
        painter.setBrush(QBrush(Qt.red))
        painter.drawPolygon(flag)

# ======================================================================
# HydronicsSchematicPanel
# ======================================================================

class HydronicsSchematicPanel(QWidget):
    """
    Read-only hydronics schematic / worksheet projection panel.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Current schematic DTO, retained for old drawn-schematic path.
        self._schematic: Optional[HydronicsSchematicDTO] = None

        # Floating inspector.
        self._inspector = _HoverInspector(self)

        self._build_ui()
        self.render_empty_state()

        self.setFocusPolicy(Qt.NoFocus)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setMinimumSize(400, 260)

    def select_proportioning_tab(self) -> None:
        """
        H-S8-L-C:
        Select the read-only Proportioning tab.

        Navigation only:
        - no topology mutation
        - no pressure calculation
        - no proportioning execution
        """
        if not hasattr(self, "_tabs"):
            return

        for index in range(self._tabs.count()):
            if self._tabs.tabText(index) == "Proportioning":
                self._tabs.setCurrentIndex(index)
                return

    # ------------------------------------------------------------------
    # Adapter ingress
    # ------------------------------------------------------------------

    def _set_schematic(self, dto: HydronicsSchematicDTO) -> None:
        """
        Replace the current schematic DTO and repaint.

        Replace-only semantics.
        No validation.
        No interpretation.
        """
        self._schematic = dto
        self.update()

    def set_index_route_trace(
        self,
        *,
        nodes: list[str],
        link_labels: list[str],
        excluded: list[str],
        basis: str,
    ) -> None:
        """
        Observer-only linear index route trace projection.
        """
        self._index_route_strip.set_route(
            nodes=nodes,
            link_labels=link_labels,
            excluded=excluded,
            basis=basis,
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        title = QLabel("Hydronics schematic")
        title.setStyleSheet("font-weight:600; padding:6px;")
        outer_layout.addWidget(title)

        self._tabs = QTabWidget(self)
        outer_layout.addWidget(self._tabs)

        overview_layout = self._make_tab("Basic Overview")
        authority_layout = self._make_tab("Authority")
        self._proportioning_tab = self._make_tab("Proportioning")
        proportioning_layout = self._proportioning_tab

        self._proportioned_tab = self._make_tab("Proportioned")
        proportioned_layout = self._proportioned_tab
        # --------------------------------------------------
        # H-S19-J — DEV common-main / leg / subleg topology
        # --------------------------------------------------
        self._common_main_leg_subleg_table = self._make_table(
            columns=[
                "Common main",
                "Leg",
                "Subleg",
                "Role",
                "Rooms",
                "Status",
            ],
            stretch_columns={1, 2, 4, 5},
        )

        self._add_section(
            proportioning_layout,
            title="DEV common-main / leg / subleg schematic — preview only",
            table=self._common_main_leg_subleg_table,
            min_height=160,
        )

        # --------------------------------------------------
        # H-S19-K — DEV common-main / leg / subleg drawn schematic
        # --------------------------------------------------
        self._common_main_leg_subleg_schematic_widget = (
            CommonMainLegSublegSchematicWidgetV1(self)
        )

        self._common_main_leg_subleg_schematic_scroll = QScrollArea(self)
        self._common_main_leg_subleg_schematic_scroll.setWidgetResizable(False)
        self._common_main_leg_subleg_schematic_scroll.setFrameShape(
            QFrame.NoFrame
        )
        self._common_main_leg_subleg_schematic_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._common_main_leg_subleg_schematic_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._common_main_leg_subleg_schematic_scroll.setWidget(
            self._common_main_leg_subleg_schematic_widget
        )

        self._add_section(
            proportioning_layout,
            title="DEV common-main / leg / subleg drawn schematic — preview only",
            table=self._common_main_leg_subleg_schematic_scroll,
            min_height=380,
        )

        # --------------------------------------------------
        # H-S20-A — Proportioned tab shell
        # --------------------------------------------------
        self._proportioned_status_table = self._make_table(
            columns=[
                "Item",
                "Status",
            ],
            stretch_columns={1},
        )

        self._add_section(
            proportioned_layout,
            title="Proportioned system — final output",
            table=self._proportioned_status_table,
            min_height=120,
        )

        self.set_proportioned_status(
            [
                {
                    "item": "Proportioned system",
                    "status": (
                        "No proportioned system committed yet — "
                        "use the Proportioning tab for preview calculations"
                    ),
                },
                {
                    "item": "Final schematic",
                    "status": "Not available until proportioning is committed",
                },
                {
                    "item": "Final pipe schedule",
                    "status": "Not available until proportioning is committed",
                },
            ]
        )
        # --------------------------------------------------
        # Overview tab
        # --------------------------------------------------
        self._emitter_demand_table = self._make_table(
            columns=["Room", "Heat Load", "Emitter", "Output", "Status"],
            stretch_columns={0},
        )

        self._add_section(
            overview_layout,
            title="Emitter demand summary",
            table=self._emitter_demand_table,
            min_height=120,
        )

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
            overview_layout,
            title="Index route accumulator",
            table=self._index_route_table,
            min_height=150,
        )

        self._index_route_strip = _IndexRouteStripWidget(self)
        self._add_section(
            overview_layout,
            title="Basic overview — calculation trace: index → boiler",
            table=self._index_route_strip,
            min_height=170,
        )

        self._pipe_size_suggestion_table = self._make_table(
            columns=[
                "Rank",
                "Route",
                "Sections",
                "Σ Straight Δp",
                "Σ Local Δp",
                "Σ Route Δp",
                "Complete",
                "Controlling",
                "Status",
            ],
            stretch_columns={1, 8},
        )
        self._add_section(
            overview_layout,
            title="Legacy route capacity suggestion — not Basic PS Haaland",
            table=self._pipe_size_suggestion_table,
            min_height=140,
        )

        overview_layout.addStretch(1)

        # --------------------------------------------------
        # Authority tab
        # --------------------------------------------------
        self._hydronic_skeleton_table = self._make_table(
            columns=["Leg", "From", "To", "Type", "Length"],
            stretch_columns={1, 2},
        )
        self._add_section(
            authority_layout,
            title="Hydronic skeleton",
            table=self._hydronic_skeleton_table,
            min_height=120,
        )

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
            authority_layout,
            title="Pipe-run intent",
            table=self._pipe_run_intent_table,
            min_height=120,
        )

        self._pipe_authority_summary_table = self._make_table(
            columns=[
                "Role",
                "From",
                "To",
                "Flow basis",
                "Mass flow",
                "Sizing scope",
                "Status",
            ],
            stretch_columns={1, 2, 3},
        )
        self._pipe_authority_summary_table.setColumnWidth(0, 150)
        self._pipe_authority_summary_table.setColumnWidth(1, 160)
        self._pipe_authority_summary_table.setColumnWidth(2, 180)
        self._pipe_authority_summary_table.setColumnWidth(3, 190)
        self._pipe_authority_summary_table.setColumnWidth(4, 110)
        self._pipe_authority_summary_table.setColumnWidth(5, 120)
        self._pipe_authority_summary_table.setColumnWidth(6, 130)

        self._add_section(
            authority_layout,
            title="Pipe authority summary",
            table=self._pipe_authority_summary_table,
            min_height=240,
        )
        self._leg_subleg_topology_table = self._make_table(
            columns=[
                "Section",
                "Role",
                "From",
                "To",
                "Flow",
                "Termination",
                "Basis",
            ],
            stretch_columns={0, 1, 2, 3, 6},
        )
        self._add_section(
            authority_layout,
            title="Leg / subleg topology",
            table=self._leg_subleg_topology_table,
            min_height=220,
        )


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
            authority_layout,
            title="Basic hydronics worksheet",
            table=self._basic_hydronics_table,
            min_height=160,
        )

        authority_layout.addStretch(1)

        # --------------------------------------------------
        # Proportioning readiness
        # --------------------------------------------------
        self._proportioning_readiness_table = self._make_table(
            columns=[
                "Item",
                "Value",
            ],
            stretch_columns={1},
        )

        self._add_section(
            proportioning_layout,
            title="Proportioning readiness — received from Basic",
            table=self._proportioning_readiness_table,
            min_height=170,
        )

        # --------------------------------------------------
        # Proportioning tab
        # --------------------------------------------------
        self._proportioning_schematic_widget = ProportioningSchematicWidgetV1(self)

        self._proportioning_schematic_scroll = QScrollArea(self)
        self._proportioning_schematic_scroll.setWidgetResizable(False)
        self._proportioning_schematic_scroll.setFrameShape(QFrame.NoFrame)
        self._proportioning_schematic_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._proportioning_schematic_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._proportioning_schematic_scroll.setWidget(
            self._proportioning_schematic_widget
        )

        self._add_section(
            proportioning_layout,
            title="Proportioning route — calculation trace: boiler → index",
            table=self._proportioning_schematic_scroll,
            min_height=300,
        )

        self._proportioning_basic_ps_sections_table = self._make_table(
            columns=[
                "Order",
                "From",
                "To",
                "Q carried",
                "Flow kg/s",
                "Pipe",
                "v m/s",
                "Δp/m",
                "Length",
                "K",
                "Local Δp",
                "Straight Δp",
                "Section Δp",
                "Status",
            ],
            stretch_columns={1, 2, 10},
        )

        self._add_section(
            proportioning_layout,
            title="Received Basic PS sections + Local K preview",
            table=self._proportioning_basic_ps_sections_table,
            min_height=180,
        )

        # --------------------------------------------------
        # H-S14 — Route Δp preview
        # --------------------------------------------------
        self._route_pressure_preview_table = self._make_table(
            columns=[
                "Rank",
                "Route",
                "Sections",
                "Σ Straight Δp",
                "Σ Local Δp",
                "Σ Route Δp",
                "Complete",
                "Controlling",
                "Status",
            ],
            stretch_columns={1, 8},
        )

        self._add_section(
            proportioning_layout,
            title="Route Δp preview — Basic PS + Local K",
            table=self._route_pressure_preview_table,
            min_height=120,
        )
        # --------------------------------------------------
        # H-S18 — Route Δp shortfall preview
        # --------------------------------------------------
        self._route_shortfall_preview_table = self._make_table(
            columns=[
                "Rank",
                "Route",
                "Route Δp",
                "Controlling Δp",
                "Δp Shortfall",
                "Action",
                "Status",
            ],
            stretch_columns={1, 5, 6},
        )

        self._add_section(
            proportioning_layout,
            title="Route Δp shortfall preview — proportioning comparison",
            table=self._route_shortfall_preview_table,
            min_height=120,
        )

        # --------------------------------------------------
        # H-S19-H — Direct vs reverse return comparison
        # --------------------------------------------------
        self._return_path_comparison_table = self._make_table(
            columns=[
                "Route",
                "Room",
                "Emitter",
                "F+R Rank",
                "F+R Δp",
                "F+R Ctrl",
                "F+RR Rank",
                "F+RR Δp",
                "F+RR Ctrl",
                "RR suitability",
                "Status",
            ],
            stretch_columns={0, 1, 2, 9, 10},
        )

        self._add_section(
            proportioning_layout,
            title="Direct vs reverse return circuit comparison — preview only",
            table=self._return_path_comparison_table,
            min_height=180,
        )

        # --------------------------------------------------
        # Branch / proportioning summary
        # --------------------------------------------------
        self._proportioning_table = self._make_table(
            columns=[
                "Group",
                "Role",
                "From",
                "To",
                "Flow",
                "Basis",
                "Status",
            ],
            stretch_columns={0, 1, 2, 3, 5, 6},
        )

        self._add_section(
            proportioning_layout,
            title="Branch / proportioning summary",
            table=self._proportioning_table,
            min_height=220,
        )

        proportioning_layout.addStretch(1)

    def set_proportioning_basic_ps_sections(self, rows: list[dict]) -> None:
        """
        Observer-only Basic PS section basis received by Proportioning.

        Display only:
        • no ProjectState access
        • no pipe sizing
        • no pressure-loss calculation
        • no balancing
        """
        if not hasattr(self, "_proportioning_basic_ps_sections_table"):
            return

        table = self._proportioning_basic_ps_sections_table
        table.setRowCount(len(rows))
        self._proportioning_basic_ps_section_row_by_id = {}

        for row_index, row in enumerate(rows):
            section_id = str(row.get("section_id") or "")
            if section_id:
                self._proportioning_basic_ps_section_row_by_id[
                    section_id
                ] = row_index

            values = [
                row.get("order", "—"),
                row.get("from", "—"),
                row.get("to", "—"),
                row.get("q_carried", "—"),
                row.get("flow_kg_s", "—"),
                row.get("pipe", "—"),
                row.get("velocity_m_s", "—"),
                row.get("dp_per_m", "—"),
                row.get("length_m", "—"),
                row.get("k_total", "0.00"),
                row.get("local_dp", "0.0 Pa"),
                row.get("straight_dp", "—"),
                row.get("section_dp", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=180, max_height=300)
        if not getattr(self, "_suppress_basic_ps_scroll_to_top", False):
            table.scrollToTop()

    def set_common_main_leg_subleg_schematic(self, schematic) -> None:
        """
        H-S19-K:
        Display DEV common-main / leg / subleg schematic.

        Display only:
        • no ProjectState access
        • no pump
        • no balancing
        • no committed return arrangement
        """
        if not hasattr(self, "_common_main_leg_subleg_schematic_widget"):
            return

        self._common_main_leg_subleg_schematic_widget.set_schematic(
            schematic
        )

    def set_common_main_leg_subleg_rows(self, rows: list[dict]) -> None:
        """
        H-S19-J:
        Display DEV common-main / leg / subleg topology.

        Display only:
        • no ProjectState access
        • no balancing
        • no pump selection
        • no committed return arrangement
        """
        if not hasattr(self, "_common_main_leg_subleg_table"):
            return

        table = self._common_main_leg_subleg_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("common_main", "Common main"),
                row.get("leg", "—"),
                row.get("subleg", "—"),
                row.get("role", "—"),
                row.get("rooms", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=160, max_height=240)
        table.scrollToTop()

    def focus_proportioning_basic_ps_section(
        self,
        section_id: str,
    ) -> None:
        """
        H-S13:
        Highlight and scroll the Proportioning received Basic PS row
        matching a Local K section selection.

        Display/focus only. No engineering authority.
        """
        if not hasattr(self, "_proportioning_basic_ps_sections_table"):
            return

        table = self._proportioning_basic_ps_sections_table
        row_map = getattr(
            self,
            "_proportioning_basic_ps_section_row_by_id",
            {},
        )

        row_index = row_map.get(str(section_id or ""))

        if row_index is None:
            return

        table.selectRow(row_index)

        item = table.item(row_index, 0)
        if item is not None:
            table.scrollToItem(item)

    def set_route_pressure_preview_rows(self, rows: list[dict]) -> None:
        """
        H-S14:
        Display route-level Δp accumulation.

        Display only:
        • no ProjectState access
        • no balancing
        • no pump selection
        """
        if not hasattr(self, "_route_pressure_preview_table"):
            return

        table = self._route_pressure_preview_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("rank", "—"),
                row.get("route", "—"),
                row.get("sections", "—"),
                row.get("straight_dp", "—"),
                row.get("local_dp", "—"),
                row.get("route_dp", "—"),
                row.get("complete", "No"),
                row.get("controlling", "No"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=120, max_height=180)
        table.scrollToTop()

    def set_return_path_comparison_rows(self, rows: list[dict]) -> None:
        """
        H-S19-H:
        Display direct-return vs reverse-return circuit comparison.

        Display only:
        • no ProjectState access
        • no balancing
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        if not hasattr(self, "_return_path_comparison_table"):
            return

        table = self._return_path_comparison_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("route", "—"),
                row.get("room", "—"),
                row.get("emitter", "—"),
                row.get("direct_rank", "—"),
                row.get("direct_total_dp", "—"),
                row.get("direct_controlling", "No"),
                row.get("reverse_rank", "—"),
                row.get("reverse_total_dp", "—"),
                row.get("reverse_controlling", "No"),
                row.get("rr_suitability", "—"),
                row.get("status", "—"),
            ]
            direct_dp = self._try_float(row.get("direct_total_dp_raw", None))
            reverse_dp = self._try_float(row.get("reverse_total_dp_raw", None))

            comparison_is_clear = False
            direct_is_lower = False
            reverse_is_lower = False

            if direct_dp is not None and reverse_dp is not None:
                delta_percent = self._delta_percent(direct_dp, reverse_dp)

                if delta_percent > self._RETURN_COMPARISON_TOLERANCE_PERCENT:
                    comparison_is_clear = True
                    direct_is_lower = direct_dp < reverse_dp
                    reverse_is_lower = reverse_dp < direct_dp

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if comparison_is_clear:
                    if col_index == 4:
                        if direct_is_lower:
                            item.setForeground(QBrush(QColor(0, 120, 0)))
                        else:
                            item.setForeground(QBrush(QColor(190, 110, 0)))

                    elif col_index == 7:
                        if reverse_is_lower:
                            item.setForeground(QBrush(QColor(0, 120, 0)))
                        else:
                            item.setForeground(QBrush(QColor(190, 110, 0)))
                table.setItem(row_index, col_index, item)


        self._fit_table_height(table, min_height=180, max_height=260)
        table.scrollToTop()

    def set_proportioned_status(self, rows: list[dict]) -> None:
        """
        H-S20-A:
        Display future final-output status for the Proportioned tab.

        Display only:
        • no ProjectState access
        • no preview calculations
        • no final proportioning commit
        """
        if not hasattr(self, "_proportioned_status_table"):
            return

        table = self._proportioned_status_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("item", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=120, max_height=180)
        table.scrollToTop()

    def set_route_shortfall_preview_rows(self, rows: list[dict]) -> None:
        """
        H-S18:
        Display route-level Δp shortfall to the controlling route.

        Display only:
        • no ProjectState access
        • no balancing valve settings
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_route_shortfall_preview_table"):
            return

        table = self._route_shortfall_preview_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("rank", "—"),
                row.get("route", "—"),
                row.get("route_dp", "—"),
                row.get("controlling_dp", "—"),
                row.get("shortfall_dp", "—"),
                row.get("action", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=120, max_height=180)
        table.scrollToTop()


    def set_proportioning_readiness(self, readiness: dict) -> None:
        """
        Observer-only readiness/status projection for Proportioning.

        No ProjectState access.
        No calculation.
        No mutation.
        """
        if not hasattr(self, "_proportioning_readiness_table"):
            return

        rows = [
            ("Index room", readiness.get("index_room", "—")),
            ("Terminal room", readiness.get("terminal_room", "—")),
            ("Terminal alignment", readiness.get("terminal_alignment", "—")),
            ("Basic basis", readiness.get("basis_mode", "—")),
            ("Total index length", readiness.get("total_index_length", "—")),
            ("Nominal Δp/m", readiness.get("nominal_gradient", "—")),
            ("Proportioning status", readiness.get("status", "—")),
        ]

        table = self._proportioning_readiness_table
        table.setRowCount(len(rows))

        for row_index, (name, value) in enumerate(rows):
            table.setItem(row_index, 0, QTableWidgetItem(str(name)))
            table.setItem(row_index, 1, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()

    def set_proportioning_schematic(self, schematic) -> None:
        """
        Observer-only proportioning schematic projection.
        """
        self._proportioning_schematic_widget.set_schematic(schematic)

    def _make_tab(self, title: str) -> QVBoxLayout:
        """
        Create a scrollable tab and return its content layout.
        """
        scroll = QScrollArea(self._tabs)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        scroll.setWidget(content)
        self._tabs.addTab(scroll, title)

        return layout

    def _make_table(
        self,
        *,
        columns: list[str],
        stretch_columns: set[int] | None = None,
    ) -> QTableWidget:
        """
        Create a standard read-only hydronics table.
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
        table: QWidget,
        min_height: int,
        expanded: bool = True,
    ) -> None:
        """
        Add a widget inside a collapsible hydronics section.
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
    # Row setters
    # ------------------------------------------------------------------

    def set_emitter_demand_rows(self, rows) -> None:
        """
        Observer-only hydronics demand projection.
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

            values = [
                row.room_name,
                heat_load,
                emitter,
                output,
                row.status,
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=120, max_height=220)
        table.scrollToTop()

    def set_hydronic_skeleton_rows(self, rows: list[dict]) -> None:
        """
        Observer-only hydronic skeleton projection.
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

    def set_pipe_authority_summary_rows(self, rows: list[dict]) -> None:
        """
        Observer-only pipe authority summary projection.
        """
        table = self._pipe_authority_summary_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("pipe_role", "—"),
                row.get("from_label", "—"),
                row.get("to_label", "—"),
                row.get("flow_basis", "—"),
                row.get("mass_flow", "—"),
                row.get("sizing_scope", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=240, max_height=340)
        table.scrollToTop()

    def set_leg_subleg_topology_rows(self, rows: list[dict]) -> None:
        """
        Observer-only leg/subleg topology projection.

        Display only:
        • no ProjectState access
        • no pressure loss
        • no pipe sizing
        • no balancing
        """
        table = self._leg_subleg_topology_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("section", "—"),
                row.get("role", "—"),
                row.get("from", "—"),
                row.get("to", "—"),
                row.get("flow", "—"),
                row.get("termination", "—"),
                row.get("basis", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=220, max_height=360)
        table.scrollToTop()

    def set_proportioning_rows(self, rows: list[dict]) -> None:
        """
        Observer-only branch/proportioning summary projection.

        Display only:
        • no ProjectState access
        • no pipe sizing
        • no pressure loss
        • no balancing
        """
        table = self._proportioning_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("group", "—"),
                row.get("role", "—"),
                row.get("from", "—"),
                row.get("to", "—"),
                row.get("flow", "—"),
                row.get("basis", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=220, max_height=340)
        table.scrollToTop()

    def set_index_route_accumulator_rows(self, rows: list[dict]) -> None:
        """
        Observer-only index route accumulator projection.
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

    def set_pipe_size_suggestion_rows(self, rows: list[dict]) -> None:
        """
        Observer-only basic pipe size suggestion projection.
        """
        table = self._pipe_size_suggestion_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("section", "—"),
                row.get("from", "—"),
                row.get("to", "—"),
                row.get("flow", "—"),
                row.get("size", "—"),
                row.get("capacity", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=140, max_height=240)
        table.scrollToTop()

    def set_basic_hydronics_worksheet_rows(self, rows: list[dict]) -> None:
        """
        Read-only basic hydronics worksheet projection.
        """
        table = self._basic_hydronics_table
        table.setRowCount(len(rows))

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
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=160, max_height=280)
        table.scrollToTop()

    # ------------------------------------------------------------------
    # Legacy drawing path
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        return

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

            painter.drawText(
                QRectF(node.x - 50, node.y + 18, 100, 20),
                Qt.AlignCenter,
                node.id,
            )

    _RETURN_COMPARISON_TOLERANCE_PERCENT = 5.0

    @staticmethod
    def _try_float(value: object) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _delta_percent(a: float, b: float) -> float:
        reference = max(abs(a), abs(b))

        if reference <= 0.0:
            return 0.0

        return abs(a - b) / reference * 100.0

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

        Pure rendering.
        Shape is a hint, not authority.
        """
        if shape == "CIRCLE":
            painter.drawEllipse(
                QRectF(x - size, y - size, size * 2, size * 2)
            )

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
            painter.drawEllipse(
                QRectF(x - size, y - size, size * 2, size * 2)
            )

    # ------------------------------------------------------------------
    # Hover formatting
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
    # Mouse hover handling
    # ------------------------------------------------------------------

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._schematic is None:
            self._inspector.hide_payload()
            event.ignore()
            return

        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()

        for node in self._schematic.nodes:
            dx = pos.x() - node.x
            dy = pos.y() - node.y
            if dx * dx + dy * dy < 12 * 12 and node.hover:
                self._inspector.show_payload(
                    self._format_node_hover(node.hover),
                    global_pos,
                )
                return

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