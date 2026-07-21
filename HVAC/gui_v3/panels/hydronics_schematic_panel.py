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
The panel is split into four tabs:

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
    • Hydronic topology authority audit — branch-aware basis
"""
from __future__ import annotations

from dataclasses import replace
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
)

from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolButton,
    QScrollArea,
    QTabWidget,
    QAbstractItemView,
    QGridLayout,
    QRadioButton,
    QButtonGroup,
    QHBoxLayout,
    QComboBox,
    QDoubleSpinBox,
    QSplitter,
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
    CommonMainLegSublegSectionEvidenceV1,
)
from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    ProportioningInputSnapshotV1,
    build_proportioning_input_snapshot_v1,
)
from HVAC.hydronics.proportioning.proportioning_readiness_gate_v1 import (
    ProportioningReadinessGateV1,
    evaluate_proportioning_readiness_v1,
)
from HVAC.hydronics.proportioning.preliminary_route_balancing_requirement_v1 import (
    PreliminaryRouteBalancingPreviewV1,
    build_preliminary_route_balancing_preview_v1,
)
from HVAC.hydronics.proportioning.balancing_point_assumption_v1 import (
    BalancingPointAssumptionV1,
    get_default_balancing_point_assumption_v1,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    build_preliminary_balancing_resistance_basis_v1,
)
from HVAC.hydronics.proportioning.section_route_identity_v1 import (
    enrich_basic_ps_section_rows_with_route_identity_v1,
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
        self._focus: dict[str, str] = {}
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
        self._proportioning_snapshot_section_rows: list[dict] = []
        self._proportioning_snapshot_route_rows: list[dict] = []
        self._proportioning_snapshot_shortfall_rows: list[dict] = []
        self._proportioning_snapshot_return_comparison_rows: list[dict] = []
        self._proportioning_input_snapshot: ProportioningInputSnapshotV1 | None = None
        self._proportioning_readiness_gate: ProportioningReadinessGateV1 | None = None
        self._preliminary_route_balancing_preview: (
                PreliminaryRouteBalancingPreviewV1 | None
        ) = None
        self._balancing_point_assumption: BalancingPointAssumptionV1 = (
            get_default_balancing_point_assumption_v1()
        )
        self._preliminary_balancing_resistance_basis: (
                PreliminaryBalancingResistanceBasisV1 | None
        ) = None
        # Current schematic DTO, retained for old drawn-schematic path.
        self._schematic: Optional[HydronicsSchematicDTO] = None

        # Floating inspector.
        self._return_path_focus_by_row: dict[int, dict[str, str]] = {}
        self._return_path_row_data_by_row: dict[int, dict] = {}
        self._common_main_leg_subleg_row_by_subleg_id: dict[str, int] = {}

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

        # H-S35-A2 — fixed table-viewer launcher.
        # This header sits outside every scrollable tab, keeping the action
        # visible without overlay geometry or event-filter ownership.
        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 4, 0)
        header_layout.setSpacing(8)

        title = QLabel("Hydronics schematic", header)
        title.setStyleSheet("font-weight:600; padding:6px;")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self._clean_proportioned_table_viewer_button = QPushButton(
            "Open Proportioned table viewer",
            header,
        )
        self._clean_proportioned_table_viewer_button.setToolTip(
            "Open the draggable, resizable read-only Proportioned "
            "table window."
        )
        self._clean_proportioned_table_viewer_button.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 5px 10px; }"
        )
        self._clean_proportioned_table_viewer_button.clicked.connect(
            self._show_clean_proportioned_table_viewer_v1
        )
        header_layout.addWidget(
            self._clean_proportioned_table_viewer_button
        )

        outer_layout.addWidget(header)

        self._tabs = QTabWidget(self)
        outer_layout.addWidget(self._tabs)

        overview_layout = self._make_tab("Basic Overview")
        authority_layout = self._make_tab("Authority")

        self._proportioning_tab = self._make_tab("Proportioning")
        proportioning_layout = self._proportioning_tab

        self._proportioning_data_tab = self._make_tab("Proportioning Data")
        self._proportioned_tab = self._proportioning_data_tab

        self._clean_proportioned_tab = self._make_tab("Proportioned")
        self._clean_proportioned_tab.addWidget(
            QLabel(
                "Clean Proportioned output — summary only. "
                "Detailed route, balancing, and authority evidence "
                "is held in Proportioning Data."
            )
        )

        # H-S35-A viewer launcher is held in the fixed panel header.

        self._clean_proportioned_output_table = self._make_table(
            columns=[
                "Item",
                "Status",
            ]
        )

        self._add_section(
            self._clean_proportioned_tab,
            title="Proportioned output summary — read-only",
            table=self._clean_proportioned_output_table,
            min_height=185,
            expanded=True,
        )

        self._configure_clean_proportioned_output_summary_table_v1()

        self._clean_proportioned_route_output_table = self._make_table(
            columns=[
                "Route",
                "Basis",
                "Sections",
                "Flow kg/s",
                "Pipe DN",
                "Δp/m",
                "Chosen Δp",
                "Added Δp",
                "Authority",
                "Status",
            ]
        )

        self._add_section(
            self._clean_proportioned_tab,
            title="Proportioned route output — read-only",
            table=self._clean_proportioned_route_output_table,
            min_height=220,
            expanded=True,
        )

        self._configure_clean_proportioned_route_output_table_v1()

        # --------------------------------------------------
        # H-S34-B — separate clean Proportioned schematic
        # --------------------------------------------------
        # This is a second widget instance. It deliberately does not use
        # the existing Proportioning schematic focus callback.
        #
        # Display only:
        # • no ProjectState mutation
        # • no hydraulic recalculation
        # • no pipe resizing
        # • no pump or valve selection
        self._clean_proportioned_common_main_leg_subleg_schematic_widget = (
            CommonMainLegSublegSchematicWidgetV1(self)
        )

        self._clean_proportioned_common_main_leg_subleg_schematic_scroll = (
            QScrollArea(self)
        )
        self._clean_proportioned_common_main_leg_subleg_schematic_scroll.setWidgetResizable(
            False
        )
        self._clean_proportioned_common_main_leg_subleg_schematic_scroll.setFrameShape(
            QFrame.NoFrame
        )
        self._clean_proportioned_common_main_leg_subleg_schematic_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._clean_proportioned_common_main_leg_subleg_schematic_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._clean_proportioned_common_main_leg_subleg_schematic_scroll.setWidget(
            self._clean_proportioned_common_main_leg_subleg_schematic_widget
        )

        self._add_section(
            self._clean_proportioned_tab,
            title=(
                "Proportioned hydronic topology schematic "
                "— read-only"
            ),
            table=(
                self._clean_proportioned_common_main_leg_subleg_schematic_scroll
            ),
            min_height=300,
            expanded=True,
        )

        self._clean_proportioned_section_view_controls = QWidget()
        controls_layout = QHBoxLayout(
            self._clean_proportioned_section_view_controls
        )
        controls_layout.setContentsMargins(0, 4, 0, 4)

        self._clean_proportioned_section_view_mode_label = QLabel(
            "Pipe-section view:"
        )
        self._clean_proportioned_section_view_mode_combo = QComboBox()
        self._clean_proportioned_section_view_mode_combo.addItems(
            [
                "Selected route only",
                "All routes",
            ]
        )
        self._clean_proportioned_section_view_mode_combo.currentTextChanged.connect(
            self._on_clean_proportioned_section_view_mode_changed_v1
        )

        # H-S41-B — evidence stage is independent of route filtering.
        self._clean_proportioned_evidence_view_label = QLabel("Evidence:")
        self._clean_proportioned_evidence_view_button = QPushButton(
            "Proportioning"
        )
        self._clean_proportioned_evidence_view_button.setCheckable(True)
        self._clean_proportioned_evidence_view_button.setChecked(True)
        self._clean_proportioned_evidence_view_button.setMaximumWidth(130)
        self._set_clean_proportioned_evidence_button_style_v1(
            self._clean_proportioned_evidence_view_button,
            "Proportioning",
        )
        self._clean_proportioned_evidence_view_button.toggled.connect(
            self._on_clean_proportioned_evidence_view_toggled_v1
        )
        self._clean_proportioned_evidence_view_mode_v1 = "Proportioning"

        self._clean_proportioned_focused_section_label = QLabel(
            "Focused route: —"
        )

        controls_layout.addWidget(
            self._clean_proportioned_section_view_mode_label
        )
        controls_layout.addWidget(
            self._clean_proportioned_section_view_mode_combo
        )
        controls_layout.addSpacing(10)
        controls_layout.addWidget(
            self._clean_proportioned_evidence_view_label
        )
        controls_layout.addWidget(
            self._clean_proportioned_evidence_view_button
        )
        controls_layout.addWidget(
            self._clean_proportioned_focused_section_label,
            1,
        )

        try:
            self._clean_proportioned_tab.layout().addWidget(
                self._clean_proportioned_section_view_controls
            )
        except Exception:
            pass

        focused_section_widget = QWidget(self)
        focused_section_layout = QVBoxLayout(focused_section_widget)
        focused_section_layout.setContentsMargins(0, 0, 0, 0)
        focused_section_layout.setSpacing(4)

        self._clean_proportioned_section_mode_table = (
            self._make_pipe_section_mode_table_v1(focused_section_widget)
        )
        focused_section_layout.addWidget(
            self._clean_proportioned_section_mode_table,
            0,
            Qt.AlignLeft,
        )

        self._clean_proportioned_focused_section_table = self._make_table(
            columns=[
                "Route",
                "Section",
                "From",
                "To",
                "Flow kg/s",
                "Pipe DN",
                "Δp/m",
                "Length",
                "K",
                "Section Δp",
                "Iter",
                "Status",
            ]
        )
        focused_section_layout.addWidget(
            self._clean_proportioned_focused_section_table,
            1,
        )

        self._add_section(
            self._clean_proportioned_tab,
            title="Focused route / subleg sections — read-only",
            table=focused_section_widget,
            min_height=225,
            expanded=True,
        )

        self._configure_clean_proportioned_focused_section_table_v1()
        self._refresh_clean_proportioned_focused_section_view_v1()

        self.set_clean_proportioned_route_output_rows([])

        self._clean_proportioned_tab.addStretch(1)

        proportioned_layout = self._proportioned_tab

        # --------------------------------------------------
        # H-S20-A2 / H-S20-B — Proportioning input snapshot summary
        # --------------------------------------------------
        self._proportioning_input_snapshot_card = QFrame(self)
        self._proportioning_input_snapshot_card.setFrameShape(QFrame.StyledPanel)
        self._proportioning_input_snapshot_card.setMinimumHeight(86)
        self._proportioning_input_snapshot_card.setMaximumHeight(118)

        snapshot_layout = QGridLayout(self._proportioning_input_snapshot_card)
        snapshot_layout.setContentsMargins(8, 6, 8, 6)
        snapshot_layout.setHorizontalSpacing(16)
        snapshot_layout.setVerticalSpacing(3)

        self._snapshot_title_label = QLabel(
            "Proportioning input snapshot — read-only basis",
            self._proportioning_input_snapshot_card,
        )
        self._snapshot_title_label.setStyleSheet("font-weight: 600;")

        self._snapshot_status_label = QLabel(
            "Status: Snapshot empty",
            self._proportioning_input_snapshot_card,
        )
        self._snapshot_sections_label = QLabel(
            "Sections: 0",
            self._proportioning_input_snapshot_card,
        )
        self._snapshot_routes_label = QLabel(
            "Routes: 0",
            self._proportioning_input_snapshot_card,
        )
        self._snapshot_returns_label = QLabel(
            "Return comparisons: 0",
            self._proportioning_input_snapshot_card,
        )

        self._snapshot_readiness_label = QLabel(
            "Readiness: Not ready for proportioning",
            self._proportioning_input_snapshot_card,
        )

        self._snapshot_warnings_label = QLabel(
            "Warnings: —",
            self._proportioning_input_snapshot_card,
        )
        self._snapshot_warnings_label.setWordWrap(True)

        self._snapshot_blockers_label = QLabel(
            "Blockers: —",
            self._proportioning_input_snapshot_card,
        )
        self._snapshot_blockers_label.setWordWrap(True)

        snapshot_layout.addWidget(self._snapshot_title_label, 0, 0, 1, 4)

        snapshot_layout.addWidget(self._snapshot_status_label, 1, 0)
        snapshot_layout.addWidget(self._snapshot_sections_label, 1, 1)
        snapshot_layout.addWidget(self._snapshot_routes_label, 1, 2)
        snapshot_layout.addWidget(self._snapshot_returns_label, 1, 3)

        snapshot_layout.addWidget(self._snapshot_readiness_label, 2, 0, 1, 4)
        snapshot_layout.addWidget(self._snapshot_warnings_label, 3, 0, 1, 4)
        snapshot_layout.addWidget(self._snapshot_blockers_label, 4, 0, 1, 4)
        # --------------------------------------------------
        # H-S20-C — Preliminary route balancing requirement
        # --------------------------------------------------
        self._preliminary_route_balancing_table = self._make_table(
            columns=[
                "Route",
                "Sections",
                "Chosen Δp",
                "Controlling Δp",
                "Shortfall",
                "Required added resistance",
                "Controlling",
                "Status",
            ],
            stretch_columns={0, 7},
        )

        self._preliminary_route_balancing_table.setSelectionMode(
            QAbstractItemView.NoSelection
        )
        self._preliminary_route_balancing_table.setFocusPolicy(Qt.NoFocus)

        self._preliminary_route_balancing_table.cellClicked.connect(
            self._on_preliminary_route_balancing_cell_clicked
        )

        self._add_section(
            proportioning_layout,
            title="Preliminary route balancing requirement — preview only",
            table=self._preliminary_route_balancing_table,
            min_height=150,
            expanded=False,
        )

        # --------------------------------------------------
        # H-S20-E — Balancing point assumption
        # --------------------------------------------------
        self._balancing_point_assumption_card = QFrame(self)
        self._balancing_point_assumption_card.setFrameShape(QFrame.StyledPanel)
        self._balancing_point_assumption_card.setMinimumHeight(48)
        self._balancing_point_assumption_card.setMaximumHeight(64)

        balancing_point_layout = QGridLayout(
            self._balancing_point_assumption_card
        )
        balancing_point_layout.setContentsMargins(8, 4, 8, 4)
        balancing_point_layout.setHorizontalSpacing(16)
        balancing_point_layout.setVerticalSpacing(2)

        self._balancing_point_title_label = QLabel(
            "Balancing point assumption — v1 preview only",
            self._balancing_point_assumption_card,
        )
        # --------------------------------------------------
        # H-S20-F — Preliminary balancing resistance basis
        # --------------------------------------------------
        self._preliminary_balancing_resistance_table = self._make_table(
            columns=[
                "Route",
                "Sections",
                "Flow kg/s",
                "Required added Δp",
                "Resistance basis",
                "Controlling",
                "Status",
            ],
            stretch_columns={0, 4, 6},
        )

        self._preliminary_balancing_resistance_table.setSelectionMode(
            QAbstractItemView.NoSelection
        )
        self._preliminary_balancing_resistance_table.setFocusPolicy(Qt.NoFocus)

        self._preliminary_balancing_resistance_table.cellClicked.connect(
            self._on_preliminary_balancing_resistance_cell_clicked
        )

        self._add_section(
            proportioning_layout,
            title="Preliminary balancing resistance basis — preview only",
            table=self._preliminary_balancing_resistance_table,
            min_height=130,
            expanded=False,
        )


        self._balancing_point_title_label.setStyleSheet("font-weight: 600;")

        self._balancing_point_scope_label = QLabel(
            "Scope: route/subleg",
            self._balancing_point_assumption_card,
        )
        self._balancing_point_location_label = QLabel(
            "Application: route/subleg balancing point",
            self._balancing_point_assumption_card,
        )
        self._balancing_point_status_label = QLabel(
            "No valve selected | no room-level control | no ProjectState mutation",
            self._balancing_point_assumption_card,
        )

        balancing_point_layout.addWidget(
            self._balancing_point_title_label,
            0,
            0,
            1,
            3,
        )
        balancing_point_layout.addWidget(
            self._balancing_point_scope_label,
            1,
            0,
        )
        balancing_point_layout.addWidget(
            self._balancing_point_location_label,
            1,
            1,
        )
        balancing_point_layout.addWidget(
            self._balancing_point_status_label,
            1,
            2,
        )

        self._add_section(
            proportioning_layout,
            title="Balancing point assumption — v1 preview only",
            table=self._balancing_point_assumption_card,
            min_height=64,
            expanded=True,
        )

        self._add_section(
            proportioning_layout,
            title="Proportioning input snapshot — read-only basis",
            table=self._proportioning_input_snapshot_card,
            min_height=118,
            expanded=False,
        )

        # --------------------------------------------------
        # H-S19-J — DEV common-main / leg / subleg topology table
        # Create now, add lower down after schematic + comparison.
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

        self._common_main_leg_subleg_table.setStyleSheet("""
    QTableWidget::item:selected {
        background-color: rgb(255, 238, 210);
    }
    """)

        # --------------------------------------------------
        # H-S19-K — DEV common-main / leg / subleg drawn schematic
        # --------------------------------------------------
        self._common_main_leg_subleg_schematic_widget = (
            CommonMainLegSublegSchematicWidgetV1(self)
        )

        self._common_main_leg_subleg_schematic_widget.set_focus_callback(
            self._on_common_main_leg_subleg_schematic_focus_requested
        )

        self._common_main_leg_subleg_schematic_scroll = QScrollArea(self)
        self._common_main_leg_subleg_schematic_scroll.setWidgetResizable(False)
        self._common_main_leg_subleg_schematic_scroll.setFrameShape(QFrame.NoFrame)
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
            min_height=300,
            expanded=True,
        )
        # --------------------------------------------------
        # H-S19-N-A — Current proportioning focus summary
        # --------------------------------------------------
        self._current_proportioning_focus_card = QFrame(self)
        self._current_proportioning_focus_card.setFrameShape(QFrame.StyledPanel)
        self._current_proportioning_focus_card.setMinimumHeight(72)
        self._current_proportioning_focus_card.setMaximumHeight(96)

        focus_layout = QGridLayout(self._current_proportioning_focus_card)
        focus_layout.setContentsMargins(8, 6, 8, 6)
        focus_layout.setHorizontalSpacing(16)
        focus_layout.setVerticalSpacing(3)

        self._current_focus_title_label = QLabel(
            "Current focus — DEV preview only",
            self._current_proportioning_focus_card,
        )
        self._current_focus_title_label.setStyleSheet("font-weight: 600;")

        self._current_focus_route_label = QLabel("Route: —", self._current_proportioning_focus_card)
        self._current_focus_room_label = QLabel("Room: —", self._current_proportioning_focus_card)
        self._current_focus_emitter_label = QLabel("Emitter: —", self._current_proportioning_focus_card)

        self._current_focus_direct_dp_label = QLabel("F+R Δp: —", self._current_proportioning_focus_card)
        self._current_focus_reverse_dp_label = QLabel("F+RR Δp: —", self._current_proportioning_focus_card)
        self._current_focus_lower_label = QLabel("Lower: —", self._current_proportioning_focus_card)

        self._current_focus_status_label = QLabel(
            "Click a schematic room or F+R / F+RR comparison row",
            self._current_proportioning_focus_card,
        )
        self._current_focus_status_label.setWordWrap(True)

        focus_layout.addWidget(self._current_focus_title_label, 0, 0, 1, 3)

        focus_layout.addWidget(self._current_focus_route_label, 1, 0)
        focus_layout.addWidget(self._current_focus_room_label, 1, 1)
        focus_layout.addWidget(self._current_focus_emitter_label, 1, 2)

        focus_layout.addWidget(self._current_focus_direct_dp_label, 2, 0)
        focus_layout.addWidget(self._current_focus_reverse_dp_label, 2, 1)
        focus_layout.addWidget(self._current_focus_lower_label, 2, 2)

        focus_layout.addWidget(self._current_focus_status_label, 3, 0, 1, 3)

        self._add_section(
            proportioning_layout,
            title="Current proportioning focus — DEV preview only",
            table=self._current_proportioning_focus_card,
            min_height=96,
            expanded=True,
        )

        self._set_current_proportioning_focus_summary({})

        # --------------------------------------------------
        # H-S19-H / H-S19-L — Direct vs reverse return comparison
        # Immediate working table below schematic.
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
                "RR add L",
                "RR add Δp",
                "RR suitability",
                "Status",
            ],
            stretch_columns={0, 1, 2, 11, 12},
        )

        self._return_path_comparison_table.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self._return_path_comparison_table.cellClicked.connect(
            self._on_return_path_comparison_cell_clicked
        )

        self._add_section(
            proportioning_layout,
            title="Direct vs reverse return circuit comparison — preview only",
            table=self._return_path_comparison_table,
            min_height=180,
            expanded=True,
        )

        # ==================================================
        # H-S20-A — Proportioned tab shell
        # ==================================================
        self._proportioned_status_table = self._make_table(
            columns=[
                "Item",
                "Status",
            ],
            stretch_columns={1},
        )
        self._proportioned_status_table.setMaximumHeight(155)
        self._proportioned_status_table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Maximum,
        )

        self._add_section(
            proportioned_layout,
            title="Proportioned system — final output",
            table=self._proportioned_status_table,
            min_height=105,
        )

        # --------------------------------------------------
        # H-S27-B — Resolved return-arrangement basis
        # --------------------------------------------------
        self._effective_return_arrangement_basis_table = self._make_table(
            columns=[
                "Scope",
                "Target",
                "Effective basis",
                "Source",
                "Status",
            ],
            stretch_columns={1, 4},
        )

        self._add_section(
            proportioned_layout,
            title="Resolved return arrangement basis — read-only",
            table=self._effective_return_arrangement_basis_table,
            min_height=130,
            expanded=False,
        )

        self.set_effective_return_arrangement_basis_rows([])
        # --------------------------------------------------
        # H-S27-C — Chosen-basis route pressure preview
        # --------------------------------------------------
        self._chosen_basis_route_pressure_preview_table = self._make_table(
            columns=[
                "Scope",
                "Route",
                "Basis",
                "Chosen Δp",
                "Alternative Δp",
                "Difference",
                "Source",
                "Status",
            ],
            stretch_columns={1, 7},
        )

        self._add_section(
            proportioned_layout,
            title="Chosen-basis route Δp preview — read-only",
            table=self._chosen_basis_route_pressure_preview_table,
            min_height=145,
            expanded=False,
        )

        self.set_chosen_basis_route_pressure_preview_rows([])


        # --------------------------------------------------
        # H-S27-D — Chosen-basis controlling route preview
        # --------------------------------------------------
        self._chosen_basis_controlling_route_preview_table = self._make_table(
            columns=[
                "Scope",
                "Route",
                "Basis",
                "Chosen Δp",
                "Controlling",
                "Required added Δp",
                "Source",
                "Status",
            ],
            stretch_columns={1, 7},
        )

        self._add_section(
            proportioned_layout,
            title="Chosen-basis controlling / shortfall preview — read-only",
            table=self._chosen_basis_controlling_route_preview_table,
            min_height=130,
            expanded=False,
        )

        self.set_chosen_basis_controlling_route_preview_rows([])

        # --------------------------------------------------
        # H-S30-C — Provisional proportioning burden
        # --------------------------------------------------
        self._provisional_proportioning_burden_table = self._make_table(
            columns=[
                "Rank",
                "Route",
                "Basis",
                "Flow kg/s",
                "Chosen Δp",
                "Controlling",
                "Required added Δp",
                "Resistance Pa/(kg/s)²",
                "Action",
                "Status",
            ],
            stretch_columns={1, 8, 9},
        )

        self._add_section(
            proportioned_layout,
            title="Provisional proportioning burden — read-only",
            table=self._provisional_proportioning_burden_table,
            min_height=145,
            expanded=True,
        )

        self.set_provisional_proportioning_burden_rows([])

        # --------------------------------------------------
        # H-S31-D — Balancing method candidates
        # --------------------------------------------------
        self._balancing_method_candidate_table = self._make_table(
            columns=[
                "Route",
                "Method",
                "Ready",
                "Controlling",
                "Required added Δp",
                "Flow kg/s",
                "Resistance Pa/(kg/s)²",
                "Status",
                "Blockers",
            ],
            stretch_columns={0, 1, 7, 8},
        )

        self._add_section(
            proportioned_layout,
            title="Balancing method candidates — read-only",
            table=self._balancing_method_candidate_table,
            min_height=145,
            expanded=True,
        )

        self.set_balancing_method_candidate_rows([])

        # --------------------------------------------------
        # H-S32-D — Valve authority input preview
        # --------------------------------------------------
        self._valve_authority_input_table = self._make_table(
            columns=[
                "Route",
                "Balancing method",
                "Authority band",
                "Ready",
                "Design valve Δp",
                "Flow kg/s",
                "Candidate resistance",
                "Controlled circuit Δp",
                "Authority",
                "Status",
                "Blockers",
            ],
            stretch_columns={0, 1, 2, 9, 10},
        )

        self._add_section(
            proportioned_layout,
            title="Valve authority preview — read-only",
            table=self._valve_authority_input_table,
            min_height=145,
            expanded=True,
        )

        self.set_valve_authority_input_rows([])

        # --------------------------------------------------
        # H-S44-E — point allocation / method / valve-duty evidence
        # --------------------------------------------------
        self._balancing_point_evidence_table = self._make_table(
            columns=[
                "Point",
                "Scope",
                "Role",
                "Topology",
                "Governed routes",
                "Flow kg/s",
                "Allocated Δp",
                "Resistance Pa/(kg/s)²",
                "Method",
                "Valve duty",
                "Controlled circuit Δp",
                "Authority",
                "Ready",
                "Status",
                "Blockers",
            ],
            stretch_columns={0, 4, 8, 9, 13, 14},
        )
        self._add_section(
            proportioned_layout,
            title=(
                "Main / leg / subleg balancing-point evidence — read-only"
            ),
            table=self._balancing_point_evidence_table,
            min_height=165,
            expanded=True,
        )
        self.set_balancing_point_evidence_rows([])

        # --------------------------------------------------
        # H-S27-F — Chosen-basis proportioned readiness summary
        # --------------------------------------------------
        self._chosen_basis_proportioned_readiness_table = self._make_table(
            columns=[
                "Item",
                "Status",
            ],
            stretch_columns={1},
        )

        self._add_section(
            proportioned_layout,
            title="Chosen-basis proportioned readiness — read-only",
            table=self._chosen_basis_proportioned_readiness_table,
            min_height=120,
            expanded=False,
        )

        self.set_chosen_basis_proportioned_readiness_rows([])

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

        # ==================================================
        # Overview tab
        # ==================================================
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
            min_height=175,
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

        # ==================================================
        # Authority tab
        # ==================================================
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

        # ==================================================
        # Proportioning tab — lower diagnostic/detail area
        # ==================================================
        # --------------------------------------------------
        # H-S26-I — Return arrangement acceptance tabs / panel wiring
        # --------------------------------------------------
        self._return_arrangement_acceptance_widget = QWidget(self)

        return_acceptance_layout = QVBoxLayout(
            self._return_arrangement_acceptance_widget
        )
        return_acceptance_layout.setContentsMargins(8, 8, 8, 8)
        return_acceptance_layout.setSpacing(6)

        self._scoped_return_arrangement_acceptance_callback = None
        self._rr_length_basis_mode_callback = None
        self._rr_manual_extra_length_callback = None
        self._scoped_rr_length_basis_callback = None
        self._return_arrangement_scope_controls = {}
        self._leg_rr_added_length_basis_modes = {}
        self._leg_rr_added_lengths_m = {}
        self._subleg_rr_added_length_basis_modes = {}
        self._subleg_rr_added_lengths_m = {}

        self._return_arrangement_tabs = QTabWidget(
            self._return_arrangement_acceptance_widget
        )
        self._return_arrangement_tabs.tabBar().setExpanding(False)
        self._return_arrangement_tabs.tabBar().setUsesScrollButtons(False)
        self._return_arrangement_tabs.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed,
        )
        self._return_arrangement_tabs.setMinimumWidth(620)
        self._return_arrangement_tabs.setMaximumWidth(760)

        # ----------------------------------------------
        # System tab — existing persisted system-wide basis
        # ----------------------------------------------
        system_tab = QWidget(self._return_arrangement_tabs)
        system_layout = QVBoxLayout(system_tab)
        system_layout.setContentsMargins(6, 6, 6, 6)
        system_layout.setSpacing(12)

        self._return_arrangement_button_group = QButtonGroup(self)
        self._return_arrangement_button_group.setExclusive(True)

        self._return_arrangement_undecided_radio = QRadioButton(
            "Undecided",
            system_tab,
        )
        self._return_arrangement_direct_radio = QRadioButton(
            "F&R",
            system_tab,
        )
        self._return_arrangement_reverse_radio = QRadioButton(
            "F+RR",
            system_tab,
        )

        self._return_arrangement_direct_radio.setToolTip(
            "Direct return / flow and return same route sense."
        )
        self._return_arrangement_reverse_radio.setToolTip(
            "Reverse return / reverse-return arrangement."
        )

        self._return_arrangement_button_group.addButton(
            self._return_arrangement_undecided_radio
        )
        self._return_arrangement_button_group.addButton(
            self._return_arrangement_direct_radio
        )
        self._return_arrangement_button_group.addButton(
            self._return_arrangement_reverse_radio
        )

        self._return_arrangement_undecided_radio.setChecked(True)

        system_radio_layout = QHBoxLayout()
        system_radio_layout.setSpacing(10)
        system_radio_layout.addWidget(
            self._return_arrangement_undecided_radio
        )
        system_radio_layout.addWidget(
            self._return_arrangement_direct_radio
        )
        system_radio_layout.addWidget(
            self._return_arrangement_reverse_radio
        )
        system_radio_layout.addStretch(1)

        self._return_arrangement_pressure_evidence_label = QLabel(
            self._return_arrangement_acceptance_widget,
        )
        self._return_arrangement_pressure_evidence_label.setWordWrap(False)
        self._return_arrangement_pressure_evidence_label.setFrameShape(
            QFrame.StyledPanel
        )
        self._return_arrangement_pressure_evidence_label.setMinimumWidth(430)
        self._return_arrangement_pressure_evidence_label.setMaximumWidth(560)
        self._return_arrangement_pressure_evidence_label.setMinimumHeight(130)
        self._return_arrangement_pressure_evidence_label.setMaximumHeight(195)
        self._return_arrangement_pressure_evidence_label.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Maximum,
        )
        self._return_arrangement_pressure_evidence_label.setText(
            "Pressure evidence — preview only\n\n"
            "F&R controlling Δp:      TBA\n"
            "F+RR controlling Δp:     TBA\n"
            "Route Δp change:         TBA\n\n"
            "F&R prelim. balancing burden:    TBA\n"
            "F+RR prelim. balancing burden:   TBA\n"
            "Prelim. burden evidence:         TBA\n\n"
            "RR length basis:         TBA\n"
            "RR extra length:         TBA\n"
            "RR extra Δp:             TBA\n"
            "Evidence guidance:       TBA"
        )

        system_layout.addLayout(system_radio_layout)
        system_layout.addStretch(1)

        self._return_arrangement_scope_controls["SYSTEM"] = {
            "layout": system_layout,
        }

        self._return_arrangement_tabs.addTab(
            system_tab,
            "System",
        )

        # ----------------------------------------------
        # Scoped override tabs
        # ----------------------------------------------
        def _make_scoped_override_tab(
                *,
                scope_key: str,
                target_label: str,
                inherit_label: str,
                parent_visible: bool = False,
        ) -> QWidget:
            tab = QWidget(self._return_arrangement_tabs)
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(6)

            target_row = QHBoxLayout()
            target_row.setSpacing(8)

            label = QLabel(target_label, tab)
            combo = QComboBox(tab)
            combo.setMinimumWidth(180)
            combo.setMaximumWidth(260)
            combo.setSizePolicy(
                QSizePolicy.Fixed,
                QSizePolicy.Fixed,
            )
            combo.addItem("No targets yet", "")

            target_row.addWidget(label, 0)
            target_row.addWidget(combo, 0)
            target_row.addStretch(1)

            layout.addLayout(target_row)

            parent_label = QLabel("", tab)
            parent_label.setWordWrap(True)
            parent_label.setVisible(parent_visible)
            layout.addWidget(parent_label)

            group = QButtonGroup(self)
            group.setExclusive(True)

            inherit_radio = QRadioButton(inherit_label, tab)
            direct_radio = QRadioButton("F&R", tab)
            reverse_radio = QRadioButton("F+RR", tab)

            group.addButton(inherit_radio)
            group.addButton(direct_radio)
            group.addButton(reverse_radio)

            inherit_radio.setChecked(True)

            radio_row = QHBoxLayout()
            radio_row.setSpacing(10)
            radio_row.addWidget(inherit_radio)
            radio_row.addWidget(direct_radio)
            radio_row.addWidget(reverse_radio)
            radio_row.addStretch(1)

            layout.addLayout(radio_row)

            # H-S38-A2 — RR length authority is grouped with the matching
            # arrangement scope. Lower scopes explicitly inherit or override.
            rr_length_row = QHBoxLayout()
            rr_length_row.setSpacing(8)

            rr_basis_label = QLabel("RR length basis:", tab)
            rr_basis_combo = QComboBox(tab)
            rr_basis_combo.setMinimumWidth(230)
            rr_basis_combo.setMaximumWidth(320)
            rr_basis_combo.addItem(inherit_label, "INHERIT")
            rr_basis_combo.addItem(
                "Physical loop — no extra allowance",
                "physical_loop_zero_extra",
            )
            rr_basis_combo.addItem(
                "Downstream proxy allowance",
                "downstream_proxy",
            )
            rr_basis_combo.addItem("Manual allowance", "manual_allowance")

            rr_length_label = QLabel("Extra length:", tab)
            rr_length_spin = QDoubleSpinBox(tab)
            rr_length_spin.setDecimals(2)
            rr_length_spin.setRange(0.0, 9999.0)
            rr_length_spin.setSingleStep(0.25)
            rr_length_spin.setSuffix(" m")
            rr_length_spin.setMinimumWidth(105)
            rr_length_spin.setMaximumWidth(135)

            rr_length_row.addWidget(rr_basis_label)
            rr_length_row.addWidget(rr_basis_combo)
            rr_length_row.addSpacing(8)
            rr_length_row.addWidget(rr_length_label)
            rr_length_row.addWidget(rr_length_spin)
            rr_length_row.addStretch(1)

            rr_status_label = QLabel(
                "RR length basis inherits its parent.",
                tab,
            )
            rr_status_label.setWordWrap(True)

            layout.addLayout(rr_length_row)
            layout.addWidget(rr_status_label)
            layout.addStretch(1)

            self._return_arrangement_scope_controls[scope_key] = {
                "layout": layout,
                "combo": combo,
                "group": group,
                "inherit_radio": inherit_radio,
                "direct_radio": direct_radio,
                "reverse_radio": reverse_radio,
                "parent_label": parent_label,
                "rr_basis_label": rr_basis_label,
                "rr_basis_combo": rr_basis_combo,
                "rr_length_label": rr_length_label,
                "rr_length_spin": rr_length_spin,
                "rr_status_label": rr_status_label,
            }

            combo.currentIndexChanged.connect(
                lambda _index, scope_key=scope_key:
                self._on_scoped_return_arrangement_target_changed(
                    scope_key
                )
            )

            inherit_radio.toggled.connect(
                lambda checked, scope_key=scope_key: checked
                and self._on_scoped_return_arrangement_acceptance_changed(
                    scope_key,
                    "INHERIT",
                )
            )
            direct_radio.toggled.connect(
                lambda checked, scope_key=scope_key: checked
                and self._on_scoped_return_arrangement_acceptance_changed(
                    scope_key,
                    "DIRECT_RETURN",
                )
            )
            reverse_radio.toggled.connect(
                lambda checked, scope_key=scope_key: checked
                and self._on_scoped_return_arrangement_acceptance_changed(
                    scope_key,
                    "REVERSE_RETURN",
                )
            )

            rr_basis_combo.currentIndexChanged.connect(
                lambda _index, scope_key=scope_key:
                self._on_scoped_rr_length_basis_changed(scope_key)
            )
            rr_length_spin.valueChanged.connect(
                lambda _value, scope_key=scope_key:
                self._on_scoped_rr_length_basis_changed(scope_key)
            )

            return tab

        self._return_arrangement_tabs.addTab(
            _make_scoped_override_tab(
                scope_key="LEG",
                target_label="Leg:",
                inherit_label="Inherit system",
            ),
            "Leg",
        )

        self._return_arrangement_tabs.addTab(
            _make_scoped_override_tab(
                scope_key="COMMON_SUBLEG",
                target_label="Common subleg:",
                inherit_label="Inherit leg/system",
            ),
            "Common",
        )

        self._return_arrangement_tabs.addTab(
            _make_scoped_override_tab(
                scope_key="BRANCH_SUBLEG",
                target_label="Branch subleg:",
                inherit_label="Inherit parent",
                parent_visible=True,
            ),
            "Branch",
        )

        # H-S26-I9:
        # Keep the acceptance tabs compact, then place Commit Proportioning
        # immediately to the right of the tab group. This reads as:
        # choose basis -> review evidence -> commit.
        # --------------------------------------------------
        # H-S29-M — RR length basis mode control
        # --------------------------------------------------
        rr_length_basis_layout = QHBoxLayout()
        rr_length_basis_layout.setContentsMargins(0, 0, 0, 0)
        rr_length_basis_layout.setSpacing(8)

        self._rr_length_basis_mode_label = QLabel(
            "RR length basis:",
            self._return_arrangement_acceptance_widget,
        )

        self._rr_length_basis_mode_combo = QComboBox(
            self._return_arrangement_acceptance_widget
        )
        self._rr_length_basis_mode_combo.setMinimumWidth(260)
        self._rr_length_basis_mode_combo.setMaximumWidth(360)
        self._rr_length_basis_mode_combo.addItem(
            "Physical loop — no extra allowance",
            "physical_loop_zero_extra",
        )
        self._rr_length_basis_mode_combo.addItem(
            "Downstream proxy allowance",
            "downstream_proxy",
        )
        self._rr_length_basis_mode_combo.addItem(
            "Manual allowance",
            "manual_allowance",
        )
        self._rr_length_basis_mode_combo.setToolTip(
            "Preview-only reverse-return extra length basis. "
            "Manual metre entry is enabled only for Manual allowance."
        )

        self._rr_manual_extra_length_label = QLabel(
            "Extra length:",
            self._return_arrangement_acceptance_widget,
        )
        self._rr_manual_extra_length_spin = QDoubleSpinBox(
            self._return_arrangement_acceptance_widget
        )
        self._rr_manual_extra_length_spin.setDecimals(2)
        self._rr_manual_extra_length_spin.setRange(0.0, 9999.0)
        self._rr_manual_extra_length_spin.setSingleStep(0.25)
        self._rr_manual_extra_length_spin.setSuffix(" m")
        self._rr_manual_extra_length_spin.setMinimumWidth(110)
        self._rr_manual_extra_length_spin.setMaximumWidth(140)
        self._rr_manual_extra_length_spin.setToolTip(
            "Manual reverse-return extra pipe length allowance. "
            "Enabled only when RR length basis is Manual allowance."
        )
        self._rr_manual_extra_length_spin.valueChanged.connect(
            self._on_rr_manual_extra_length_changed
        )

        self._rr_length_basis_mode_combo.currentIndexChanged.connect(
            self._on_rr_length_basis_mode_changed
        )

        self._rr_length_basis_status_label = QLabel(
            "System RR length basis.",
            self._return_arrangement_acceptance_widget,
        )
        self._rr_length_basis_status_label.setWordWrap(True)

        rr_length_basis_layout.addWidget(self._rr_length_basis_mode_label)
        rr_length_basis_layout.addWidget(self._rr_length_basis_mode_combo)
        rr_length_basis_layout.addSpacing(12)
        rr_length_basis_layout.addWidget(self._rr_manual_extra_length_label)
        rr_length_basis_layout.addWidget(self._rr_manual_extra_length_spin)
        rr_length_basis_layout.addStretch(1)

        self._update_rr_manual_extra_length_enabled()

        return_tabs_row = QHBoxLayout()
        return_tabs_row.setContentsMargins(0, 0, 0, 0)
        return_tabs_row.setSpacing(8)

        return_tabs_row.addWidget(
            self._return_arrangement_tabs,
            0,
            Qt.AlignLeft | Qt.AlignTop,
        )

        self._return_arrangement_scope_key_by_tab_index = {
            0: "SYSTEM",
            1: "LEG",
            2: "COMMON_SUBLEG",
            3: "BRANCH_SUBLEG",
        }
        self._return_arrangement_tabs.currentChanged.connect(
            self._on_return_arrangement_tab_changed
        )

        self._move_return_arrangement_evidence_label_to_current_tab()

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        self._return_arrangement_acceptance_status_label = QLabel(
            "Evidence is guidance only — user design basis remains authoritative. No pump, valve, balancing, or pipe resizing.",
            self,
        )
        self._return_arrangement_acceptance_status_label.setWordWrap(True)

        self._commit_proportioning_button = QPushButton(
            "Commit Proportioning",
            self._return_arrangement_acceptance_widget,
        )
        self._commit_proportioning_button.setMinimumWidth(150)
        self._commit_proportioning_button.setMaximumWidth(190)
        self._commit_proportioning_button.clicked.connect(
            self._on_commit_proportioning_button_clicked
        )

        return_tabs_row.addWidget(
            self._commit_proportioning_button,
            0,
            Qt.AlignLeft | Qt.AlignBottom,
        )
        return_tabs_row.addStretch(1)

        # H-S38-A2 — The former global RR length row is now the
        # backward-compatible System editor inside the System tab.
        system_layout.insertLayout(1, rr_length_basis_layout)
        system_layout.insertWidget(2, self._rr_length_basis_status_label)
        self._return_arrangement_scope_controls["SYSTEM"].update(
            {
                "rr_basis_label": self._rr_length_basis_mode_label,
                "rr_basis_combo": self._rr_length_basis_mode_combo,
                "rr_length_label": self._rr_manual_extra_length_label,
                "rr_length_spin": self._rr_manual_extra_length_spin,
                "rr_status_label": self._rr_length_basis_status_label,
            }
        )
        return_acceptance_layout.addLayout(return_tabs_row)

        footer_layout.addWidget(
            self._return_arrangement_acceptance_status_label,
            1,
        )
        return_acceptance_layout.addLayout(footer_layout)

        self.set_commit_proportioning_ready(
            ready=False,
            reason=(
                "Accept a Direct or Reverse return arrangement basis before "
                "committing proportioning."
            ),
        )

        self._return_arrangement_undecided_radio.toggled.connect(
            lambda checked: checked
            and self._on_system_return_arrangement_acceptance_changed(
                "UNDECIDED"
            )
        )
        self._return_arrangement_direct_radio.toggled.connect(
            lambda checked: checked
            and self._on_system_return_arrangement_acceptance_changed(
                "DIRECT_RETURN"
            )
        )
        self._return_arrangement_reverse_radio.toggled.connect(
            lambda checked: checked
            and self._on_system_return_arrangement_acceptance_changed(
                "REVERSE_RETURN"
            )
        )
        for rr_arrangement_radio in (
            self._return_arrangement_undecided_radio,
            self._return_arrangement_direct_radio,
            self._return_arrangement_reverse_radio,
        ):
            rr_arrangement_radio.toggled.connect(
                lambda _checked: self._update_rr_manual_extra_length_enabled()
            )

        self._add_section(
            proportioning_layout,
            title="Return arrangement acceptance — user design basis",
            table=self._return_arrangement_acceptance_widget,
            min_height=210,
            expanded=True,
        )
        # --------------------------------------------------
        # Proportioning readiness
        # --------------------------------------------------
        self._proportioning_readiness_widget = QWidget(self)
        proportioning_readiness_layout = QVBoxLayout(
            self._proportioning_readiness_widget
        )
        proportioning_readiness_layout.setContentsMargins(0, 0, 0, 0)
        proportioning_readiness_layout.setSpacing(6)

        self._proportioning_readiness_table = self._make_table(
            columns=[
                "Item",
                "Value",
            ],
            stretch_columns={1},
        )
        proportioning_readiness_layout.addWidget(
            self._proportioning_readiness_table
        )

        self._add_section(
            proportioning_layout,
            title="Proportioning readiness — received from Basic",
            table=self._proportioning_readiness_widget,
            min_height=215,
            expanded=False,
        )

        # --------------------------------------------------
        # H-S25-C — Hydronic topology authority audit
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
            title="Hydronic topology authority audit — branch-aware basis",
            table=self._proportioning_table,
            min_height=220,
            expanded=False,
        )

        # --------------------------------------------------
        # H-S25-D — Selected route trace schematic
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
            title="Selected route trace — boiler → index",
            table=self._proportioning_schematic_scroll,
            min_height=300,
            expanded=False,
        )

        # --------------------------------------------------
        # H-S37-B5 — Basic selection vs Proportioning pressure evidence
        # --------------------------------------------------
        self._proportioning_basic_ps_sections_table = self._make_table(
            columns=[
                "Order",
                "From",
                "To",
                "Q carried",
                "Flow kg/s",
                "Basic pipe",
                "Basic v",
                "Max v",
                "v source",
                "Basic basis",
                "Prop v",
                "Prop Δp/m",
                "Prop Re",
                "Prop f",
                "Prop method",
                "Iter",
                "Length",
                "K",
                "Local Δp",
                "Straight Δp",
                "Section Δp",
                "Status",
            ],
            stretch_columns={1, 2, 8, 21},
        )
        self._proportioning_basic_ps_sections_table.cellClicked.connect(
            self._on_basic_ps_velocity_section_table_clicked_v1
        )

        self._add_section(
            proportioning_layout,
            title=(
                "Basic PS selection + Proportioning / Local K evidence"
            ),
            table=self._proportioning_basic_ps_sections_table,
            min_height=180,
            expanded=False,
        )

        # --------------------------------------------------
        # H-S37-B4 — Local section maximum-velocity editor
        # --------------------------------------------------
        velocity_editor = QFrame(self)
        velocity_editor.setFrameShape(QFrame.StyledPanel)
        velocity_layout = QGridLayout(velocity_editor)
        velocity_layout.setContentsMargins(8, 8, 8, 8)
        velocity_layout.setHorizontalSpacing(10)
        velocity_layout.setVerticalSpacing(6)

        velocity_notice = QLabel(
            "Select one stable Basic PS section. Changing the value does "
            "nothing until Apply is pressed; Clear restores Environment "
            "inheritance for this section only.",
            velocity_editor,
        )
        velocity_notice.setWordWrap(True)
        velocity_layout.addWidget(velocity_notice, 0, 0, 1, 4)

        velocity_layout.addWidget(QLabel("Local section:", velocity_editor), 1, 0)
        self._basic_ps_velocity_section_combo = QComboBox(velocity_editor)
        self._basic_ps_velocity_section_combo.currentIndexChanged.connect(
            self._on_basic_ps_velocity_section_changed_v1
        )
        velocity_layout.addWidget(
            self._basic_ps_velocity_section_combo,
            1,
            1,
            1,
            3,
        )

        velocity_layout.addWidget(QLabel("Section ID:", velocity_editor), 2, 0)
        self._basic_ps_velocity_section_id_label = QLabel("—", velocity_editor)
        self._basic_ps_velocity_section_id_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        velocity_layout.addWidget(
            self._basic_ps_velocity_section_id_label,
            2,
            1,
            1,
            3,
        )

        velocity_layout.addWidget(
            QLabel("Environment default:", velocity_editor),
            3,
            0,
        )
        self._basic_ps_velocity_environment_label = QLabel("—", velocity_editor)
        velocity_layout.addWidget(
            self._basic_ps_velocity_environment_label,
            3,
            1,
        )

        velocity_layout.addWidget(
            QLabel("Local override:", velocity_editor),
            3,
            2,
        )
        self._basic_ps_velocity_override_spin = QDoubleSpinBox(velocity_editor)
        self._basic_ps_velocity_override_spin.setRange(0.10, 5.00)
        self._basic_ps_velocity_override_spin.setDecimals(2)
        self._basic_ps_velocity_override_spin.setSingleStep(0.05)
        self._basic_ps_velocity_override_spin.setSuffix(" m/s")
        velocity_layout.addWidget(
            self._basic_ps_velocity_override_spin,
            3,
            3,
        )

        velocity_layout.addWidget(QLabel("Effective basis:", velocity_editor), 4, 0)
        self._basic_ps_velocity_effective_label = QLabel("—", velocity_editor)
        self._basic_ps_velocity_effective_label.setWordWrap(True)
        velocity_layout.addWidget(
            self._basic_ps_velocity_effective_label,
            4,
            1,
            1,
            3,
        )

        self._basic_ps_velocity_apply_button = QPushButton(
            "Apply to this section",
            velocity_editor,
        )
        self._basic_ps_velocity_clear_button = QPushButton(
            "Clear local override — inherit Environment",
            velocity_editor,
        )
        self._basic_ps_velocity_apply_button.clicked.connect(
            self._on_apply_basic_ps_velocity_override_v1
        )
        self._basic_ps_velocity_clear_button.clicked.connect(
            self._on_clear_basic_ps_velocity_override_v1
        )
        velocity_layout.addWidget(
            self._basic_ps_velocity_apply_button,
            5,
            2,
        )
        velocity_layout.addWidget(
            self._basic_ps_velocity_clear_button,
            5,
            3,
        )
        velocity_layout.setColumnStretch(1, 1)
        velocity_layout.setColumnStretch(3, 1)

        self._add_section(
            proportioning_layout,
            title="Local section maximum velocity — authority editor",
            table=velocity_editor,
            min_height=175,
            expanded=True,
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
            expanded=False,
        )

        # --------------------------------------------------
        # H-S18 — Route Δp shortfall preview
        # --------------------------------------------------
        self._route_shortfall_preview_table = self._make_table(
            columns=[
                "Rank",
                "Route",
                "Chosen Δp",
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
            expanded=False,
        )

        # --------------------------------------------------
        # H-S19-J — DEV common-main / leg / subleg topology evidence
        # --------------------------------------------------
        self._add_section(
            proportioning_layout,
            title="DEV common-main / leg / subleg topology — preview only",
            table=self._common_main_leg_subleg_table,
            min_height=160,
            expanded=False,
        )

        proportioning_layout.addStretch(1)

    def _refresh_proportioning_input_snapshot(self) -> None:
        """
        H-S20-A2:
        Build the read-only proportioning input snapshot from current
        workbench rows.

        Authority boundary:
        • no ProjectState mutation
        • no balancing
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        snapshot = build_proportioning_input_snapshot_v1(
            section_rows=getattr(
                self,
                "_proportioning_snapshot_section_rows",
                [],
            ),
            route_rows=getattr(
                self,
                "_proportioning_snapshot_route_rows",
                [],
            ),
            shortfall_rows=getattr(
                self,
                "_proportioning_snapshot_shortfall_rows",
                [],
            ),
            return_comparison_rows=getattr(
                self,
                "_proportioning_snapshot_return_comparison_rows",
                [],
            ),
        )

        self._proportioning_input_snapshot = snapshot

        gate = evaluate_proportioning_readiness_v1(snapshot)
        self._proportioning_readiness_gate = gate

        self._set_proportioning_input_snapshot_summary(snapshot, gate)

        preview = build_preliminary_route_balancing_preview_v1(snapshot)

        self._preliminary_route_balancing_preview = preview
        self._set_preliminary_route_balancing_preview(preview)
        resistance_basis = build_preliminary_balancing_resistance_basis_v1(
            snapshot=snapshot,
            balancing_preview=preview,
        )
        self._preliminary_balancing_resistance_basis = resistance_basis
        self._set_preliminary_balancing_resistance_basis(resistance_basis)

    def _set_preliminary_balancing_resistance_basis(
            self,
            basis: PreliminaryBalancingResistanceBasisV1 | None,
    ) -> None:
        """
        H-S20-F:
        Display preliminary route/subleg balancing resistance basis.

        Preview only:
        • no ProjectState mutation
        • no valve selection
        • no Kv/Kvs selection
        • no lockshield setting
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        table = getattr(self, "_preliminary_balancing_resistance_table", None)
        if table is None:
            return

        if basis is None:
            self._preliminary_balancing_resistance_focus_by_row = {}
            self._preliminary_balancing_resistance_row_data_by_row = {}
            table.setRowCount(0)
            return

        rows = list(basis.rows or [])
        self._preliminary_balancing_resistance_focus_by_row = {}
        self._preliminary_balancing_resistance_row_data_by_row = {}
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            route_label = str(getattr(row, "route_label", "") or "")
            route_id = str(getattr(row, "route_id", "") or "")
            leg_id = str(getattr(row, "leg_id", "") or "")
            subleg_id = str(getattr(row, "subleg_id", "") or "")

            if not route_id and subleg_id:
                route_id = subleg_id

            self._preliminary_balancing_resistance_focus_by_row[row_index] = {
                "route": route_label,
                "route_label": route_label,
                "route_id": route_id,
                "leg_id": leg_id,
                "subleg_id": subleg_id,
            }

            self._preliminary_balancing_resistance_row_data_by_row[row_index] = {
                "source": "preliminary_resistance_basis",
                "route": route_label,
                "route_label": route_label,
                "route_id": route_id,
                "leg_id": leg_id,
                "subleg_id": subleg_id,
                "sections": str(getattr(row, "sections", "") or "—"),
                "flow_kg_s": str(getattr(row, "flow_kg_s", "") or "—"),
                "required_added_dp": str(getattr(row, "required_added_dp", "") or "—"),
                "resistance_basis": str(
                    getattr(row, "resistance_pa_per_kg_s2", "") or "—"
                ),
                "controlling": str(getattr(row, "controlling", "") or "No"),
                "status": str(getattr(row, "status", "") or basis.status or "—"),
            }

            values = [
                row.route_label or "—",
                row.sections or "—",
                row.flow_kg_s or "—",
                row.required_added_dp or "—",
                row.resistance_pa_per_kg_s2 or "—",
                row.controlling or "No",
                row.status or basis.status or "—",
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                if col_index == 5 and str(value).strip().lower() in (
                        "yes",
                        "true",
                        "1",
                ):
                    item.setForeground(QBrush(QColor(190, 110, 0)))

                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=110, max_height=170)
        table.scrollToTop()

    def _parse_pressure_pa_value(self, value) -> float | None:
        """
        H-S26-C:
        Best-effort parser for pressure values displayed in preview rows.
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value or "").strip()
        if not text or text == "—":
            return None

        text = (
            text.replace("Pa", "")
            .replace("pa", "")
            .replace(",", "")
            .strip()
        )

        try:
            return float(text)
        except ValueError:
            return None

    def _format_pressure_pa_value(self, value: float | None) -> str:
        """
        H-S26-C:
        Format pressure value for the system-wide pressure evidence summary.
        """
        if value is None:
            return "TBA"
        return f"{value:,.0f} Pa"

    def _return_row_pressure_value(
            self,
            row: dict,
            keys: tuple[str, ...],
    ) -> float | None:
        """
        H-S26-C:
        Read a pressure value from a return-comparison row using several
        possible key names, keeping this tolerant of current/future row shapes.
        """
        for key in keys:
            if key in row:
                value = self._parse_pressure_pa_value(row.get(key))
                if value is not None:
                    return value
        return None

    def _return_row_bool_value(
            self,
            row: dict,
            keys: tuple[str, ...],
    ) -> bool:
        """
        H-S26-C:
        Read a controlling flag from a return-comparison row.
        """
        for key in keys:
            if key not in row:
                continue

            value = row.get(key)

            if isinstance(value, bool):
                return value

            text = str(value or "").strip().lower()
            if text in {"true", "yes", "y", "1", "controlling", "index"}:
                return True

        return False

    @staticmethod
    def _return_arrangement_truthy(value) -> bool:
        if isinstance(value, bool):
            return value

        text = str(value or "").strip().lower()
        return text in {"true", "yes", "y", "1", "branch"}

    @staticmethod
    def _return_arrangement_row_value(
            row: dict,
            keys: tuple[str, ...],
            default: str = "",
    ) -> str:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return str(value)

        return default

    def _set_return_arrangement_override_targets(
            self,
            rows: list[dict] | None,
    ) -> None:
        """
        H-S26-I:
        Populate scoped return-arrangement target combos from the current
        common-main / leg / subleg topology rows.

        Panel only:
        • no ProjectState mutation
        • no pump / valve / balancing / pipe resize
        """
        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        if not controls:
            return

        rows = [
            dict(row or {})
            for row in (rows or [])
        ]

        leg_items: dict[str, str] = {}
        common_items: dict[str, str] = {}
        branch_items: dict[str, tuple[str, str]] = {}

        for row in rows:
            leg_id = self._return_arrangement_row_value(
                row,
                ("leg_id", "legId", "leg"),
            )
            leg_label = self._return_arrangement_row_value(
                row,
                ("leg_label", "legLabel", "leg"),
                leg_id,
            )

            if leg_id:
                leg_items.setdefault(
                    leg_id,
                    leg_label or leg_id,
                )

            subleg_id = self._return_arrangement_row_value(
                row,
                ("subleg_id", "sublegId", "subleg"),
            )
            subleg_label = self._return_arrangement_row_value(
                row,
                ("subleg_label", "sublegLabel", "subleg"),
                subleg_id,
            )
            parent_subleg_id = self._return_arrangement_row_value(
                row,
                ("parent_subleg_id", "parentSublegId"),
            )
            parent_subleg_label = self._return_arrangement_row_value(
                row,
                (
                    "parent_subleg_label",
                    "parentSublegLabel",
                    "parent_subleg",
                    "parent",
                ),
                parent_subleg_id,
            )

            role_text = self._return_arrangement_row_value(
                row,
                ("role", "subleg_role", "type"),
            ).lower()

            is_branch = (
                self._return_arrangement_truthy(
                    row.get("is_branch_subleg")
                )
                or bool(parent_subleg_id)
                or "branch" in role_text
                or "branch" in subleg_label.lower()
            )

            is_common = (
                bool(subleg_id)
                and not is_branch
                and (
                    "common" in role_text
                    or "common" in subleg_label.lower()
                    or "primary" in subleg_id.lower()
                )
            )

            if is_common:
                common_items.setdefault(
                    subleg_id,
                    subleg_label or subleg_id,
                )

            if is_branch:
                branch_items.setdefault(
                    subleg_id,
                    (
                        subleg_label or subleg_id,
                        parent_subleg_label or "Parent: TBA",
                        parent_subleg_id,
                    ),
                )

        def populate_combo(
                scope_key: str,
                items,
        ) -> None:
            control = controls.get(scope_key, {})
            combo = control.get("combo")
            if combo is None:
                return

            combo.blockSignals(True)
            try:
                combo.clear()

                if not items:
                    combo.addItem("No targets", "")
                    combo.setEnabled(False)
                else:
                    for item in items:
                        if len(item) == 2:
                            label, value = item
                        else:
                            label, value, _parent = item
                        combo.addItem(label, value)

                    combo.setEnabled(True)

            finally:
                combo.blockSignals(False)

        populate_combo(
            "LEG",
            [
                (label, key)
                for key, label in leg_items.items()
            ],
        )
        populate_combo(
            "COMMON_SUBLEG",
            [
                (label, key)
                for key, label in common_items.items()
            ],
        )
        populate_combo(
            "BRANCH_SUBLEG",
            [
                (label, key, parent_label)
                for key, (label, parent_label, _parent_id)
                in branch_items.items()
            ],
        )

        branch_control = controls.get("BRANCH_SUBLEG", {})
        branch_combo = branch_control.get("combo")
        branch_parent_label = branch_control.get("parent_label")

        if branch_combo is not None:
            branch_combo.setProperty(
                "parent_labels_by_id",
                {
                    key: parent_label
                    for key, (_label, parent_label, _parent_id)
                    in branch_items.items()
                },
            )
            branch_combo.setProperty(
                "parent_ids_by_id",
                {
                    key: parent_id
                    for key, (_label, _parent_label, parent_id)
                    in branch_items.items()
                },
            )

        if branch_parent_label is not None:
            branch_parent_label.setVisible(True)

        self._on_scoped_return_arrangement_target_changed(
            "BRANCH_SUBLEG"
        )

        for scope_key, control in controls.items():
            combo = control.get("combo")
            enabled = bool(
                combo is not None
                and combo.isEnabled()
                and str(combo.currentData() or "")
            )

            for key in (
                "inherit_radio",
                "direct_radio",
                "reverse_radio",
            ):
                radio = control.get(key)
                if radio is not None:
                    radio.setEnabled(enabled)

    def _on_scoped_return_arrangement_target_changed(
            self,
            scope_key: str,
    ) -> None:
        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        control = controls.get(scope_key, {})

        combo = control.get("combo")
        parent_label = control.get("parent_label")

        if scope_key == "BRANCH_SUBLEG" and parent_label is not None:
            parent_text = "Parent: TBA"

            if combo is not None:
                target_id = str(combo.currentData() or "")
                parent_labels = combo.property("parent_labels_by_id") or {}
                parent_value = parent_labels.get(target_id)

                if parent_value:
                    parent_text = f"Parent: {parent_value}"

            parent_label.setText(parent_text)

        self._apply_scoped_return_arrangement_selection_for_scope(scope_key)
        self._apply_scoped_rr_length_basis_selection_for_scope(scope_key)
        self._refresh_return_arrangement_evidence_for_current_scope()

    def set_scoped_rr_length_basis_callback(self, callback) -> None:
        """H-S38-A2 adapter callback for one scoped RR length edit."""
        self._scoped_rr_length_basis_callback = callback

    def set_scoped_rr_length_basis_overrides(
            self,
            *,
            leg_basis_modes: dict[str, str],
            leg_lengths_m: dict[str, float],
            subleg_basis_modes: dict[str, str],
            subleg_lengths_m: dict[str, float],
    ) -> None:
        """Restore scoped RR length intent without emitting user changes."""
        self._leg_rr_added_length_basis_modes = dict(leg_basis_modes or {})
        self._leg_rr_added_lengths_m = dict(leg_lengths_m or {})
        self._subleg_rr_added_length_basis_modes = dict(
            subleg_basis_modes or {}
        )
        self._subleg_rr_added_lengths_m = dict(subleg_lengths_m or {})

        for scope_key in ("LEG", "COMMON_SUBLEG", "BRANCH_SUBLEG"):
            self._apply_scoped_rr_length_basis_selection_for_scope(scope_key)

    def _apply_scoped_rr_length_basis_selection_for_scope(
            self,
            scope_key: str,
    ) -> None:
        control = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        ).get(scope_key, {})
        target_combo = control.get("combo")
        basis_combo = control.get("rr_basis_combo")
        length_spin = control.get("rr_length_spin")

        if target_combo is None or basis_combo is None or length_spin is None:
            return

        target_id = str(target_combo.currentData() or "")
        if scope_key == "LEG":
            modes = getattr(self, "_leg_rr_added_length_basis_modes", {})
            lengths = getattr(self, "_leg_rr_added_lengths_m", {})
        else:
            modes = getattr(self, "_subleg_rr_added_length_basis_modes", {})
            lengths = getattr(self, "_subleg_rr_added_lengths_m", {})

        mode = str(modes.get(target_id, "INHERIT") or "INHERIT")
        try:
            added_length_m = max(float(lengths.get(target_id, 0.0)), 0.0)
        except (TypeError, ValueError):
            added_length_m = 0.0

        basis_index = basis_combo.findData(mode)
        if basis_index < 0:
            basis_index = basis_combo.findData("INHERIT")

        basis_combo.blockSignals(True)
        length_spin.blockSignals(True)
        try:
            basis_combo.setCurrentIndex(max(basis_index, 0))
            length_spin.setValue(added_length_m)
        finally:
            length_spin.blockSignals(False)
            basis_combo.blockSignals(False)

        self._update_scoped_rr_length_controls_enabled(scope_key)

    def _update_scoped_rr_length_controls_enabled(
            self,
            scope_key: str,
    ) -> None:
        control = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        ).get(scope_key, {})
        target_combo = control.get("combo")
        basis_combo = control.get("rr_basis_combo")
        basis_label = control.get("rr_basis_label")
        length_spin = control.get("rr_length_spin")
        length_label = control.get("rr_length_label")
        status_label = control.get("rr_status_label")

        if target_combo is None or basis_combo is None or length_spin is None:
            return

        has_target = bool(str(target_combo.currentData() or ""))
        direct_selected = bool(
            control.get("direct_radio") is not None
            and control["direct_radio"].isChecked()
        )
        mode = str(basis_combo.currentData() or "INHERIT")
        rr_editable = has_target and not direct_selected
        manual_editable = rr_editable and mode == "manual_allowance"

        basis_combo.setEnabled(rr_editable)
        length_spin.setEnabled(manual_editable)
        if basis_label is not None:
            basis_label.setEnabled(rr_editable)
        if length_label is not None:
            length_label.setEnabled(manual_editable)

        if status_label is not None:
            if not has_target:
                status = "Select a stable scope target."
            elif direct_selected:
                status = "RR length basis is dormant while this scope is F&R."
            elif mode == "INHERIT":
                status = "RR length basis inherits its parent authority."
            elif mode == "manual_allowance":
                status = "Explicit Manual RR allowance for this scope."
            else:
                status = "Explicit RR length basis for this scope."
            status_label.setText(status)

    def _on_scoped_rr_length_basis_changed(self, scope_key: str) -> None:
        control = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        ).get(scope_key, {})
        target_combo = control.get("combo")
        basis_combo = control.get("rr_basis_combo")
        length_spin = control.get("rr_length_spin")

        if target_combo is None or basis_combo is None or length_spin is None:
            return

        target_id = str(target_combo.currentData() or "")
        if not target_id:
            return

        parent_id = ""
        if scope_key == "BRANCH_SUBLEG":
            parent_ids = target_combo.property("parent_ids_by_id") or {}
            parent_id = str(parent_ids.get(target_id) or "")

        mode = str(basis_combo.currentData() or "INHERIT")
        self._update_scoped_rr_length_controls_enabled(scope_key)

        callback = getattr(self, "_scoped_rr_length_basis_callback", None)
        if callback is not None:
            callback(
                {
                    "scope": scope_key,
                    "target_id": target_id,
                    "target_label": str(target_combo.currentText() or ""),
                    "parent_subleg_id": parent_id,
                    "basis_mode": mode,
                    "added_length_m": float(length_spin.value()),
                }
            )

    def set_scoped_return_arrangement_acceptance_callback(
            self,
            callback,
    ) -> None:
        """
        H-S26-I:
        Adapter callback for scoped return-arrangement overrides.
        """
        self._scoped_return_arrangement_acceptance_callback = callback

    def _on_scoped_return_arrangement_acceptance_changed(
            self,
            scope_key: str,
            basis: str,
    ) -> None:
        """
        H-S26-I:
        User-facing scoped return-arrangement override.

        Override only:
        • no room/subleg exclusion
        • no pump / valve / balancing / pipe resize
        """
        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        control = controls.get(scope_key, {})

        combo = control.get("combo")
        target_id = ""
        target_label = ""

        if combo is not None:
            target_id = str(combo.currentData() or "")
            target_label = str(combo.currentText() or "")

        if not target_id:
            return

        callback = getattr(
            self,
            "_scoped_return_arrangement_acceptance_callback",
            None,
        )

        self._update_scoped_rr_length_controls_enabled(scope_key)
        self._refresh_return_arrangement_evidence_for_current_scope()

        if callback is not None:
            callback(
                scope_key,
                target_id,
                target_label,
                basis,
            )

    def _current_return_arrangement_scope_key(self) -> str:
        tabs = getattr(
            self,
            "_return_arrangement_tabs",
            None,
        )
        if tabs is None:
            return "SYSTEM"

        index = int(tabs.currentIndex())
        mapping = getattr(
            self,
            "_return_arrangement_scope_key_by_tab_index",
            {},
        )

        return str(mapping.get(index, "SYSTEM") or "SYSTEM")

    def _current_return_arrangement_scope_target(self) -> tuple[str, str]:
        scope_key = self._current_return_arrangement_scope_key()

        if scope_key == "SYSTEM":
            return "", "System"

        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        control = controls.get(scope_key, {})
        combo = control.get("combo")

        if combo is None:
            return "", "—"

        return (
            str(combo.currentData() or ""),
            str(combo.currentText() or "—"),
        )

    def _current_return_arrangement_basis_label(self) -> str:
        scope_key = self._current_return_arrangement_scope_key()

        if scope_key == "SYSTEM":
            if getattr(
                    self,
                    "_return_arrangement_direct_radio",
                    None,
            ) is not None and self._return_arrangement_direct_radio.isChecked():
                return "F&R"

            if getattr(
                    self,
                    "_return_arrangement_reverse_radio",
                    None,
            ) is not None and self._return_arrangement_reverse_radio.isChecked():
                return "F+RR"

            return "Undecided"

        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        control = controls.get(scope_key, {})

        if (
                control.get("direct_radio") is not None
                and control["direct_radio"].isChecked()
        ):
            return "F&R"

        if (
                control.get("reverse_radio") is not None
                and control["reverse_radio"].isChecked()
        ):
            return "F+RR"

        return "Inherit"

    def _return_arrangement_evidence_heading(self) -> str:
        scope_key = self._current_return_arrangement_scope_key()
        target_id, target_label = self._current_return_arrangement_scope_target()
        basis_label = self._current_return_arrangement_basis_label()

        if scope_key == "SYSTEM":
            return f"System — pressure evidence ({basis_label})"

        if scope_key == "LEG":
            return f"Leg {target_label} — pressure evidence ({basis_label})"

        if scope_key == "COMMON_SUBLEG":
            return (
                f"Common subleg {target_label} — pressure evidence "
                f"({basis_label})"
            )

        if scope_key == "BRANCH_SUBLEG":
            return (
                f"Branch subleg {target_label} — pressure evidence "
                f"({basis_label})"
            )

        return "Pressure evidence — preview only"

    def _return_arrangement_filtered_evidence_rows(self) -> list[dict]:
        rows = [
            dict(row or {})
            for row in getattr(
                self,
                "_proportioning_snapshot_return_comparison_rows",
                [],
            )
        ]

        scope_key = self._current_return_arrangement_scope_key()
        target_id, _target_label = self._current_return_arrangement_scope_target()

        if scope_key == "SYSTEM":
            return rows

        if not target_id:
            return []

        if scope_key == "LEG":
            return [
                row
                for row in rows
                if str(row.get("leg_id", "") or "") == target_id
            ]

        if scope_key in {"COMMON_SUBLEG", "BRANCH_SUBLEG"}:
            return [
                row
                for row in rows
                if (
                    str(row.get("subleg_id", "") or "") == target_id
                    or str(row.get("route_id", "") or "") == target_id
                )
            ]

        return rows

    def _refresh_return_arrangement_evidence_for_current_scope(self) -> None:
        self._set_return_arrangement_pressure_evidence_summary(
            self._return_arrangement_filtered_evidence_rows(),
            heading=self._return_arrangement_evidence_heading(),
        )

    def _on_return_arrangement_tab_changed(
            self,
            _index: int,
    ) -> None:
        self._move_return_arrangement_evidence_label_to_current_tab()
        self._refresh_return_arrangement_evidence_for_current_scope()

    def set_scoped_return_arrangement_acceptance_basis(
            self,
            *,
            leg_arrangements: dict | None = None,
            subleg_arrangements: dict | None = None,
    ) -> None:
        """
        H-S26-I6:
        Restore persisted scoped return-arrangement overrides into the tab
        controls after project load / refresh.

        Panel only:
            no ProjectState mutation here.
        """
        self._scoped_return_arrangement_leg_arrangements = {
            str(key): str(value)
            for key, value in dict(leg_arrangements or {}).items()
        }
        self._scoped_return_arrangement_subleg_arrangements = {
            str(key): str(value)
            for key, value in dict(subleg_arrangements or {}).items()
        }

        for scope_key in (
                "LEG",
                "COMMON_SUBLEG",
                "BRANCH_SUBLEG",
        ):
            self._apply_scoped_return_arrangement_selection_for_scope(
                scope_key
            )

        self._refresh_return_arrangement_evidence_for_current_scope()

    def _scoped_return_arrangement_basis_for_target(
            self,
            scope_key: str,
            target_id: str,
    ) -> str:
        scope_key = str(scope_key or "").strip().upper()
        target_id = str(target_id or "").strip()

        if not target_id:
            return "INHERIT"

        if scope_key == "LEG":
            source = getattr(
                self,
                "_scoped_return_arrangement_leg_arrangements",
                {},
            )
        else:
            source = getattr(
                self,
                "_scoped_return_arrangement_subleg_arrangements",
                {},
            )

        basis = str(source.get(target_id, "INHERIT") or "INHERIT").upper()

        if basis not in {
                "INHERIT",
                "DIRECT_RETURN",
                "REVERSE_RETURN",
        }:
            return "INHERIT"

        return basis

    def _apply_scoped_return_arrangement_selection_for_scope(
            self,
            scope_key: str,
    ) -> None:
        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        control = controls.get(scope_key, {})

        combo = control.get("combo")
        if combo is None:
            return

        target_id = str(combo.currentData() or "")
        basis = self._scoped_return_arrangement_basis_for_target(
            scope_key,
            target_id,
        )

        radio_map = {
            "INHERIT": control.get("inherit_radio"),
            "DIRECT_RETURN": control.get("direct_radio"),
            "REVERSE_RETURN": control.get("reverse_radio"),
        }

        radios = [
            radio
            for radio in radio_map.values()
            if radio is not None
        ]

        for radio in radios:
            radio.blockSignals(True)

        try:
            wanted = radio_map.get(
                basis,
                radio_map.get("INHERIT"),
            )
            if wanted is not None:
                wanted.setChecked(True)
        finally:
            for radio in radios:
                radio.blockSignals(False)

    def _return_arrangement_current_scope_layout(self):
        scope_key = self._current_return_arrangement_scope_key()
        controls = getattr(
            self,
            "_return_arrangement_scope_controls",
            {},
        )
        return controls.get(scope_key, {}).get("layout")

    def _move_return_arrangement_evidence_label_to_current_tab(self) -> None:
        """
        H-S26-I7:
        Keep the pressure-evidence box inside the active acceptance tab.

        Layout only:
            no ProjectState mutation.
        """
        label = getattr(
            self,
            "_return_arrangement_pressure_evidence_label",
            None,
        )
        if label is None:
            return

        layout = self._return_arrangement_current_scope_layout()
        if layout is None:
            return

        previous_layout = getattr(
            self,
            "_return_arrangement_evidence_layout",
            None,
        )
        if previous_layout is not None and previous_layout is not layout:
            previous_layout.removeWidget(label)

        # Insert before the stretch item if the tab has one.
        insert_index = layout.count()
        if insert_index > 0:
            insert_index -= 1

        layout.insertWidget(
            insert_index,
            label,
            0,
        )
        self._return_arrangement_evidence_layout = layout
        label.show()

    def _set_return_arrangement_pressure_evidence_summary(
            self,
            rows: list[dict] | None = None,
            *,
            heading: str = "Pressure evidence — preview only",
    ) -> None:
        """
        H-S26-C:
        Show system-wide return arrangement pressure evidence beside the
        acceptance radio buttons.

        Evidence only:
        • no ProjectState persistence
        • no final Proportioned commit
        • no valve selection
        • no pump selection
        • no pipe resizing
        • no automatic choice from F+R / F+RR comparison evidence

        Balancing burden definition:
        Σ(max(controlling route Δp - circuit route Δp, 0))
        """
        label = getattr(
            self,
            "_return_arrangement_pressure_evidence_label",
            None,
        )
        if label is None:
            return

        rows = list(rows or [])

        direct_values: list[float] = []
        reverse_values: list[float] = []

        direct_controlling_values: list[float] = []
        reverse_controlling_values: list[float] = []

        for row in rows:
            row = dict(row or {})

            direct_dp = self._return_row_pressure_value(
                row,
                (
                    "direct_dp",
                    "direct_route_dp",
                    "direct_total_dp",
                    "direct_sigma_dp",
                    "direct_ΣΔp",
                    "Direct ΣΔp",
                    "F+R Δp",
                    "f_r_dp",
                ),
            )
            reverse_dp = self._return_row_pressure_value(
                row,
                (
                    "reverse_dp",
                    "reverse_route_dp",
                    "reverse_total_dp",
                    "reverse_sigma_dp",
                    "reverse_ΣΔp",
                    "Reverse ΣΔp",
                    "F+RR Δp",
                    "f_rr_dp",
                ),
            )

            if direct_dp is not None:
                direct_values.append(direct_dp)

                if self._return_row_bool_value(
                        row,
                        (
                            "direct_controlling",
                            "Direct Controlling",
                            "direct_is_controlling",
                            "F+R Ctrl",
                            "f_r_ctrl",
                        ),
                ):
                    direct_controlling_values.append(direct_dp)

            if reverse_dp is not None:
                reverse_values.append(reverse_dp)

                if self._return_row_bool_value(
                        row,
                        (
                            "reverse_controlling",
                            "Reverse Controlling",
                            "reverse_is_controlling",
                            "F+RR Ctrl",
                            "f_rr_ctrl",
                        ),
                ):
                    reverse_controlling_values.append(reverse_dp)

        direct_controlling_dp = (
            max(direct_controlling_values)
            if direct_controlling_values
            else (max(direct_values) if direct_values else None)
        )
        reverse_controlling_dp = (
            max(reverse_controlling_values)
            if reverse_controlling_values
            else (max(reverse_values) if reverse_values else None)
        )

        direct_burden = None
        if direct_controlling_dp is not None and direct_values:
            direct_burden = sum(
                max(direct_controlling_dp - value, 0.0)
                for value in direct_values
            )

        reverse_burden = None
        if reverse_controlling_dp is not None and reverse_values:
            reverse_burden = sum(
                max(reverse_controlling_dp - value, 0.0)
                for value in reverse_values
            )

        controlling_change_text = "TBA"
        if (
                direct_controlling_dp is not None
                and reverse_controlling_dp is not None
        ):
            controlling_delta = direct_controlling_dp - reverse_controlling_dp

            if controlling_delta > 0:
                controlling_change_text = (
                    f"{abs(controlling_delta):,.0f} Pa lower with F+RR"
                )
            elif controlling_delta < 0:
                controlling_change_text = (
                    f"{abs(controlling_delta):,.0f} Pa higher with F+RR"
                )
            else:
                controlling_change_text = "No change"

        balancing_reduction_text = "TBA"
        evidence_guidance = "Evidence guidance:                 TBA"

        if direct_burden is not None and reverse_burden is not None:
            burden_delta = direct_burden - reverse_burden

            if burden_delta > 0:
                balancing_reduction_text = f"{burden_delta:,.0f} Pa"
                evidence_guidance = (
                    "Evidence guidance:                 "
                    "F+RR shows lower preliminary imbalance evidence"
                )
            elif burden_delta < 0:
                balancing_reduction_text = (
                    f"{abs(burden_delta):,.0f} Pa higher with F+RR"
                )
                evidence_guidance = (
                    "Evidence guidance:                 "
                    "F&R shows lower preliminary imbalance evidence"
                )
            else:
                balancing_reduction_text = "No change"
                evidence_guidance = (
                    "Evidence guidance:                 "
                    "F&R and F+RR show no preliminary burden difference"
                )

        heading = str(heading or "Pressure evidence — preview only")

        (
            rr_length_basis_text,
            rr_extra_length_text,
            rr_extra_dp_text,
        ) = self._return_arrangement_rr_length_evidence_summary(
            self._return_arrangement_filtered_evidence_rows()
        )

        label.setText(
            f"{heading}\n\n"
            f"F&R controlling Δp:      "
            f"{self._format_pressure_pa_value(direct_controlling_dp)}\n"
            f"F+RR controlling Δp:     "
            f"{self._format_pressure_pa_value(reverse_controlling_dp)}\n"
            f"Route Δp change:         "
            f"{controlling_change_text}\n\n"
            f"F&R prelim. balancing burden:    "
            f"{self._format_pressure_pa_value(direct_burden)}\n"
            f"F+RR prelim. balancing burden:   "
            f"{self._format_pressure_pa_value(reverse_burden)}\n"
            f"Prelim. burden evidence:         "
            f"{balancing_reduction_text}\n\n"
            f"RR length basis:         {rr_length_basis_text}\n"
            f"RR extra length:         {rr_extra_length_text}\n"
            f"RR extra Δp:             {rr_extra_dp_text}\n"
            f"{evidence_guidance}"
        )

    def _return_arrangement_rr_length_evidence_summary(
            self,
            rows: list[dict],
    ) -> tuple[str, str, str]:
        """
        H-S29-L:
        Summarise RR length-basis evidence for the return-arrangement
        acceptance panel.

        Display only:
        • no ProjectState mutation
        • no manual entry yet
        • no pump / valve / balancing / pipe resize
        """
        rows = [dict(row or {}) for row in (rows or [])]

        if not rows:
            return "TBA", "TBA", "TBA"

        basis_text = self._return_arrangement_rr_length_basis_from_rows(rows)

        length_values = [
            value
            for value in (
                self._return_row_length_m_value(
                    row,
                    (
                        "rr_added_length",
                        "rr_added_length_m",
                        "rr_extra_length",
                        "rr_extra_length_m",
                    ),
                )
                for row in rows
            )
            if value is not None
        ]

        pressure_values = [
            value
            for value in (
                self._return_row_pressure_value(
                    row,
                    (
                        "rr_added_dp",
                        "rr_added_pressure_drop_Pa",
                        "rr_extra_dp",
                        "rr_extra_pressure_drop_Pa",
                    ),
                )
                for row in rows
            )
            if value is not None
        ]

        length_text = (
            "TBA"
            if not length_values
            else f"{max(length_values):.2f} m"
        )

        pressure_text = (
            "TBA"
            if not pressure_values
            else self._format_pressure_pa_value(max(pressure_values))
        )

        return basis_text, length_text, pressure_text

    @staticmethod
    def _return_arrangement_rr_length_basis_from_rows(
            rows: list[dict],
    ) -> str:
        """
        Read the H-S29-K RR length basis from row status text or explicit
        future row keys.
        """
        for row in rows:
            for key in (
                    "rr_length_basis",
                    "rr_added_length_basis",
                    "rr_added_length_basis_mode",
            ):
                value = str(row.get(key) or "").strip()

                if value:
                    return value

            status = str(row.get("status") or "").strip()
            marker = "RR length basis:"

            if marker in status:
                value = status.split(marker, 1)[1].split(";", 1)[0].strip()

                if value:
                    return value

        return "Physical loop — no extra allowance"

    def _return_row_length_m_value(
            self,
            row: dict,
            keys: tuple[str, ...],
    ) -> float | None:
        for key in keys:
            if key not in row:
                continue

            value = self._parse_length_m_value(row.get(key))

            if value is not None:
                return value

        return None

    @staticmethod
    def _parse_length_m_value(value) -> float | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value or "").strip()

        if not text or text == "—":
            return None

        lowered = text.lower()

        if lowered in {"tba", "none", "not set"}:
            return None

        cleaned = (
            lowered.replace("metres", "")
            .replace("meters", "")
            .replace("meter", "")
            .replace("metre", "")
            .replace("m", "")
            .replace(",", "")
            .replace("max", "")
            .replace("extra", "")
            .strip()
        )

        try:
            return float(cleaned)
        except ValueError:
            return None


    @staticmethod
    def _normalise_rr_length_basis_mode_ui(mode: str) -> str:
        mode = (
            str(mode or "")
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if mode in {
                "downstream",
                "downstream_proxy",
                "derived_downstream",
                "downstream_allowance",
        }:
            return "downstream_proxy"

        if mode in {
                "manual",
                "manual_allowance",
                "manual_length",
                "manual_extra",
        }:
            return "manual_allowance"

        return "physical_loop_zero_extra"

    def set_rr_length_basis_mode_callback(self, callback) -> None:
        """
        H-S29-M:
        Adapter callback for user-selected RR added-length basis mode.
        """
        self._rr_length_basis_mode_callback = callback

    def set_rr_manual_extra_length_callback(self, callback) -> None:
        """
        H-S29-N:
        Adapter callback for user-entered manual RR extra length.
        """
        self._rr_manual_extra_length_callback = callback

    def set_rr_manual_extra_length_m(self, value: float) -> None:
        """
        H-S29-N:
        Restore/display manual RR extra length without emitting user intent.
        """
        spin = getattr(self, "_rr_manual_extra_length_spin", None)

        if spin is None:
            return

        try:
            parsed = max(float(value), 0.0)
        except (TypeError, ValueError):
            parsed = 0.0

        spin.blockSignals(True)
        try:
            spin.setValue(parsed)
        finally:
            spin.blockSignals(False)

    def _update_rr_manual_extra_length_enabled(self) -> None:
        """
        H-S29-N:
        Manual metre entry is editable only for Manual allowance.
        """
        combo = getattr(self, "_rr_length_basis_mode_combo", None)
        spin = getattr(self, "_rr_manual_extra_length_spin", None)
        label = getattr(self, "_rr_manual_extra_length_label", None)

        if combo is None or spin is None:
            return

        mode = self._normalise_rr_length_basis_mode_ui(
            str(combo.currentData() or "")
        )
        direct_selected = bool(
            getattr(self, "_return_arrangement_direct_radio", None)
            is not None
            and self._return_arrangement_direct_radio.isChecked()
        )
        rr_editable = not direct_selected
        enabled = rr_editable and mode == "manual_allowance"

        combo.setEnabled(rr_editable)
        spin.setEnabled(enabled)

        basis_label = getattr(self, "_rr_length_basis_mode_label", None)
        if basis_label is not None:
            basis_label.setEnabled(rr_editable)
        if label is not None:
            label.setEnabled(enabled)

        status_label = getattr(self, "_rr_length_basis_status_label", None)
        if status_label is not None:
            if direct_selected:
                status_label.setText(
                    "System RR length basis is dormant while F&R is selected."
                )
            elif mode == "manual_allowance":
                status_label.setText("System Manual RR allowance is active.")
            else:
                status_label.setText("System RR length basis is active for F+RR.")

    def _on_rr_manual_extra_length_changed(self, value: float) -> None:
        """
        H-S29-N:
        User-facing manual RR extra length entry.
        """
        callback = getattr(self, "_rr_manual_extra_length_callback", None)

        self._refresh_return_arrangement_evidence_for_current_scope()

        if callback is not None:
            callback(max(float(value), 0.0))

    def set_rr_length_basis_mode(self, mode: str) -> None:
        """
        H-S29-M:
        Restore/display RR length basis mode without treating it as a
        fresh user selection.
        """
        combo = getattr(self, "_rr_length_basis_mode_combo", None)

        if combo is None:
            return

        mode = self._normalise_rr_length_basis_mode_ui(mode)
        index = combo.findData(mode)

        if index < 0:
            index = combo.findData("physical_loop_zero_extra")

        combo.blockSignals(True)
        try:
            combo.setCurrentIndex(max(index, 0))
        finally:
            combo.blockSignals(False)

        self._update_rr_manual_extra_length_enabled()

    def _on_rr_length_basis_mode_changed(self, _index: int) -> None:
        """
        H-S29-M:
        User-facing RR length basis mode selection.

        Selection only:
        • no manual metre entry yet
        • no pump / valve / balancing / pipe resize
        • no final hydraulic result
        """
        combo = getattr(self, "_rr_length_basis_mode_combo", None)

        if combo is None:
            return

        mode = self._normalise_rr_length_basis_mode_ui(
            str(combo.currentData() or "")
        )

        self._update_rr_manual_extra_length_enabled()

        callback = getattr(self, "_rr_length_basis_mode_callback", None)

        self._refresh_return_arrangement_evidence_for_current_scope()

        if callback is not None:
            callback(mode)


    def set_system_return_arrangement_acceptance_basis(
            self,
            basis: str,
    ) -> None:
        """
        H-S26-D:
        Restore/display the persisted system-wide return arrangement basis
        without treating it as a fresh user click.

        Display only:
        • no ProjectState mutation here
        • no final Proportioned commit
        • no valve selection
        • no pump selection
        • no pipe resizing
        """
        basis = str(basis or "").strip().upper()

        radio_map = {
            "DIRECT_RETURN": getattr(
                self,
                "_return_arrangement_direct_radio",
                None,
            ),
            "REVERSE_RETURN": getattr(
                self,
                "_return_arrangement_reverse_radio",
                None,
            ),
            "UNDECIDED": getattr(
                self,
                "_return_arrangement_undecided_radio",
                None,
            ),
        }

        wanted_radio = radio_map.get(
            basis,
            radio_map.get("UNDECIDED"),
        )

        radios = [
            radio
            for radio in radio_map.values()
            if radio is not None
        ]

        for radio in radios:
            radio.blockSignals(True)

        try:
            if wanted_radio is not None:
                wanted_radio.setChecked(True)
        finally:
            for radio in radios:
                radio.blockSignals(False)

        # H-S29-M2:
        # When the adapter restores the accepted FR/F+RR basis with
        # signals blocked, the evidence heading/result must still refresh.
        self._refresh_return_arrangement_evidence_for_current_scope()

    def set_system_return_arrangement_acceptance_callback(self, callback) -> None:
        """
        H-S26-C:
        Adapter callback for user-accepted system return-arrangement basis.
        """
        self._system_return_arrangement_acceptance_callback = callback

    def _on_system_return_arrangement_acceptance_changed(
            self,
            basis: str,
    ) -> None:
        """
        H-S26-C:
        User-facing system return-arrangement acceptance.

        Design acceptance only:
        • no ProjectState persistence here
        • no final Proportioned commit
        • no valve selection
        • no pump selection
        • no pipe resizing
        • no automatic choice from F+R / F+RR comparison evidence
        """
        callback = getattr(
            self,
            "_system_return_arrangement_acceptance_callback",
            None,
        )

        self._refresh_return_arrangement_evidence_for_current_scope()

        if callback is not None:
            callback(basis)

        # H-S29-M2:
        # Keep the visible evidence box in step with the selected
        # FR/F+RR acceptance radio even before/after adapter refresh.
        self._refresh_return_arrangement_evidence_for_current_scope()

        # H-S29-M2:
        # Keep the visible evidence box in step with the selected
        # FR/F+RR acceptance radio even before/after adapter refresh.
        self._refresh_return_arrangement_evidence_for_current_scope()

    def _set_preliminary_route_balancing_preview(
            self,
            preview: PreliminaryRouteBalancingPreviewV1 | None,
    ) -> None:
        """
        H-S20-C:
        Display preliminary route balancing requirement preview.

        Preview only:
        • no ProjectState mutation
        • no balancing valve selection
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        table = getattr(self, "_preliminary_route_balancing_table", None)
        if table is None:
            return

        if preview is None:
            self._preliminary_route_balancing_focus_by_row = {}
            self._preliminary_route_balancing_row_data_by_row = {}
            table.setRowCount(0)
            return

        rows = list(preview.rows or [])
        table.setRowCount(len(rows))
        self._preliminary_route_balancing_focus_by_row = {}
        self._preliminary_route_balancing_row_data_by_row = {}

        for row_index, row in enumerate(rows):
            route_label = str(getattr(row, "route_label", "") or "")
            route_id = str(getattr(row, "route_id", "") or "")
            leg_id = str(getattr(row, "leg_id", "") or "")
            subleg_id = str(getattr(row, "subleg_id", "") or "")

            required_added_dp = (
                str(getattr(row, "required_added_resistance", "") or "")
                or str(getattr(row, "required_added_dp", "") or "")
                or str(getattr(row, "required_added_resistance_dp", "") or "")
                or str(getattr(row, "shortfall", "") or "")
                or "—"
            )

            self._preliminary_route_balancing_focus_by_row[row_index] = {
                "route_id": route_id,
                "route": route_label,
                "route_label": route_label,
                "leg_id": leg_id,
                "subleg_id": subleg_id,
                "room_id": "",
                "emitter_id": "",
            }

            self._preliminary_route_balancing_row_data_by_row[row_index] = {
                "source": "preliminary_route_balancing",
                "route": route_label,
                "route_label": route_label,
                "route_id": route_id,
                "leg_id": leg_id,
                "subleg_id": subleg_id,
                "sections": str(getattr(row, "sections", "") or "—"),
                "route_dp": str(getattr(row, "route_dp", "") or "—"),
                "controlling_route_dp": str(
                    getattr(row, "controlling_route_dp", "") or "—"
                ),
                "shortfall": str(getattr(row, "shortfall", "") or "—"),
                "required_added_dp": required_added_dp,
                "controlling": str(getattr(row, "controlling", "") or "No"),
                "status": str(getattr(row, "status", "") or "—"),
            }

            values = [
                row.route_label or "—",
                row.sections or "—",
                row.route_dp or "—",
                row.controlling_route_dp or "—",
                row.shortfall_dp or "—",
                row.required_added_resistance_dp or "—",
                row.controlling or "No",
                row.status or preview.status or "—",
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                if col_index == 6 and str(value).strip().lower() in (
                        "yes",
                        "true",
                        "1",
                ):
                    item.setForeground(QBrush(QColor(190, 110, 0)))
                if col_index == 6 and str(value).strip().lower() in ("yes", "true", "1"):
                    item.setForeground(QBrush(QColor(190, 110, 0)))
                table.setItem(row_index, col_index, item)


        self._fit_table_height(table, min_height=120, max_height=190)
        table.scrollToTop()

    def _set_proportioning_input_snapshot_summary(
            self,
            snapshot: ProportioningInputSnapshotV1 | None,
            gate: ProportioningReadinessGateV1 | None = None,
    ) -> None:
        """
        H-S20-A2:
        Display compact read-only snapshot status.
        """
        if not hasattr(self, "_snapshot_status_label"):
            return

        if snapshot is None:
            self._snapshot_status_label.setText("Status: Snapshot empty")
            self._snapshot_sections_label.setText("Sections: 0")
            self._snapshot_routes_label.setText("Routes: 0")
            self._snapshot_returns_label.setText("Return comparisons: 0")
            self._snapshot_warnings_label.setText("Warnings: —")
            self._snapshot_readiness_label.setText("Readiness: Not ready for proportioning")
            self._snapshot_blockers_label.setText("Blockers: No proportioning input snapshot is available")
            return

        self._snapshot_status_label.setText(f"Status: {snapshot.status}")
        self._snapshot_sections_label.setText(f"Sections: {len(snapshot.sections)}")
        self._snapshot_routes_label.setText(f"Routes: {len(snapshot.routes)}")
        self._snapshot_returns_label.setText(
            f"Return comparisons: {len(snapshot.return_comparisons)}"
        )

        if snapshot.warnings:
            self._snapshot_warnings_label.setText(
                "Warnings: " + " | ".join(snapshot.warnings)
            )
        else:
            self._snapshot_warnings_label.setText("Warnings: none")

        if gate is None:
            self._snapshot_readiness_label.setText(
                "Readiness: Not ready for proportioning"
            )
            self._snapshot_blockers_label.setText("Blockers: —")
        else:
            self._snapshot_readiness_label.setText(f"Readiness: {gate.status}")

            if gate.blockers:
                self._snapshot_blockers_label.setText(
                    "Blockers: " + " | ".join(gate.blockers)
                )
            else:
                self._snapshot_blockers_label.setText("Blockers: none")

    def _on_preliminary_balancing_resistance_cell_clicked(
            self,
            row_index: int,
            column_index: int,
    ) -> None:
        """
        H-S20-G:
        Manual focus from preliminary balancing resistance basis.

        Focus/link only:
        • no ProjectState mutation
        • no balancing valve selection
        • no Kv/Kvs selection
        • no lockshield setting
        • no pump selection
        • no pipe resizing
        """
        focus = getattr(
            self,
            "_preliminary_balancing_resistance_focus_by_row",
            {},
        ).get(row_index, {}) or {}

        self._focus_preliminary_balancing_resistance_row(row_index)
        self._focus_preliminary_route_balancing_row_by_focus(focus)

        comparison_row_index = self._focus_return_path_comparison_row_by_focus(focus)

        row_data = {}
        comparison_focus = {}

        if comparison_row_index is not None:
            row_data = getattr(
                self,
                "_return_path_row_data_by_row",
                {},
            ).get(comparison_row_index, {}) or {}

            comparison_focus = getattr(
                self,
                "_return_path_focus_by_row",
                {},
            ).get(comparison_row_index, {}) or {}

        if comparison_focus:
            self._focus_common_main_leg_subleg_row(comparison_focus)
        else:
            self._focus_common_main_leg_subleg_row(focus)

        self._set_current_proportioning_route_focus_summary(
            self._preliminary_route_focus_summary_from_focus(focus)
        )

    def _clear_preliminary_balancing_resistance_table_focus(self) -> None:
        table = getattr(self, "_preliminary_balancing_resistance_table", None)
        if table is None:
            return

        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item is not None:
                    item.setBackground(QBrush())

    def _focus_preliminary_balancing_resistance_row(
            self,
            row_index: int,
    ) -> None:
        table = getattr(self, "_preliminary_balancing_resistance_table", None)
        if table is None:
            return

        self._clear_preliminary_balancing_resistance_table_focus()

        if row_index < 0 or row_index >= table.rowCount():
            return

        focus_brush = QBrush(QColor(255, 238, 210))  # pale orange focus only

        for c in range(table.columnCount()):
            item = table.item(row_index, c)
            if item is not None:
                item.setBackground(focus_brush)

        first_item = table.item(row_index, 0)
        if first_item is not None:
            table.scrollToItem(
                first_item,
                QAbstractItemView.PositionAtCenter,
            )

    def _focus_preliminary_balancing_resistance_row_by_focus(
            self,
            focus: dict,
    ) -> int | None:
        """
        H-S20-G:
        Focus the balancing resistance-basis row from a route/subleg focus payload.
        """
        wanted_subleg_id = str((focus or {}).get("subleg_id", "") or "")
        wanted_route_id = str((focus or {}).get("route_id", "") or "")
        wanted_route = str((focus or {}).get("route", "") or "")

        row_map = getattr(
            self,
            "_preliminary_balancing_resistance_focus_by_row",
            {},
        ) or {}

        if wanted_subleg_id:
            for row_index, row_focus in row_map.items():
                row_subleg_id = str((row_focus or {}).get("subleg_id", "") or "")
                if row_subleg_id == wanted_subleg_id:
                    self._focus_preliminary_balancing_resistance_row(row_index)
                    return int(row_index)

        if wanted_route_id:
            for row_index, row_focus in row_map.items():
                row_route_id = str((row_focus or {}).get("route_id", "") or "")
                if row_route_id == wanted_route_id:
                    self._focus_preliminary_balancing_resistance_row(row_index)
                    return int(row_index)

        if wanted_route:
            for row_index, row_focus in row_map.items():
                row_route = str((row_focus or {}).get("route", "") or "")
                if self._route_label_matches(wanted_route, row_route):
                    self._focus_preliminary_balancing_resistance_row(row_index)
                    return int(row_index)

        self._clear_preliminary_balancing_resistance_table_focus()
        return None

    def _on_preliminary_route_balancing_cell_clicked(
            self,
            row_index: int,
            column_index: int,
    ) -> None:
        """
        H-S20-D:
        Manual focus from preliminary route balancing preview.

        Focus/link only:
        • no ProjectState mutation
        • no balancing valve selection
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        focus = getattr(
            self,
            "_preliminary_route_balancing_focus_by_row",
            {},
        ).get(row_index, {}) or {}

        self._focus_preliminary_route_balancing_row(row_index)
        self._focus_preliminary_balancing_resistance_row_by_focus(focus)

        comparison_row_index = self._focus_return_path_comparison_row_by_focus(focus)

        row_data = {}
        comparison_focus = {}

        if comparison_row_index is not None:
            row_data = getattr(
                self,
                "_return_path_row_data_by_row",
                {},
            ).get(comparison_row_index, {}) or {}

            comparison_focus = getattr(
                self,
                "_return_path_focus_by_row",
                {},
            ).get(comparison_row_index, {}) or {}

        if comparison_focus:
            self._focus_common_main_leg_subleg_row(comparison_focus)
        else:
            self._focus_common_main_leg_subleg_row(focus)

        self._set_current_proportioning_route_focus_summary(
            self._preliminary_route_focus_summary_from_focus(focus)
        )

    def _on_common_main_leg_subleg_schematic_focus_requested(
            self,
            focus: dict,
    ) -> None:
        """
        H-S19-M / H-S19-N-A:
        Receive room/subleg focus from DEV schematic click.

        Focus only:
        • no ProjectState mutation
        • no committed return arrangement
        • no balancing
        • no pipe resizing
        """
        self._focus_common_main_leg_subleg_row(focus)

        row_index = self._focus_return_path_comparison_row_by_focus(focus)
        row_data = {}

        if row_index is not None:
            row_data = getattr(
                self,
                "_return_path_row_data_by_row",
                {},
            ).get(row_index, {}) or {}

        balancing_focus = dict(focus)

        if row_data.get("route"):
            balancing_focus["route"] = str(row_data.get("route") or "")

        self._focus_preliminary_route_balancing_row_by_focus(balancing_focus)
        self._focus_preliminary_balancing_resistance_row_by_focus(balancing_focus)
        self._set_current_proportioning_focus_summary(row_data)

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

        self._proportioning_snapshot_section_rows = (
            enrich_basic_ps_section_rows_with_route_identity_v1(
                [
                    dict(row)
                    for row in (rows or [])
                ]
            )
        )

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
                row.get(
                    "basic_velocity_m_s",
                    row.get("velocity_m_s", "—"),
                ),
                row.get(
                    "basic_max_velocity_m_s",
                    row.get("applied_max_velocity_m_s", "—"),
                ),
                row.get(
                    "basic_velocity_source",
                    row.get("max_velocity_source", "—"),
                ),
                row.get(
                    "basic_friction_basis",
                    "Velocity selection / Haaland Δp",
                ),
                row.get("proportioning_velocity_m_s", "—"),
                row.get("proportioning_dp_per_m", "—"),
                row.get("proportioning_reynolds_number", "—"),
                row.get("proportioning_friction_factor", "—"),
                row.get("proportioning_friction_method", "—"),
                row.get("proportioning_colebrook_iterations", "—"),
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

        self._set_clean_proportioned_evidence_availability_v1(rows)
        self._set_basic_ps_velocity_editor_rows_v1(rows)
        self._refresh_proportioning_input_snapshot()
        self._fit_table_height(table, min_height=180, max_height=300)

        if not getattr(self, "_suppress_basic_ps_scroll_to_top", False):
            table.scrollToTop()

    def set_basic_ps_section_velocity_override_callback(
            self,
            callback,
    ) -> None:
        """Register the adapter-owned H-S37-B4 authority callback."""
        self._basic_ps_section_velocity_override_callback = callback

    @staticmethod
    def _basic_ps_velocity_optional_float_v1(value) -> float | None:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    def _set_basic_ps_velocity_editor_rows_v1(self, rows: list[dict]) -> None:
        combo = getattr(self, "_basic_ps_velocity_section_combo", None)
        if combo is None:
            return

        previous_section_id = str(
            combo.currentData()
            or getattr(self, "_basic_ps_velocity_selected_section_id", "")
            or ""
        )
        row_copies = [dict(row) for row in (rows or [])]
        self._basic_ps_velocity_editor_rows_by_section_id = {
            str(row.get("section_id") or ""): row
            for row in row_copies
            if str(row.get("section_id") or "")
        }
        self._basic_ps_velocity_editor_section_ids = [
            str(row.get("section_id") or "")
            for row in row_copies
        ]

        previous_signal_state = combo.blockSignals(True)
        try:
            combo.clear()
            for row in row_copies:
                section_id = str(row.get("section_id") or "")
                if not section_id:
                    continue
                route = str(row.get("route") or "Route")
                order = str(row.get("order") or "—")
                from_label = str(row.get("from") or "—")
                to_label = str(row.get("to") or "—")
                combo.addItem(
                    f"{route} | {order} — {from_label} → {to_label}",
                    section_id,
                )

            wanted_index = combo.findData(previous_section_id)
            if wanted_index < 0 and combo.count():
                wanted_index = 0
            combo.setCurrentIndex(wanted_index)
        finally:
            combo.blockSignals(previous_signal_state)

        self._on_basic_ps_velocity_section_changed_v1(combo.currentIndex())

    def _on_basic_ps_velocity_section_table_clicked_v1(
            self,
            row_index: int,
            _column_index: int,
    ) -> None:
        section_ids = getattr(
            self,
            "_basic_ps_velocity_editor_section_ids",
            [],
        )
        if not (0 <= row_index < len(section_ids)):
            return

        section_id = str(section_ids[row_index] or "")
        combo = getattr(self, "_basic_ps_velocity_section_combo", None)
        if combo is None or not section_id:
            return
        combo_index = combo.findData(section_id)
        if combo_index >= 0:
            combo.setCurrentIndex(combo_index)

    def _on_basic_ps_velocity_section_changed_v1(
            self,
            _index: int = -1,
    ) -> None:
        combo = getattr(self, "_basic_ps_velocity_section_combo", None)
        if combo is None:
            return

        section_id = str(combo.currentData() or "")
        rows_by_id = getattr(
            self,
            "_basic_ps_velocity_editor_rows_by_section_id",
            {},
        )
        row = rows_by_id.get(section_id, {})
        has_section = bool(section_id and row)
        self._basic_ps_velocity_selected_section_id = section_id

        section_id_label = self._basic_ps_velocity_section_id_label
        environment_label = self._basic_ps_velocity_environment_label
        effective_label = self._basic_ps_velocity_effective_label
        spin = self._basic_ps_velocity_override_spin
        apply_button = self._basic_ps_velocity_apply_button
        clear_button = self._basic_ps_velocity_clear_button

        if not has_section:
            section_id_label.setText("—")
            environment_label.setText("—")
            effective_label.setText("—")
            spin.setEnabled(False)
            apply_button.setEnabled(False)
            clear_button.setEnabled(False)
            return

        environment_value = self._basic_ps_velocity_optional_float_v1(
            row.get("environment_max_velocity_m_s")
        )
        local_value = self._basic_ps_velocity_optional_float_v1(
            row.get("local_max_velocity_override_m_s")
        )
        effective_value = self._basic_ps_velocity_optional_float_v1(
            row.get("applied_max_velocity_m_s")
        )
        source = str(row.get("max_velocity_source") or "—")

        section_id_label.setText(section_id)
        environment_label.setText(
            "—" if environment_value is None else f"{environment_value:.2f} m/s"
        )
        if local_value is not None:
            spin.setValue(local_value)
        elif environment_value is not None:
            spin.setValue(environment_value)
        elif effective_value is not None:
            spin.setValue(effective_value)

        effective_value_text = (
            "—" if effective_value is None else f"{effective_value:.2f} m/s"
        )
        local_state = (
            f"Local override {local_value:.2f} m/s"
            if local_value is not None
            else "No local override — inherits Environment"
        )
        effective_label.setText(
            f"{effective_value_text} — {source}. {local_state}."
        )
        spin.setEnabled(True)
        apply_button.setEnabled(True)
        clear_button.setEnabled(local_value is not None)
        self.focus_proportioning_basic_ps_section(section_id)

    def _on_apply_basic_ps_velocity_override_v1(self) -> None:
        section_id = str(
            getattr(self, "_basic_ps_velocity_selected_section_id", "") or ""
        )
        callback = getattr(
            self,
            "_basic_ps_section_velocity_override_callback",
            None,
        )
        if not section_id or not callable(callback):
            return
        callback(
            {
                "action": "set",
                "section_id": section_id,
                "max_velocity_m_s": float(
                    self._basic_ps_velocity_override_spin.value()
                ),
            }
        )

    def _on_clear_basic_ps_velocity_override_v1(self) -> None:
        section_id = str(
            getattr(self, "_basic_ps_velocity_selected_section_id", "") or ""
        )
        callback = getattr(
            self,
            "_basic_ps_section_velocity_override_callback",
            None,
        )
        if not section_id or not callable(callback):
            return
        callback(
            {
                "action": "clear",
                "section_id": section_id,
            }
        )

    def _preliminary_focus_row_matches(
            self,
            focus: dict,
            row: dict,
    ) -> bool:
        wanted_subleg_id = str((focus or {}).get("subleg_id", "") or "")
        wanted_route_id = str((focus or {}).get("route_id", "") or "")
        wanted_route = (
            str((focus or {}).get("route", "") or "")
            or str((focus or {}).get("route_label", "") or "")
        )

        row_subleg_id = str((row or {}).get("subleg_id", "") or "")
        row_route_id = str((row or {}).get("route_id", "") or "")
        row_route = (
            str((row or {}).get("route", "") or "")
            or str((row or {}).get("route_label", "") or "")
        )

        if wanted_subleg_id and row_subleg_id == wanted_subleg_id:
            return True

        if wanted_route_id and row_route_id == wanted_route_id:
            return True

        if wanted_route and row_route:
            return self._route_label_matches(wanted_route, row_route)

        return False

    def _preliminary_route_focus_summary_from_focus(
            self,
            focus: dict,
    ) -> dict:
        """
        H-S20-H:
        Build a route/subleg summary row from the preliminary balancing tables.

        Display only:
        • no ProjectState mutation
        • no valve selection
        • no Kv/Kvs
        • no lockshield setting
        • no pump selection
        • no pipe resizing
        """
        summary: dict = {}

        route_rows = getattr(
            self,
            "_preliminary_route_balancing_row_data_by_row",
            {},
        ) or {}

        resistance_rows = getattr(
            self,
            "_preliminary_balancing_resistance_row_data_by_row",
            {},
        ) or {}

        for row in route_rows.values():
            if self._preliminary_focus_row_matches(focus, row):
                summary.update(dict(row))
                break

        for row in resistance_rows.values():
            if self._preliminary_focus_row_matches(focus, row):
                resistance_row = dict(row)

                for key, value in resistance_row.items():
                    if key in ("flow_kg_s", "resistance_basis"):
                        summary[key] = value
                    elif not summary.get(key) or summary.get(key) == "—":
                        summary[key] = value

                break

        if not summary:
            summary = dict(focus or {})
            summary.setdefault("source", "preliminary_route_focus")

        return summary

    def _set_current_proportioning_route_focus_summary(
            self,
            row: dict | None,
    ) -> None:
        """
        H-S20-H:
        Display route/subleg balancing focus in the Current Focus card.

        This is separate from the room/emitter F+R vs F+RR focus summary.
        """
        if not hasattr(self, "_current_focus_route_label"):
            return

        row = row or {}

        route = (
            str(row.get("route", "") or "")
            or str(row.get("route_label", "") or "")
            or "—"
        )
        sections = str(row.get("sections", "—") or "—")
        flow = str(row.get("flow_kg_s", "—") or "—")
        route_dp = str(row.get("route_dp", "—") or "—")
        required_added_dp = str(row.get("required_added_dp", "—") or "—")
        resistance_basis = str(row.get("resistance_basis", "—") or "—")
        controlling = str(row.get("controlling", "—") or "—")
        status = str(row.get("status", "—") or "—")

        self._current_focus_route_label.setText(f"Route: {route}")
        self._current_focus_room_label.setText(
            "Scope: route/subleg balancing point"
        )
        self._current_focus_emitter_label.setText(
            f"Sections: {sections} | Flow: {flow}"
        )
        self._current_focus_direct_dp_label.setText(
            f"Route Δp: {route_dp}"
        )
        self._current_focus_reverse_dp_label.setText(
            f"Required added Δp: {required_added_dp}"
        )
        self._current_focus_lower_label.setText(
            f"Resistance basis: {resistance_basis}"
        )
        self._current_focus_status_label.setText(
            f"{status} | Controlling: {controlling} | "
            "DEV preview only — no valve selected"
        )

    def _set_current_proportioning_focus_summary(self, row: dict | None) -> None:
        """
        H-S19-N-A:
        Display the current proportioning focus summary.

        Display only:
        • no ProjectState mutation
        • no committed return arrangement
        • no balancing
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_current_focus_route_label"):
            return

        row = row or {}

        if not row:
            self._current_focus_route_label.setText("Route: —")
            self._current_focus_room_label.setText("Room: —")
            self._current_focus_emitter_label.setText("Emitter: —")
            self._current_focus_direct_dp_label.setText("F+R Δp: —")
            self._current_focus_reverse_dp_label.setText("F+RR Δp: —")
            self._current_focus_lower_label.setText("Lower: —")
            self._current_focus_status_label.setText(
                "Click a schematic room or F+R / F+RR comparison row"
            )
            return

        direct_dp = str(row.get("direct_total_dp", "—") or "—")
        reverse_dp = str(row.get("reverse_total_dp", "—") or "—")

        lower = "—"
        direct_raw = self._try_float(row.get("direct_total_dp_raw", None))
        reverse_raw = self._try_float(row.get("reverse_total_dp_raw", None))

        if direct_raw is not None and reverse_raw is not None:
            delta_percent = self._delta_percent(direct_raw, reverse_raw)
            if delta_percent <= self._RETURN_COMPARISON_TOLERANCE_PERCENT:
                lower = "Similar / within tolerance"
            elif direct_raw < reverse_raw:
                lower = "F+R"
            elif reverse_raw < direct_raw:
                lower = "F+RR"

        self._current_focus_route_label.setText(
            f"Route: {str(row.get('route', '—') or '—')}"
        )
        self._current_focus_room_label.setText(
            f"Room: {str(row.get('room', '—') or '—')}"
        )
        self._current_focus_emitter_label.setText(
            f"Emitter: {str(row.get('emitter', '—') or '—')}"
        )

        self._current_focus_direct_dp_label.setText(f"F+R Δp: {direct_dp}")
        self._current_focus_reverse_dp_label.setText(f"F+RR Δp: {reverse_dp}")
        self._current_focus_lower_label.setText(f"Lower: {lower}")

        status = str(row.get("status", "—") or "—")
        suitability = str(row.get("rr_suitability", "—") or "—")

        self._current_focus_status_label.setText(
            f"{suitability} | {status} | DEV preview only — no arrangement committed"
        )

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

        # H-S34-B:
        # Feed the same display-only DTO to the separate clean
        # Proportioned schematic instance. Focus state remains local to
        # each widget instance.
        clean_proportioned_schematic = getattr(
            self,
            "_clean_proportioned_common_main_leg_subleg_schematic_widget",
            None,
        )

        # H-S36-A2: keep the topology DTO as the immutable base for
        # a separate clean Proportioned evidence projection. The original
        # Proportioning schematic above remains topology-only.
        self._clean_proportioned_schematic_base_dto_v1 = schematic
        self._refresh_clean_proportioned_schematic_section_evidence_v1()

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
        # H-S26-I:
        # Feed the Return arrangement acceptance scoped target combos from
        # the same topology rows as the common-main / leg / subleg table.
        self._set_return_arrangement_override_targets(rows)

        if not hasattr(self, "_common_main_leg_subleg_table"):
            return

        table = self._common_main_leg_subleg_table
        table.setRowCount(len(rows))
        self._common_main_leg_subleg_table.setStyleSheet("""
        QTableWidget::item:selected {
            background-color: rgb(255, 238, 210);
            color: rgb(20, 20, 20);
        }
        """)
        for row_index, row in enumerate(rows):
            subleg_id = str(row.get("subleg_id", "") or "")
            if subleg_id:
                self._common_main_leg_subleg_row_by_subleg_id[subleg_id] = row_index
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
        Display route-level pressure preview rows.
        """
        if not hasattr(self, "_route_pressure_preview_table"):
            self._proportioning_snapshot_route_rows = []
            return

        self._proportioning_snapshot_route_rows = [
            dict(row)
            for row in (rows or [])
        ]

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
        self._configure_clean_proportioned_output_summary_table_v1()
        table.scrollToTop()
        self._refresh_proportioning_input_snapshot()

    def _focus_return_path_comparison_row_by_focus(
            self,
            focus: dict,
    ) -> int | None:
        """
        H-S19-M / H-S19-N-A / H-S20-D:
        Focus the Direct vs reverse return comparison row from a
        room/subleg/route focus payload.

        Match order:
        1. exact room
        2. exact subleg
        3. exact route_id
        4. route-label match, allowing heating-leg prefixes
        """
        table = getattr(self, "_return_path_comparison_table", None)
        if table is None:
            return None

        wanted_room_id = str((focus or {}).get("room_id", "") or "")
        wanted_subleg_id = str((focus or {}).get("subleg_id", "") or "")
        wanted_route_id = str((focus or {}).get("route_id", "") or "")
        wanted_route = str((focus or {}).get("route", "") or "")

        if (
                not wanted_room_id
                and not wanted_subleg_id
                and not wanted_route_id
                and not wanted_route
        ):
            self._clear_return_path_comparison_table_focus()
            return None

        row_map = getattr(self, "_return_path_focus_by_row", {}) or {}

        if wanted_room_id:
            for row_index, row_focus in row_map.items():
                if str((row_focus or {}).get("room_id", "") or "") == wanted_room_id:
                    self._focus_return_path_comparison_row(row_index)
                    return int(row_index)

        if wanted_subleg_id:
            for row_index, row_focus in row_map.items():
                if str((row_focus or {}).get("subleg_id", "") or "") == wanted_subleg_id:
                    self._focus_return_path_comparison_row(row_index)
                    return int(row_index)

        if wanted_route_id:
            for row_index, row_focus in row_map.items():
                if str((row_focus or {}).get("route_id", "") or "") == wanted_route_id:
                    self._focus_return_path_comparison_row(row_index)
                    return int(row_index)

        if wanted_route:
            for row_index, row_focus in row_map.items():
                row_route = str((row_focus or {}).get("route", "") or "")

                if self._route_label_matches(wanted_route, row_route):
                    self._focus_return_path_comparison_row(row_index)
                    return int(row_index)

        self._clear_return_path_comparison_table_focus()
        return None

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
            self._return_path_focus_by_row = {}
            return
        self._proportioning_snapshot_return_comparison_rows = [
            dict(row)
            for row in (rows or [])
        ]

        self._refresh_return_arrangement_evidence_for_current_scope()

        table = self._return_path_comparison_table

        table.setRowCount(len(rows))
        self._return_path_focus_by_row = {}
        self._return_path_row_data_by_row = {}

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
                row.get("rr_added_length", "—"),
                row.get("rr_added_dp", "—"),
                row.get("rr_suitability", "—"),
                row.get("status", "—"),
            ]

            self._return_path_focus_by_row[row_index] = {
                "route": str(row.get("route", "") or ""),
                "route_id": str(row.get("route_id", "") or ""),
                "leg_id": str(row.get("leg_id", "") or ""),
                "subleg_id": str(row.get("subleg_id", "") or ""),
                "room_id": str(row.get("room_id", "") or ""),
                "emitter_id": str(row.get("emitter_id", "") or ""),
            }

            self._return_path_row_data_by_row[row_index] = dict(row)

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
        self._refresh_proportioning_input_snapshot()

    def _route_label_matches(self, wanted: str, candidate: str) -> bool:
        """
        Match route labels where one view may include the heating-leg prefix.

        Example:
            wanted:    "Heating Leg 2 / Leg 2B Branch subleg"
            candidate: "Leg 2B Branch subleg"
        """
        wanted_text = str(wanted or "").strip().lower()
        candidate_text = str(candidate or "").strip().lower()

        if not wanted_text or not candidate_text:
            return False

        return (
                wanted_text == candidate_text
                or wanted_text in candidate_text
                or candidate_text in wanted_text
        )

    def _on_return_path_comparison_cell_clicked(
            self,
            row_index: int,
            column_index: int,
    ) -> None:
        """
        H-S19-L / H-S19-N-A / H-S20-D:
        Manual click focus for the return comparison table.

        Uses cellClicked instead of Qt row selection so the pale focus
        background does not override F+R / F+RR green/orange text colours.

        Focus/link only:
        • no ProjectState mutation
        • no balancing valve selection
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        focus = getattr(
            self,
            "_return_path_focus_by_row",
            {},
        ).get(row_index, {}) or {}

        row_data = getattr(
            self,
            "_return_path_row_data_by_row",
            {},
        ).get(row_index, {}) or {}

        self._focus_return_path_comparison_row(row_index)
        self._focus_common_main_leg_subleg_row(focus)
        self._focus_preliminary_route_balancing_row_by_focus(focus)
        self._focus_preliminary_balancing_resistance_row_by_focus(focus)
        self._set_current_proportioning_focus_summary(row_data)

    def _on_return_path_comparison_selection_changed(self) -> None:
        table = getattr(self, "_return_path_comparison_table", None)
        if table is None:
            return

        selection_model = table.selectionModel()
        if selection_model is None:
            return

        selected_rows = selection_model.selectedRows()

        if not selected_rows:
            self._clear_return_path_comparison_table_focus()
            self._clear_common_main_leg_subleg_table_focus()

            schematic = getattr(
                self,
                "_common_main_leg_subleg_schematic_widget",
                None,
            )
            if schematic is not None and hasattr(schematic, "set_focus"):
                schematic.set_focus(None)

            return

        row_index = selected_rows[0].row()
        focus = getattr(
            self,
            "_return_path_focus_by_row",
            {},
        ).get(row_index, {}) or {}
        self._focus_return_path_comparison_row(row_index)
        self._focus_common_main_leg_subleg_row(focus)

    def _clear_return_path_comparison_table_focus(self) -> None:
        table = getattr(self, "_return_path_comparison_table", None)
        if table is None:
            return

        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item is not None:
                    item.setBackground(QBrush())

    def _focus_preliminary_route_balancing_row_by_focus(
            self,
            focus: dict,
    ) -> int | None:
        """
        H-S20-D:
        Focus the preliminary route balancing row from a route/subleg focus payload.

        Focus/link only:
        • no ProjectState mutation
        • no balancing valve selection
        • no pump selection
        • no pipe resizing
        • no committed return arrangement
        """
        wanted_subleg_id = str((focus or {}).get("subleg_id", "") or "")
        wanted_route_id = str((focus or {}).get("route_id", "") or "")
        wanted_route = str((focus or {}).get("route", "") or "")

        row_map = getattr(
            self,
            "_preliminary_route_balancing_focus_by_row",
            {},
        ) or {}

        if wanted_subleg_id:
            for row_index, row_focus in row_map.items():
                row_subleg_id = str((row_focus or {}).get("subleg_id", "") or "")
                if row_subleg_id == wanted_subleg_id:
                    self._focus_preliminary_route_balancing_row(row_index)
                    return int(row_index)

        if wanted_route_id:
            for row_index, row_focus in row_map.items():
                row_route_id = str((row_focus or {}).get("route_id", "") or "")
                if row_route_id == wanted_route_id:
                    self._focus_preliminary_route_balancing_row(row_index)
                    return int(row_index)

        if wanted_route:
            for row_index, row_focus in row_map.items():
                row_route = str((row_focus or {}).get("route", "") or "")
                if self._route_label_matches(wanted_route, row_route):
                    self._focus_preliminary_route_balancing_row(row_index)
                    return int(row_index)

        self._clear_preliminary_route_balancing_table_focus()
        return None

    def _focus_return_path_comparison_row(self, row_index: int) -> None:
        table = getattr(self, "_return_path_comparison_table", None)
        if table is None:
            return

        self._clear_return_path_comparison_table_focus()

        if row_index < 0 or row_index >= table.rowCount():
            return

        focus_brush = QBrush(QColor(255, 238, 210))  # pale orange focus

        for c in range(table.columnCount()):
            item = table.item(row_index, c)
            if item is not None:
                item.setBackground(focus_brush)

        first_item = table.item(row_index, 0)
        if first_item is not None:
            table.scrollToItem(
                first_item,
                QAbstractItemView.PositionAtCenter,
            )

    def _focus_common_main_leg_subleg_row(self, focus: dict) -> None:
        topology_table = getattr(self, "_common_main_leg_subleg_table", None)
        schematic = getattr(
            self,
            "_common_main_leg_subleg_schematic_widget",
            None,
        )

        leg_id = str((focus or {}).get("leg_id", "") or "")
        subleg_id = str((focus or {}).get("subleg_id", "") or "")
        room_id = str((focus or {}).get("room_id", "") or "")

        if topology_table is not None:
            topology_table.clearSelection()
            self._clear_common_main_leg_subleg_table_focus()

            focus_brush = QBrush(QColor(255, 238, 210))  # pale orange table focus
            text_brush = QBrush(QColor(20, 20, 20))  # dark readable text

            matched_row = -1

            for r in range(topology_table.rowCount()):
                row_matches = False

                for c in range(topology_table.columnCount()):
                    item = topology_table.item(r, c)
                    if item is None:
                        continue

                    item_text = item.text().strip()

                    if subleg_id and item_text == subleg_id:
                        row_matches = True
                        break

                    if room_id and room_id in item_text:
                        row_matches = True
                        break

                    if leg_id and item_text == leg_id:
                        row_matches = True
                        break

                if row_matches:
                    matched_row = r
                    break

            if matched_row >= 0:
                topology_table.selectRow(matched_row)

                for c in range(topology_table.columnCount()):
                    item = topology_table.item(matched_row, c)
                    if item is not None:
                        item.setBackground(focus_brush)
                        item.setForeground(text_brush)

                first_item = topology_table.item(matched_row, 0)
                if first_item is not None:
                    topology_table.scrollToItem(
                        first_item,
                        QAbstractItemView.PositionAtCenter,
                    )

        if schematic is not None and hasattr(schematic, "set_focus"):
            schematic.set_focus(
                {
                    "leg_id": leg_id,
                    "subleg_id": subleg_id,
                    "room_id": room_id,
                }
            )

    def set_effective_return_arrangement_basis_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S27-B:
        Display the resolved effective return-arrangement basis consumed by
        Proportioned.

        Display only:
            no ProjectState access
            no balancing
            no pump selection
            no valve selection
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_effective_return_arrangement_basis_table"):
            return

        table = self._effective_return_arrangement_basis_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "scope": "—",
                    "target": "—",
                    "effective_basis": "—",
                    "source": "—",
                    "status": "No resolved return arrangement basis yet",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("scope", "—"),
                row.get("target", "—"),
                row.get("effective_basis", "—"),
                row.get("source", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=120, max_height=240)
        table.scrollToTop()

    def set_chosen_basis_route_pressure_preview_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S27-C:
        Display chosen-basis route Δp preview consumed by Proportioned.

        Display only:
            no ProjectState access
            no balancing
            no pump selection
            no valve selection
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_chosen_basis_route_pressure_preview_table"):
            return

        table = self._chosen_basis_route_pressure_preview_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "scope": "—",
                    "route": "—",
                    "basis": "—",
                    "chosen_dp": "—",
                    "alternative_dp": "—",
                    "difference": "—",
                    "source": "—",
                    "status": "No chosen-basis route Δp preview yet",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("scope", "—"),
                row.get("route", "—"),
                row.get("basis", "—"),
                row.get("chosen_dp", "—"),
                row.get("alternative_dp", "—"),
                row.get("difference", "—"),
                row.get("source", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                table.setItem(row_index, col_index, item)

        table.setWordWrap(False)
        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)



    def set_chosen_basis_controlling_route_preview_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S27-D:
        Display chosen-basis controlling route preview.

        Display only:
            no ProjectState access
            no balancing
            no pump selection
            no valve selection
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_chosen_basis_controlling_route_preview_table"):
            return

        table = self._chosen_basis_controlling_route_preview_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "scope": "—",
                    "route": "—",
                    "basis": "—",
                    "chosen_dp": "—",
                    "controlling": "No",
                    "dp_below_controlling": "—",
                    "source": "—",
                    "status": "No chosen-basis controlling route preview yet",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("scope", "—"),
                row.get("route", "—"),
                row.get("basis", "—"),
                row.get("chosen_dp", "—"),
                row.get("controlling", "No"),
                row.get("dp_below_controlling", "—"),
                row.get("source", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                table.setItem(row_index, col_index, item)

        table.setWordWrap(False)
        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)

    def set_provisional_proportioning_burden_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S30-C:
        Display provisional route burden evidence in the Proportioned tab.

        Display only:
            no ProjectState access
            no balancing valve selection
            no pump selection
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_provisional_proportioning_burden_table"):
            return

        table = self._provisional_proportioning_burden_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "rank": "—",
                    "route": "—",
                    "basis": "—",
                    "flow_kg_s": "—",
                    "chosen_dp": "—",
                    "controlling": "No",
                    "required_added_dp": "—",
                    "resistance_pa_per_kg_s2": "—",
                    "action": "Waiting for chosen-basis burden evidence",
                    "status": "Preview only — no valve selected",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("rank", "—"),
                row.get("route", "—"),
                row.get("basis", "—"),
                row.get("flow_kg_s", "—"),
                row.get("chosen_dp", "—"),
                row.get("controlling", "No"),
                row.get("required_added_dp", "—"),
                row.get("resistance_pa_per_kg_s2", "—"),
                row.get("action", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        table.setWordWrap(False)
        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)

        self._fit_table_height(table, min_height=120, max_height=240)
        table.scrollToTop()

    def set_balancing_method_candidate_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S31-D:
        Display route-level balancing method candidates in the Proportioned tab.

        Read-only preview:
            no ProjectState access
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no pump selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_balancing_method_candidate_table"):
            return

        table = self._balancing_method_candidate_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "route": "—",
                    "method": "—",
                    "ready": "No",
                    "controlling": "No",
                    "required_added_dp": "—",
                    "flow_kg_s": "—",
                    "resistance_pa_per_kg_s2": "—",
                    "status": (
                        "Waiting for balancing method candidate evidence"
                    ),
                    "blockers": "—",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("route", "—"),
                row.get("method", "—"),
                row.get("ready", "No"),
                row.get("controlling", "No"),
                row.get("required_added_dp", "—"),
                row.get("flow_kg_s", "—"),
                row.get("resistance_pa_per_kg_s2", "—"),
                row.get("status", "—"),
                row.get("blockers", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        table.setWordWrap(False)

        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)

    def set_balancing_point_evidence_rows(
            self,
            rows: list[dict],
    ) -> None:
        """H-S44-E display-only point allocation and valve-duty evidence."""
        if not hasattr(self, "_balancing_point_evidence_table"):
            return
        table = self._balancing_point_evidence_table
        rows = list(rows or [])
        if not rows:
            rows = [
                {
                    "balancing_point_id": "—",
                    "point_scope": "—",
                    "point_role": "—",
                    "topology": "—",
                    "governed_routes": "—",
                    "point_flow": "—",
                    "allocated_dp": "—",
                    "resistance": "—",
                    "method": "—",
                    "valve_duty": "—",
                    "controlled_dp": "—",
                    "authority": "—",
                    "ready": "No",
                    "status": "Waiting for H-S44 point evidence",
                    "blockers": "—",
                }
            ]
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.get("balancing_point_id", "—"),
                row.get("point_scope", "—"),
                row.get("point_role", "—"),
                row.get("topology", "—"),
                row.get("governed_routes", "—"),
                row.get("point_flow", "—"),
                row.get("allocated_dp", "—"),
                row.get("resistance", "—"),
                row.get("method", "—"),
                row.get("valve_duty", "—"),
                row.get("controlled_dp", "—"),
                row.get("authority", "—"),
                row.get("ready", "No"),
                row.get("status", "—"),
                row.get("blockers", "—"),
            ]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)
        table.setWordWrap(False)
        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)
        self._fit_table_height(table, min_height=120, max_height=260)

    def set_valve_authority_input_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S32-D:
        Display route-level valve authority input preview.

        Read-only preview:
            no ProjectState access
            no authority ratio calculation here
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no manufacturer valve data
            no pump selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_valve_authority_input_table"):
            return

        table = self._valve_authority_input_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "route": "—",
                    "balancing_method": "—",
                    "authority_state": "—",
                    "ready": "No",
                    "design_valve_dp": "—",
                    "flow_kg_s": "—",
                    "candidate_resistance": "—",
                    "controlled_circuit_dp": "—",
                    "authority": "—",
                    "status": "Waiting for valve authority input evidence",
                    "blockers": "—",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("route", "—"),
                row.get("balancing_method", "—"),
                row.get("authority_state", "—"),
                row.get("ready", "No"),
                row.get("design_valve_dp", "—"),
                row.get("flow_kg_s", "—"),
                row.get("candidate_resistance", "—"),
                row.get("controlled_circuit_dp", "—"),
                row.get("authority", "—"),
                row.get("status", "—"),
                row.get("blockers", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        table.setWordWrap(False)

        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)

        self._fit_table_height(table, min_height=105, max_height=155)
        table.scrollToTop()

    def set_chosen_basis_proportioned_readiness_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S27-F:
        Display chosen-basis proportioned readiness summary.

        Display only:
            no ProjectState access
            no balancing
            no pump selection
            no valve selection
            no pipe resizing
            no final hydraulic result
        """
        if not hasattr(self, "_chosen_basis_proportioned_readiness_table"):
            return

        table = self._chosen_basis_proportioned_readiness_table
        rows = list(rows or [])

        if not rows:
            rows = [
                {
                    "item": "Chosen-basis proportioned readiness",
                    "status": "No chosen-basis proportioned readiness summary yet",
                }
            ]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("item", "—"),
                self._clean_proportioned_summary_status_v1(
                    item=row.get("item", "—"),
                    status=row.get("status", "—"),
                ),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                table.setItem(row_index, col_index, item)

        table.setWordWrap(False)
        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)

    def _clean_proportioned_focused_route_label_v1(self) -> str:
        """
        H-S33-J:
        Return the currently focused clean Proportioned route label.

        UI state only:
        • no ProjectState access
        • no section filtering yet
        • no schematic focus yet
        • no pressure / authority calculation changes
        """
        return str(
            getattr(
                self,
                "_clean_proportioned_focused_route_label",
                "",
            )
            or ""
        ).strip()

    def _set_clean_proportioned_focused_route_label_v1(
            self,
            route_label: object,
    ) -> None:
        """
        H-S33-J:
        Store the currently focused clean Proportioned route label.

        This is transient UI state only. It is intentionally not persisted.
        """
        self._clean_proportioned_focused_route_label = str(
            route_label or ""
        ).strip()

        # H-S34-G: every present or future clean route-selection surface uses
        # this central state setter, so the clean schematic follows without
        # direct table-to-widget coupling.
        self._refresh_clean_proportioned_schematic_focus_v1()
        self._sync_clean_proportioned_route_selection_v1(
            self._clean_proportioned_focused_route_label_v1()
        )


    @staticmethod
    def _clean_proportioned_schematic_section_ordinal_v1(
            row: dict,
    ) -> int:
        """Resolve a positive display section ordinal without calculation."""
        import re

        for key in ("section", "order"):
            text = str(row.get(key, "") or "").strip()
            match = re.fullmatch(r"0*(\d+)", text)

            if match:
                value = int(match.group(1))
                return value if value > 0 else 0

        section_id = str(row.get("section_id", "") or "").strip()
        match = re.search(r"-section-0*(\d+)$", section_id)

        if not match:
            return 0

        value = int(match.group(1))
        return value if value > 0 else 0

    def _clean_proportioned_schematic_route_matches_section_v1(
            self,
            *,
            route: object,
            row: dict,
    ) -> bool:
        """Match stable subleg identity first, then the existing route token."""
        route_subleg_id = str(
            getattr(route, "subleg_id", "") or ""
        ).strip()
        row_subleg_id = str(row.get("subleg_id", "") or "").strip()
        row_route_id = str(row.get("route_id", "") or "").strip()

        for stable_value in (row_subleg_id, row_route_id):
            if (
                    stable_value
                    and stable_value not in {"—", "-"}
                    and route_subleg_id
                    and stable_value == route_subleg_id
            ):
                return True

        row_token = ""

        for value in (
            row.get("route_code", ""),
            row.get("route", ""),
            row.get("to", ""),
            row.get("from", ""),
        ):
            row_token = self._clean_proportioned_schematic_route_token_v1(
                value
            )
            if row_token:
                break

        if not row_token:
            return False

        route_tokens = {
            self._clean_proportioned_schematic_route_token_v1(value)
            for value in (
                getattr(route, "subleg_label", ""),
                getattr(route, "subleg_id", ""),
                getattr(route, "route_label", ""),
            )
            if str(value or "").strip()
        }

        return row_token in route_tokens

    def _clean_proportioned_schematic_with_section_evidence_v1(
            self,
            schematic: object,
            rows: list[dict],
    ):
        """
        H-S36-A2 — clean schematic section-evidence mapping.

        Map existing read-only section rows to room-entry trace ordinals.
        No pressure, sizing, balancing, take-off, or ProjectState logic.
        """
        if schematic is None:
            return None

        routes = tuple(getattr(schematic, "routes", ()) or ())
        preferred_rows = (
            self._clean_proportioned_prefer_engineering_section_rows_v1(
                [dict(row or {}) for row in (rows or [])]
            )
        )
        mapped_routes = []

        def identity_value(
                row: dict,
                key: str,
                fallback: object,
        ) -> str:
            value = str(row.get(key, "") or "").strip()

            if value and value not in {"—", "-"}:
                return value

            return str(fallback or "").strip()

        for route in routes:
            room_labels = tuple(getattr(route, "room_labels", ()) or ())
            evidence_items = []
            seen_segments: set[tuple[int, str, str]] = set()

            for row in preferred_rows:
                if not self._clean_proportioned_schematic_route_matches_section_v1(
                        route=route,
                        row=row,
                ):
                    continue

                ordinal = self._clean_proportioned_schematic_section_ordinal_v1(
                    row
                )

                if ordinal <= 0 or ordinal > len(room_labels):
                    continue

                from_label = str(row.get("from", "") or "")
                to_label = str(row.get("to", "") or "")
                segment_key = (ordinal, from_label, to_label)

                if segment_key in seen_segments:
                    continue

                seen_segments.add(segment_key)
                trace_index = ordinal - 1
                evidence_items.append(
                    CommonMainLegSublegSectionEvidenceV1(
                        section_id=str(row.get("section_id", "") or ""),
                        section_ordinal=ordinal,
                        trace_index=trace_index,
                        trace_room_id=str(room_labels[trace_index] or ""),
                        route_id=identity_value(
                            row,
                            "route_id",
                            getattr(route, "subleg_id", ""),
                        ),
                        leg_id=identity_value(
                            row,
                            "leg_id",
                            getattr(route, "leg_id", ""),
                        ),
                        subleg_id=identity_value(
                            row,
                            "subleg_id",
                            getattr(route, "subleg_id", ""),
                        ),
                        from_label=from_label,
                        to_label=to_label,
                        flow_kg_s=str(row.get("flow_kg_s", "") or ""),
                        pipe_dn=str(row.get("pipe_dn", "") or ""),
                        dp_per_m=str(row.get("dp_per_m", "") or ""),
                        length=str(row.get("length", "") or ""),
                        k=str(row.get("k", "") or ""),
                        section_dp=str(row.get("section_dp", "") or ""),
                        iter=str(row.get("iter", "") or ""),
                        status=str(row.get("status", "") or ""),
                    )
                )

            evidence_items.sort(key=lambda item: item.section_ordinal)
            mapped_routes.append(
                replace(route, section_evidence=tuple(evidence_items))
            )

        return replace(schematic, routes=tuple(mapped_routes))

    def _refresh_clean_proportioned_schematic_section_evidence_v1(
            self,
    ) -> None:
        """Rebuild only the separate clean Proportioned display DTO."""
        base_schematic = getattr(
            self,
            "_clean_proportioned_schematic_base_dto_v1",
            None,
        )
        rows = list(
            getattr(
                self,
                "_clean_proportioned_focused_section_source_rows",
                [],
            )
            or []
        )
        mapped_schematic = (
            self._clean_proportioned_schematic_with_section_evidence_v1(
                base_schematic,
                rows,
            )
        )

        self._clean_proportioned_schematic_dto_v1 = mapped_schematic

        schematic_widget = getattr(
            self,
            "_clean_proportioned_common_main_leg_subleg_schematic_widget",
            None,
        )

        if schematic_widget is not None:
            schematic_widget.set_schematic(mapped_schematic)

        self._refresh_clean_proportioned_schematic_focus_v1()

    def _clean_proportioned_schematic_route_token_v1(
            self,
            value: object,
    ) -> str:
        # Reuse the H-S33 table token convention first, then recognise the
        # separate schematic DTO's labels such as "Subleg 1B".
        token = self._clean_proportioned_route_token_from_text_v1(value)

        if token:
            return token

        import re

        match = re.search(
            r"\bSUBLEG\s*(\d+[A-Z])\b",
            str(value or "").upper(),
        )

        return match.group(1) if match else ""

    def _clean_proportioned_schematic_focus_for_route_label_v1(
            self,
            route_label: object,
    ) -> dict | None:
        # Resolve the clean route label to stable IDs from the display DTO.
        route_token = self._clean_proportioned_schematic_route_token_v1(
            route_label
        )

        if not route_token:
            return None

        schematic = getattr(
            self,
            "_clean_proportioned_schematic_dto_v1",
            None,
        )
        routes = tuple(getattr(schematic, "routes", ()) or ())

        for route in routes:
            candidate_values = (
                getattr(route, "route_label", ""),
                getattr(route, "subleg_label", ""),
                getattr(route, "subleg_id", ""),
            )
            candidate_tokens = {
                self._clean_proportioned_schematic_route_token_v1(value)
                for value in candidate_values
                if str(value or "").strip()
            }

            if route_token not in candidate_tokens:
                continue

            return {
                "leg_id": str(getattr(route, "leg_id", "") or ""),
                "subleg_id": str(
                    getattr(route, "subleg_id", "") or ""
                ),
                "room_id": "",
            }

        return None

    def _refresh_clean_proportioned_schematic_focus_v1(self) -> None:
        # Apply shared route-focus state only to the separate clean schematic.
        schematic_widget = getattr(
            self,
            "_clean_proportioned_common_main_leg_subleg_schematic_widget",
            None,
        )

        if schematic_widget is None or not hasattr(
                schematic_widget,
                "set_focus",
        ):
            return

        route_label = self._clean_proportioned_focused_route_label_v1()
        focus = self._clean_proportioned_schematic_focus_for_route_label_v1(
            route_label
        )
        schematic_widget.set_focus(focus)


    def _build_clean_proportioned_table_viewer_v1(self) -> None:
        """
        H-S35-A:
        Build one reusable non-modal clean Proportioned table viewer.

        The viewer owns duplicate read-only table projections. It never
        reparents the embedded tables and carries no engineering authority.
        """
        if getattr(self, "_clean_proportioned_table_viewer_dialog", None):
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Proportioned data viewer — read-only")
        dialog.setModal(False)
        dialog.setWindowModality(Qt.NonModal)
        dialog.resize(1280, 720)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        notice = QLabel(
            "Display-only Proportioned route and pipe-section evidence. "
            "Selection is shared with the Proportioned schematic.",
            dialog,
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.addWidget(QLabel("Pipe-section view:", dialog))

        mode_combo = QComboBox(dialog)
        mode_combo.addItems(["Selected route only", "All routes"])
        controls.addWidget(mode_combo)

        controls.addSpacing(10)
        controls.addWidget(QLabel("Evidence:", dialog))
        evidence_mode = self._clean_proportioned_evidence_view_v1()
        evidence_button = QPushButton(evidence_mode, dialog)
        evidence_button.setCheckable(True)
        evidence_button.setMaximumWidth(130)
        evidence_button.setChecked(evidence_mode == "Proportioning")
        self._set_clean_proportioned_evidence_button_style_v1(
            evidence_button,
            evidence_mode,
        )
        controls.addWidget(evidence_button)

        focus_label = QLabel("Focused route: —", dialog)
        controls.addWidget(focus_label, 1)
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Vertical, dialog)
        splitter.setChildrenCollapsible(False)

        route_frame = QFrame(splitter)
        route_frame.setFrameShape(QFrame.StyledPanel)
        route_layout = QVBoxLayout(route_frame)
        route_layout.setContentsMargins(4, 4, 4, 4)
        route_layout.addWidget(QLabel(
            "Proportioned route output — read-only",
            route_frame,
        ))

        route_table = self._make_table(
            columns=[
                "Route",
                "Basis",
                "Sections",
                "Flow kg/s",
                "Pipe DN",
                "Δp/m",
                "Chosen Δp",
                "Added Δp",
                "Authority",
                "Status",
            ]
        )
        route_table.setWordWrap(False)
        route_table.setAlternatingRowColors(True)
        self._apply_clean_proportioned_table_focus_style_v1(route_table)
        route_table.setToolTip(
            "Read-only duplicate of the clean Proportioned route output."
        )
        route_layout.addWidget(route_table)

        section_frame = QFrame(splitter)
        section_frame.setFrameShape(QFrame.StyledPanel)
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(4, 4, 4, 4)
        section_layout.addWidget(QLabel(
            "Focused route / subleg sections — read-only",
            section_frame,
        ))

        section_mode_table = self._make_pipe_section_mode_table_v1(
            section_frame
        )
        section_layout.addWidget(section_mode_table, 0, Qt.AlignLeft)

        section_table = self._make_table(
            columns=[
                "Route",
                "Section",
                "From",
                "To",
                "Flow kg/s",
                "Pipe DN",
                "Δp/m",
                "Length",
                "K",
                "Section Δp",
                "Iter",
                "Status",
            ]
        )
        section_table.setWordWrap(False)
        section_table.setAlternatingRowColors(True)
        self._apply_clean_proportioned_table_focus_style_v1(section_table)
        section_table.setToolTip(
            "Read-only duplicate of the focused pipe-section evidence."
        )
        section_layout.addWidget(section_table)

        splitter.addWidget(route_frame)
        splitter.addWidget(section_frame)
        splitter.setSizes([270, 390])
        layout.addWidget(splitter, 1)

        self._clean_proportioned_table_viewer_dialog = dialog
        self._clean_proportioned_table_viewer_mode_combo = mode_combo
        self._clean_proportioned_table_viewer_evidence_button = (
            evidence_button
        )
        self._clean_proportioned_table_viewer_focus_label = focus_label
        self._clean_proportioned_table_viewer_route_table = route_table
        self._clean_proportioned_table_viewer_section_mode_table = (
            section_mode_table
        )
        self._clean_proportioned_table_viewer_section_table = section_table

        mode_combo.currentTextChanged.connect(
            self._on_clean_proportioned_table_viewer_mode_changed_v1
        )
        evidence_button.toggled.connect(
            self._on_clean_proportioned_evidence_view_toggled_v1
        )
        route_table.itemSelectionChanged.connect(
            self._on_clean_proportioned_table_viewer_route_selection_changed_v1
        )

    @staticmethod
    def _copy_clean_proportioned_table_projection_v1(
            source_table: object,
            target_table: object,
    ) -> None:
        """Copy one read-only table projection without sharing ownership."""
        if source_table is None or target_table is None:
            return

        previous_signal_state = target_table.blockSignals(True)

        try:
            column_count = source_table.columnCount()
            row_count = source_table.rowCount()

            target_table.setColumnCount(column_count)
            target_table.setHorizontalHeaderLabels(
                [
                    str(source_table.horizontalHeaderItem(index).text())
                    if source_table.horizontalHeaderItem(index) is not None
                    else ""
                    for index in range(column_count)
                ]
            )
            target_table.setRowCount(row_count)

            for row_index in range(row_count):
                target_table.setRowHeight(
                    row_index,
                    source_table.rowHeight(row_index),
                )

                for column_index in range(column_count):
                    source_item = source_table.item(row_index, column_index)
                    item = (
                        QTableWidgetItem(source_item)
                        if source_item is not None
                        else QTableWidgetItem("—")
                    )
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    target_table.setItem(row_index, column_index, item)

            for column_index in range(column_count):
                target_table.setColumnWidth(
                    column_index,
                    source_table.columnWidth(column_index),
                )

            target_table.horizontalHeader().setStretchLastSection(
                source_table.horizontalHeader().stretchLastSection()
            )
        finally:
            target_table.blockSignals(previous_signal_state)

    def _refresh_clean_proportioned_table_viewer_v1(self) -> None:
        """Refresh the optional H-S35-A viewer from embedded projections."""
        dialog = getattr(
            self,
            "_clean_proportioned_table_viewer_dialog",
            None,
        )

        if dialog is None:
            return

        self._copy_clean_proportioned_table_projection_v1(
            getattr(self, "_clean_proportioned_route_output_table", None),
            getattr(
                self,
                "_clean_proportioned_table_viewer_route_table",
                None,
            ),
        )
        self._copy_clean_proportioned_table_projection_v1(
            getattr(
                self,
                "_clean_proportioned_focused_section_table",
                None,
            ),
            getattr(
                self,
                "_clean_proportioned_table_viewer_section_table",
                None,
            ),
        )
        self._set_pipe_section_mode_table_v1(
            getattr(
                self,
                "_clean_proportioned_table_viewer_section_mode_table",
                None,
            ),
            list(
                getattr(
                    self,
                    "_clean_proportioned_visible_section_rows_v1",
                    [],
                )
                or []
            ),
        )

        source_label = getattr(
            self,
            "_clean_proportioned_focused_section_label",
            None,
        )
        target_label = getattr(
            self,
            "_clean_proportioned_table_viewer_focus_label",
            None,
        )

        if source_label is not None and target_label is not None:
            target_label.setText(source_label.text())

        source_combo = getattr(
            self,
            "_clean_proportioned_section_view_mode_combo",
            None,
        )
        target_combo = getattr(
            self,
            "_clean_proportioned_table_viewer_mode_combo",
            None,
        )

        if source_combo is not None and target_combo is not None:
            previous_signal_state = target_combo.blockSignals(True)
            try:
                target_combo.setCurrentText(source_combo.currentText())
            finally:
                target_combo.blockSignals(previous_signal_state)

        self._sync_clean_proportioned_route_selection_v1(
            self._clean_proportioned_focused_route_label_v1()
        )

    def _sync_clean_proportioned_route_selection_v1(
            self,
            route_label: object,
    ) -> None:
        """Mirror transient route focus without recursive selection signals."""
        label = str(route_label or "").strip()

        for attribute_name in (
            "_clean_proportioned_route_output_table",
            "_clean_proportioned_table_viewer_route_table",
        ):
            table = getattr(self, attribute_name, None)

            if table is None:
                continue

            # H-S35-A1: minimal table doubles used by focused regressions do
            # not expose the complete QWidget/QTableWidget signal API.
            required_methods = (
                "blockSignals",
                "clearSelection",
                "rowCount",
                "item",
            )

            if not all(hasattr(table, name) for name in required_methods):
                continue

            previous_signal_state = table.blockSignals(True)

            try:
                table.clearSelection()

                if not label:
                    continue

                for row_index in range(table.rowCount()):
                    item = table.item(row_index, 0)

                    if item is None or str(item.text() or "").strip() != label:
                        continue

                    table.selectRow(row_index)
                    table.setCurrentCell(row_index, 0)
                    table.scrollToItem(item)
                    break
            finally:
                table.blockSignals(previous_signal_state)

    def _on_clean_proportioned_table_viewer_route_selection_changed_v1(
            self,
    ) -> None:
        """Use viewer route selection as another transient focus surface."""
        table = getattr(
            self,
            "_clean_proportioned_table_viewer_route_table",
            None,
        )

        if table is None:
            return

        row_index = table.currentRow()

        if row_index < 0:
            return

        item = table.item(row_index, 0)
        route_label = str(item.text() if item is not None else "").strip()

        if not route_label or route_label == "—":
            return

        self._set_clean_proportioned_focused_route_label_v1(route_label)
        self._refresh_clean_proportioned_focused_section_view_v1()

    def _on_clean_proportioned_table_viewer_mode_changed_v1(
            self,
            mode_text: object,
    ) -> None:
        """Mirror the viewer's display mode through the embedded control."""
        source_combo = getattr(
            self,
            "_clean_proportioned_section_view_mode_combo",
            None,
        )

        if source_combo is None:
            return

        value = str(mode_text or "").strip()

        if source_combo.currentText() != value:
            source_combo.setCurrentText(value)
        else:
            self._refresh_clean_proportioned_focused_section_view_v1()

    def _show_clean_proportioned_table_viewer_v1(self) -> None:
        """Show and activate the reusable draggable H-S35-A viewer."""
        self._build_clean_proportioned_table_viewer_v1()
        self._refresh_clean_proportioned_table_viewer_v1()

        dialog = self._clean_proportioned_table_viewer_dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()


    def _clean_proportioned_route_label_for_row_v1(self, row_index: int) -> str:
        """
        H-S33-J:
        Read the route label from the clean Proportioned route-output table.
        """
        if not hasattr(self, "_clean_proportioned_route_output_table"):
            return ""

        table = self._clean_proportioned_route_output_table

        if row_index < 0:
            return ""

        try:
            item = table.item(row_index, 0)
        except Exception:
            return ""

        if item is None:
            return ""

        try:
            return str(item.text() or "").strip()
        except Exception:
            return ""

    def _on_clean_proportioned_route_output_selection_changed_v1(self) -> None:
        """
        H-S33-J:
        Capture the currently selected clean route-output row.

        Selecting a new route replaces the previous focused route state.
        Later H-S33-K/H-S33-L can use this state to show either one route's
        pipe sections or all routes.
        """
        if not hasattr(self, "_clean_proportioned_route_output_table"):
            return

        table = self._clean_proportioned_route_output_table

        row_index = -1

        try:
            selected_rows = table.selectionModel().selectedRows()
        except Exception:
            selected_rows = []

        if selected_rows:
            try:
                row_index = selected_rows[0].row()
            except Exception:
                row_index = -1

        if row_index < 0:
            try:
                row_index = table.currentRow()
            except Exception:
                row_index = -1

        route_label = self._clean_proportioned_route_label_for_row_v1(
            row_index
        )

        self._set_clean_proportioned_focused_route_label_v1(route_label)

        if hasattr(
                self,
                "_refresh_clean_proportioned_focused_section_view_v1",
        ):
            self._refresh_clean_proportioned_focused_section_view_v1()

    def _wire_clean_proportioned_route_output_selection_v1(
            self,
            table: object,
    ) -> None:
        """
        H-S33-J:
        Wire clean route-output row selection into transient focused-route
        UI state.

        Repeated configure calls are safe; the connection is only made once.
        """
        if table is None:
            return

        if getattr(
                self,
                "_clean_proportioned_route_output_selection_wired_v1",
                False,
        ):
            return

        try:
            table.itemSelectionChanged.connect(
                self._on_clean_proportioned_route_output_selection_changed_v1
            )
        except Exception:
            return

        self._clean_proportioned_route_output_selection_wired_v1 = True



    @staticmethod
    def _set_clean_proportioned_evidence_button_style_v1(
            button: object,
            mode: str,
    ) -> None:
        """H-S41-B1: mirror the non-interactive mode indicator colours."""
        if button is None:
            return
        proportioning = str(mode or "") == "Proportioning"
        background = "rgb(46, 139, 87)" if proportioning else "rgb(232, 145, 55)"
        foreground = "white" if proportioning else "black"
        button.setStyleSheet(
            "QPushButton {"
            f"background-color: {background}; "
            f"color: {foreground}; "
            "font-weight: 600;"
            "}"
        )

    def _clean_proportioned_evidence_view_v1(self) -> str:
        """Return the selected read-only evidence stage."""
        value = str(
            getattr(
                self,
                "_clean_proportioned_evidence_view_mode_v1",
                "Proportioning",
            )
            or "Proportioning"
        )
        return "Basic PS" if value == "Basic PS" else "Proportioning"

    def _set_clean_proportioned_evidence_view_v1(
            self,
            mode: str,
            *,
            refresh: bool = True,
    ) -> None:
        """Synchronise embedded/viewer toggles without engineering mutation."""
        resolved = "Basic PS" if str(mode or "") == "Basic PS" else "Proportioning"
        self._clean_proportioned_evidence_view_mode_v1 = resolved
        checked = resolved == "Proportioning"

        for attribute in (
            "_clean_proportioned_evidence_view_button",
            "_clean_proportioned_table_viewer_evidence_button",
        ):
            button = getattr(self, attribute, None)
            if button is None:
                continue
            previous = button.blockSignals(True)
            try:
                button.setChecked(checked)
                button.setText(resolved)
                self._set_clean_proportioned_evidence_button_style_v1(
                    button,
                    resolved,
                )
            finally:
                button.blockSignals(previous)

        if not refresh:
            return
        self._refresh_clean_proportioned_focused_section_view_v1()
        if getattr(self, "_clean_proportioned_table_viewer_dialog", None):
            self._refresh_clean_proportioned_table_viewer_v1()

    def _on_clean_proportioned_evidence_view_toggled_v1(
            self,
            checked: bool,
    ) -> None:
        self._set_clean_proportioned_evidence_view_v1(
            "Proportioning" if checked else "Basic PS"
        )

    def _set_clean_proportioned_evidence_availability_v1(
            self,
            rows: list[dict],
    ) -> None:
        """Disable Proportioning choice when no Colebrook evidence exists."""
        explicit = [
            str((row or {}).get("proportioning_friction_method", "") or "")
            .strip()
            .casefold()
            for row in (rows or [])
        ]
        available = any(value.startswith("colebrook") for value in explicit)
        self._clean_proportioned_proportioning_evidence_available_v1 = available

        if rows and not available:
            self._set_clean_proportioned_evidence_view_v1(
                "Basic PS",
                refresh=False,
            )

        for attribute in (
            "_clean_proportioned_evidence_view_button",
            "_clean_proportioned_table_viewer_evidence_button",
        ):
            button = getattr(self, attribute, None)
            if button is not None:
                button.setEnabled(available)

    def _clean_proportioned_evidence_row_v1(
            self,
            row: dict,
    ) -> dict:
        """Project one existing row into Basic or Proportioning evidence."""
        projected = dict(row or {})
        mode = self._clean_proportioned_evidence_view_v1()

        if mode == "Basic PS":
            projected["pipe_dn"] = (
                projected.get("basic_pipe_dn")
                or projected.get("pipe_dn")
                or "—"
            )
            projected["dp_per_m"] = (
                projected.get("basic_dp_per_m") or "—"
            )
            projected["iter"] = "—"
            projected["friction_method"] = (
                projected.get("basic_friction_method") or "Haaland"
            )
            # Current K and section-Δp values use Proportioning evidence.
            # Hide them rather than presenting mixed calculation stages.
            projected["k"] = "—"
            projected["section_dp"] = "—"
            projected["status"] = (
                "Basic PS evidence — velocity selection / Haaland estimate; "
                "Proportioning Local K and section Δp hidden"
            )
            return projected

        projected["pipe_dn"] = (
            projected.get("proportioning_pipe_dn")
            or projected.get("pipe_dn")
            or "—"
        )
        projected["dp_per_m"] = (
            projected.get("proportioning_dp_per_m")
            or projected.get("dp_per_m")
            or "—"
        )
        projected["iter"] = (
            projected.get("proportioning_iter")
            or projected.get("iter")
            or "—"
        )
        projected["friction_method"] = (
            projected.get("proportioning_friction_method")
            or projected.get("friction_method")
            or "—"
        )
        return projected

    def _clean_proportioned_section_view_mode_v1(self) -> str:
        """
        H-S33-K:
        Return the clean Proportioned focused section view mode.

        UI state only:
        • no ProjectState access
        • no section evidence calculation
        • no pressure / authority calculation changes
        """
        mode = ""

        if hasattr(self, "_clean_proportioned_section_view_mode_combo"):
            try:
                mode = self._clean_proportioned_section_view_mode_combo.currentText()
            except Exception:
                mode = ""

        if not mode:
            mode = str(
                getattr(
                    self,
                    "_clean_proportioned_section_view_mode",
                    "",
                )
                or ""
            ).strip()

        if mode not in {"Selected route only", "All routes"}:
            mode = "Selected route only"

        return mode

    def _set_clean_proportioned_section_view_mode_v1(
            self,
            mode: object,
    ) -> None:
        """
        H-S33-K:
        Store the clean Proportioned focused section view mode.

        This is transient UI state only. It is intentionally not persisted.
        """
        mode_text = str(mode or "").strip()

        if mode_text not in {"Selected route only", "All routes"}:
            mode_text = "Selected route only"

        self._clean_proportioned_section_view_mode = mode_text

        if hasattr(self, "_clean_proportioned_section_view_mode_combo"):
            try:
                if (
                        self._clean_proportioned_section_view_mode_combo.currentText()
                        != mode_text
                ):
                    self._clean_proportioned_section_view_mode_combo.setCurrentText(
                        mode_text
                    )
            except Exception:
                pass

    def _on_clean_proportioned_section_view_mode_changed_v1(
            self,
            *_args: object,
    ) -> None:
        """
        H-S33-K:
        Refresh the focused section shell when the user switches between
        selected-route-only and all-routes mode.
        """
        self._set_clean_proportioned_section_view_mode_v1(
            self._clean_proportioned_section_view_mode_v1()
        )
        self._refresh_clean_proportioned_focused_section_view_v1()

    def _configure_clean_proportioned_focused_section_table_v1(self) -> None:
        """
        H-S33-K:
        Configure the focused route/subleg pipe-section shell table.

        Visual/UI shell only:
        • no section rows populated from engineering evidence yet
        • no final hydraulics
        • no valve product / Kv / Kvs
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_clean_proportioned_focused_section_table"):
            return

        table = self._clean_proportioned_focused_section_table

        table.setWordWrap(False)
        table.setAlternatingRowColors(True)
        self._apply_clean_proportioned_table_focus_style_v1(table)

        table.setToolTip(
            "Focused pipe-section view shell — read-only; section evidence "
            "population comes in a later milestone."
        )

        widths = [
            190,  # Route
            95,   # Section
            120,  # From
            120,  # To
            85,   # Flow kg/s
            80,   # Pipe DN
            80,   # Δp/m
            80,   # Length
            55,   # K
            95,   # Section Δp
            55,   # Iter
            330,  # Status
        ]

        for col_index, width in enumerate(widths):
            try:
                table.setColumnWidth(col_index, width)
            except Exception:
                pass

        try:
            table.horizontalHeader().setStretchLastSection(True)
        except AttributeError:
            pass

    def _clean_proportioned_section_display_row_v1(
            self,
            row: dict,
    ) -> dict:
        """
        H-S33-M5A:
        Final display guard for focused section rows.

        Iter means Colebrook iteration count only. Even if an upstream
        adapter/source row already carries an iter value, the final table
        display must suppress it unless the row explicitly says Colebrook.

        Display guard only:
        • no hydraulic calculation
        • no ProjectState mutation
        • no pipe resizing
        """
        display_row = dict(row or {})

        display_row["iter"] = self._clean_proportioned_iter_display_value_v1(
            row=display_row,
            raw_iter=display_row.get("iter", "—"),
            status=display_row.get("status", "—"),
        )

        return display_row



    def _make_pipe_section_mode_table_v1(
            self,
            parent: object = None,
    ) -> QTableWidget:
        """Build the universal one-cell pipe-section friction-mode display."""
        table = QTableWidget(1, 1, parent)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setFixedHeight(38)
        table.setMaximumWidth(210)
        table.setColumnWidth(0, 190)
        self._set_pipe_section_mode_table_v1(table, [])
        return table

    @staticmethod
    def _pipe_section_friction_mode_v1(rows: list[dict]) -> str:
        """
        Resolve the display mode from the rows actually shown in the table.

        Unknown rows do not manufacture Colebrook authority. Colebrook is
        shown only when every explicit visible method is Colebrook.
        """
        explicit_methods: set[str] = set()
        for row in rows or []:
            method = str(
                (row or {}).get("friction_method", "") or ""
            ).strip().casefold()
            if method and method not in {"—", "-", "unknown"}:
                explicit_methods.add(method)

        colebrook_active = bool(explicit_methods) and all(
            method.startswith("colebrook")
            for method in explicit_methods
        )
        return "Colebrook" if colebrook_active else "Haaland estimate"

    def _set_pipe_section_mode_table_v1(
            self,
            table: object,
            rows: list[dict],
    ) -> None:
        """Render the universal mode cell without hydraulic calculation."""
        if table is None:
            return

        evidence_view = self._clean_proportioned_evidence_view_v1()
        mode_text = (
            "Colebrook"
            if evidence_view == "Proportioning"
            else "Haaland estimate"
        )
        colebrook_active = mode_text == "Colebrook"
        item = QTableWidgetItem(mode_text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)

        font = item.font()
        font.setBold(True)
        point_size = font.pointSize()
        font.setPointSize(point_size if point_size > 0 else 10)
        item.setFont(font)
        item.setForeground(
            QBrush(
                QColor(255, 255, 255)
                if colebrook_active
                else QColor(0, 0, 0)
            )
        )
        item.setBackground(
            QBrush(
                QColor(46, 139, 87)
                if colebrook_active
                else QColor(232, 145, 55)
            )
        )
        table.setItem(0, 0, item)

    def _set_clean_proportioned_focused_section_rows_v1(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S33-K:
        Populate the focused section shell with placeholder rows only.

        H-S33-L will replace these placeholder rows with real section evidence.
        """
        if not hasattr(self, "_clean_proportioned_focused_section_table"):
            return

        table = self._clean_proportioned_focused_section_table
        visible_rows = [
            self._clean_proportioned_evidence_row_v1(dict(row or {}))
            for row in (rows or [])
        ]
        self._clean_proportioned_visible_section_rows_v1 = visible_rows
        self._set_pipe_section_mode_table_v1(
            getattr(self, "_clean_proportioned_section_mode_table", None),
            visible_rows,
        )

        columns = [
            "route",
            "section",
            "from",
            "to",
            "flow_kg_s",
            "pipe_dn",
            "dp_per_m",
            "length",
            "k",
            "section_dp",
            "iter",
            "status",
        ]

        # H-S41-B2 — render the explicitly selected evidence stage.
        table.setRowCount(len(visible_rows))

        for row_index, row in enumerate(visible_rows):
            display_row = self._clean_proportioned_section_display_row_v1(row)

            values = [
                display_row.get(column, "—")
                for column in columns
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value if value != "" else "—"))
                table.setItem(row_index, col_index, item)

        for row_index in range(table.rowCount()):
            table.setRowHeight(row_index, 24)

        self._configure_clean_proportioned_focused_section_table_v1()

        try:
            self._fit_table_height(table, min_height=110, max_height=220)
        except Exception:
            pass

        try:
            table.scrollToTop()
        except Exception:
            pass

    def _clean_proportioned_table_item_text_v1(self, item: object) -> str:
        """
        H-S33-L:
        Read plain text from a QTableWidgetItem-like object.
        """
        if item is None:
            return ""

        try:
            return str(item.text() or "").strip()
        except Exception:
            return str(item or "").strip()

    def _clean_proportioned_iter_display_value_v1(
            self,
            *,
            row: dict,
            raw_iter: object,
            status: object = "",
    ) -> str:
        """
        H-S33-M5:
        Display Iter only when the row explicitly represents a Colebrook
        friction solve.

        Iter means Colebrook iteration count only:
        • Haaland / first-pass Haaland rows show —
        • unknown method rows show —
        • no hydraulic calculation is performed here
        • no ProjectState mutation
        """
        iter_text = str(raw_iter or "").strip()

        if not iter_text or iter_text in {"—", "-"}:
            return "—"

        evidence_parts: list[str] = []

        for key in (
            "friction_method",
            "Friction method",
            "method",
            "Method",
            "solver",
            "Solver",
            "status",
            "Status",
            "friction_status",
            "Friction status",
            "calculation_method",
            "Calculation method",
            "source",
            "Source",
            "note",
            "Note",
            "notes",
            "Notes",
        ):
            if key in row and row.get(key) not in (None, ""):
                evidence_parts.append(str(row.get(key)))

        if status:
            evidence_parts.append(str(status))

        evidence_text = " ".join(evidence_parts).lower()

        if "colebrook" not in evidence_text:
            return "—"

        return iter_text



    def _normalise_clean_proportioned_section_source_row_v1(
            self,
            row: dict,
    ) -> dict:
        """
        H-S33-L:
        Normalise existing pipe/section evidence rows into the clean focused
        section table schema.

        This is display mapping only:
        • no new pressure calculation
        • no pipe resizing
        • no ProjectState mutation
        """
        def first_value(*keys: str) -> str:
            for key in keys:
                if key in row and row.get(key) not in (None, ""):
                    return str(row.get(key)).strip()
            return "—"

        route = first_value(
            "route",
            "Route",
            "route_label",
            "Route label",
            "subleg",
            "Subleg",
            "subleg_label",
            "Subleg label",
            "target",
            "Target",
            "target_label",
            "Target label",
            "scope",
            "Scope",
            "scope_label",
            "Scope label",
        )

        return {
            "route": route,
            # H-S36-A1: preserve stable section/route identity for the
            # later schematic trace mapping; display values remain unchanged.
            "section_id": first_value("section_id"),
            "route_code": first_value("route_code"),
            "leg_id": first_value("leg_id"),
            "subleg_id": first_value("subleg_id"),
            "route_id": first_value("route_id"),
            "subleg_role": first_value("subleg_role"),
            "takeoff_status": first_value("takeoff_status"),
            "section": first_value(
                "section",
                "order",
                "Order",
                "section_label",
                "section_id",
            ),
            "from": first_value(
                "from",
                "from_label",
                "from_node",
                "From",
            ),
            "to": first_value(
                "to",
                "to_label",
                "to_node",
                "To",
            ),
            "flow_kg_s": first_value(
                "flow_kg_s",
                "flow",
                "Flow kg/s",
                "mass_flow_kg_s",
            ),
            "pipe_dn": first_value(
                "pipe_dn",
                "pipe",
                "Pipe DN",
                "Pipe",
                "dn",
            ),
            "dp_per_m": first_value(
                "dp_per_m",
                "Δp/m",
                "dp_m",
                "pressure_gradient",
            ),
            "length": first_value(
                "length",
                "Length",
                "length_m",
            ),
            "k": first_value(
                "k",
                "K",
                "local_k",
                "k_total",
            ),
            "section_dp": first_value(
                "section_dp",
                "Section Δp",
                "section_dp_pa",
                "total_dp",
            ),
            "iter": self._clean_proportioned_iter_display_value_v1(
                row=row,
                raw_iter=first_value(
                    "iter",
                    "Iter",
                    "colebrook_iter",
                    "colebrook_iterations",
                    "iteration_count",
                    "iterations",
                    "friction_iterations",
                ),
                status=first_value(
                    "status",
                    "Status",
                ),
            ),
            "basic_pipe_dn": first_value(
                "basic_pipe_dn",
                "pipe",
                "Pipe",
            ),
            "basic_dp_per_m": first_value(
                "basic_dp_per_m",
                "Basic Δp/m",
            ),
            "basic_friction_method": first_value(
                "basic_friction_method",
                "Basic method",
            ),
            "proportioning_pipe_dn": first_value(
                "proportioning_pipe_dn",
                "pipe_dn",
                "Pipe DN",
                "pipe",
            ),
            "proportioning_dp_per_m": first_value(
                "proportioning_dp_per_m",
                "dp_per_m",
                "Δp/m",
            ),
            "proportioning_iter": first_value(
                "proportioning_colebrook_iterations",
                "proportioning_iter",
                "iter",
                "Iter",
            ),
            "proportioning_friction_method": first_value(
                "proportioning_friction_method",
                "friction_method",
                "Friction method",
                "method",
                "Method",
            ),
            "friction_method": first_value(
                "proportioning_friction_method",
                "friction_method",
                "Friction method",
                "method",
                "Method",
            ),
            "status": first_value(
                "status",
                "Status",
            ),
        }

    def _clean_proportioned_section_source_rows_from_tables_v1(
            self,
    ) -> list[dict]:
        """
        H-S33-L:
        Discover existing section evidence from already-populated table widgets.

        This is intentionally defensive so it can reuse the existing
        Proportioning Data section table without depending on one fragile
        widget name.
        """
        rows: list[dict] = []

        skip_names = {
            "_clean_proportioned_output_table",
            "_clean_proportioned_route_output_table",
            "_clean_proportioned_focused_section_table",
        }

        for attr_name, table in vars(self).items():
            if attr_name in skip_names:
                continue

            if not all(
                    hasattr(table, name)
                    for name in (
                        "rowCount",
                        "columnCount",
                        "horizontalHeaderItem",
                        "item",
                    )
            ):
                continue

            try:
                headers = [
                    self._clean_proportioned_table_item_text_v1(
                        table.horizontalHeaderItem(col_index)
                    )
                    for col_index in range(table.columnCount())
                ]
            except Exception:
                continue

            header_keys = {header.lower() for header in headers}

            looks_like_section_table = (
                {"from", "to"}.issubset(header_keys)
                and (
                    "flow kg/s" in header_keys
                    or "section Δp".lower() in header_keys
                    or "length" in header_keys
                    or "q carried" in header_keys
                )
            )

            if not looks_like_section_table:
                continue

            try:
                row_count = table.rowCount()
            except Exception:
                continue

            for row_index in range(row_count):
                raw_row: dict = {}

                for col_index, header in enumerate(headers):
                    if not header:
                        continue

                    try:
                        item = table.item(row_index, col_index)
                    except Exception:
                        item = None

                    raw_row[header] = self._clean_proportioned_table_item_text_v1(
                        item
                    )

                if any(value not in ("", "—") for value in raw_row.values()):
                    rows.append(
                        self._normalise_clean_proportioned_section_source_row_v1(
                            raw_row
                        )
                    )

        return rows

    def set_clean_proportioned_focused_section_source_rows_v1(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S33-L:
        Store explicit focused-section source rows.

        Adapter wiring can use this later; this milestone can also discover
        existing visible section evidence from current tables.
        """
        identity_rows = enrich_basic_ps_section_rows_with_route_identity_v1(
            [dict(row or {}) for row in (rows or [])]
        )

        self._clean_proportioned_focused_section_source_rows = [
            self._normalise_clean_proportioned_section_source_row_v1(row)
            for row in identity_rows
        ]

        self._refresh_clean_proportioned_schematic_section_evidence_v1()
        self._refresh_clean_proportioned_focused_section_view_v1()

    def _clean_proportioned_section_source_rows_v1(self) -> list[dict]:
        """
        H-S33-L:
        Return focused-section source rows, preferring explicit rows when set,
        otherwise discovering existing section evidence from visible tables.
        """
        explicit_rows = getattr(
            self,
            "_clean_proportioned_focused_section_source_rows",
            None,
        )

        if explicit_rows:
            return self._enrich_clean_proportioned_section_route_labels_v1(
                list(explicit_rows)
            )

        return self._enrich_clean_proportioned_section_route_labels_v1(
            self._clean_proportioned_section_source_rows_from_tables_v1()
        )

    def _clean_proportioned_route_matches_section_row_v1(
            self,
            *,
            route_label: str,
            row: dict,
    ) -> bool:
        """
        H-S33-L:
        Match a focused route label against a section row route/subleg label.
        """
        route_text = str(route_label or "").strip().lower()
        row_route = str(row.get("route", "") or "").strip().lower()

        if not route_text or not row_route or row_route == "—":
            return False

        return (
            route_text == row_route
            or route_text in row_route
            or row_route in route_text
        )

    def _clean_proportioned_section_rows_for_view_v1(
            self,
            *,
            mode: str,
            route_label: str,
            source_rows: list[dict],
    ) -> list[dict]:
        """
        H-S33-L:
        Apply the clean section view mode.

        Selected route only:
            returns matching route/subleg rows only.

        All routes:
            returns all available section rows.
        """
        if mode == "All routes":
            return list(source_rows)

        if not route_label:
            return []

        return [
            row
            for row in source_rows
            if self._clean_proportioned_route_matches_section_row_v1(
                route_label=route_label,
                row=row,
            )
        ]



    def _clean_proportioned_route_labels_from_output_table_v1(self) -> list[str]:
        """
        H-S33-M1:
        Read clean route labels from the clean Proportioned route-output table.
        """
        if not hasattr(self, "_clean_proportioned_route_output_table"):
            return []

        table = self._clean_proportioned_route_output_table
        labels: list[str] = []

        try:
            row_count = table.rowCount()
        except Exception:
            return []

        for row_index in range(row_count):
            label = self._clean_proportioned_route_label_for_row_v1(row_index)

            if label and label not in labels:
                labels.append(label)

        return labels

    def _clean_proportioned_route_token_from_text_v1(
            self,
            text: object,
    ) -> str:
        """
        H-S33-M1:
        Extract route token from labels such as:
            Leg 1A Common subleg
            R1 L1A-R01
            L2B
        """
        import re

        value = str(text or "").upper()

        match = re.search(r"\bL\s*(\d+[A-Z])\b", value)

        if match:
            return match.group(1)

        match = re.search(r"\bLEG\s*(\d+[A-Z])\b", value)

        if match:
            return match.group(1)

        return ""

    def _infer_clean_proportioned_route_label_for_section_row_v1(
            self,
            row: dict,
    ) -> str:
        """
        H-S33-M1:
        Infer section-row route label from endpoint text when the source
        section evidence does not already carry a route/subleg label.

        Display matching only:
        • no hydraulic calculation
        • no ProjectState mutation
        • no pipe resizing
        """
        existing = str(row.get("route", "") or "").strip()

        if existing and existing != "—":
            return existing

        endpoint_text = " ".join(
            str(row.get(key, "") or "")
            for key in (
                "from",
                "to",
                "section",
                "status",
            )
        )

        section_token = self._clean_proportioned_route_token_from_text_v1(
            endpoint_text
        )

        if not section_token:
            return existing or "—"

        for route_label in self._clean_proportioned_route_labels_from_output_table_v1():
            route_token = self._clean_proportioned_route_token_from_text_v1(
                route_label
            )

            if route_token and route_token == section_token:
                return route_label

        return existing or "—"

    def _enrich_clean_proportioned_section_route_labels_v1(
            self,
            rows: list[dict],
    ) -> list[dict]:
        """
        H-S33-M1:
        Add inferred route labels to section rows where possible.
        """
        enriched: list[dict] = []

        for row in rows:
            new_row = dict(row)
            new_row["route"] = (
                self._infer_clean_proportioned_route_label_for_section_row_v1(
                    new_row
                )
            )
            enriched.append(new_row)

        return enriched



    def _clean_proportioned_section_row_has_engineering_values_v1(
            self,
            row: dict,
    ) -> bool:
        """
        H-S33-M3:
        True when a focused section row carries real pipe/section engineering
        evidence rather than only endpoint/schematic text.

        Display filtering only:
        • no hydraulic calculation
        • no ProjectState mutation
        • no pipe resizing
        """
        for key in (
            "flow_kg_s",
            "pipe_dn",
            "dp_per_m",
            "length",
            "k",
            "section_dp",
            "iter",
        ):
            value = str(row.get(key, "") or "").strip()

            if value and value not in {"—", "-"}:
                return True

        return False

    def _clean_proportioned_prefer_engineering_section_rows_v1(
            self,
            rows: list[dict],
    ) -> list[dict]:
        """
        H-S33-M3 / H-S35-A3:
        Prefer real pipe/section evidence rows over endpoint-only rows.

        H-S35-A3: prefer named sections over matching fallbacks. When a
        numbered/named engineering row and an unnumbered discovered fallback
        share the same route and From → To endpoints, retain the named row and
        omit only its weaker fallback duplicate.

        If no engineering rows exist yet, keep the original rows so the
        fallback/placeholder behaviour remains visible.
        """
        engineering_rows = [
            row
            for row in rows
            if self._clean_proportioned_section_row_has_engineering_values_v1(
                row
            )
        ]

        if not engineering_rows:
            return rows

        def row_identity(row: dict) -> tuple[str, str, str] | None:
            values = tuple(
                str(row.get(key, "") or "").strip().casefold()
                for key in ("route", "from", "to")
            )

            if any(value in {"", "—", "-"} for value in values):
                return None

            return values

        def has_named_section(row: dict) -> bool:
            value = str(row.get("section", "") or "").strip()
            return value not in {"", "—", "-"}

        named_identities = {
            identity
            for row in engineering_rows
            if has_named_section(row)
            for identity in (row_identity(row),)
            if identity is not None
        }

        return [
            row
            for row in engineering_rows
            if (
                has_named_section(row)
                or row_identity(row) not in named_identities
            )
        ]



    def _clean_proportioned_focused_section_count_label_v1(
            self,
            *,
            base_label: str,
            rows: list[dict],
    ) -> str:
        """
        H-S33-M4:
        Build the focused section view label with a visible section count.

        Display polish only:
        • no hydraulic calculation
        • no ProjectState mutation
        • no pipe resizing
        """
        count = len(rows or [])

        if count <= 0:
            return f"{base_label} — no sections available"

        suffix = "section" if count == 1 else "sections"

        return f"{base_label} — showing {count} {suffix}"



    def _refresh_clean_proportioned_focused_section_view_v1(self) -> None:
        """
        H-S33-L:
        Refresh the focused route/subleg pipe-section table from existing
        section evidence where available.

        This remains read-only display wiring:
        • no new hydraulic calculation
        • no ProjectState mutation
        • no valve product / Kv / Kvs
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_clean_proportioned_focused_section_table"):
            return

        mode = self._clean_proportioned_section_view_mode_v1()
        route_label = self._clean_proportioned_focused_route_label_v1()
        source_rows = self._clean_proportioned_section_source_rows_v1()

        rows = self._clean_proportioned_section_rows_for_view_v1(
            mode=mode,
            route_label=route_label,
            source_rows=source_rows,
        )
        rows = self._clean_proportioned_prefer_engineering_section_rows_v1(
            rows
        )

        if mode == "All routes":
            label_text = self._clean_proportioned_focused_section_count_label_v1(
                base_label="Focused route: all routes",
                rows=rows,
            )

            if rows:
                status_rows = rows
            else:
                status_rows = [
                    {
                        "route": "All routes",
                        "section": "—",
                        "from": "—",
                        "to": "—",
                        "flow_kg_s": "—",
                        "pipe_dn": "—",
                        "dp_per_m": "—",
                        "length": "—",
                        "k": "—",
                        "section_dp": "—",
                        "iter": "—",
                        "status": (
                            "No pipe-section evidence rows available yet"
                        ),
                    }
                ]

        elif route_label:
            label_text = self._clean_proportioned_focused_section_count_label_v1(
                base_label=f"Focused route: {route_label}",
                rows=rows,
            )

            if rows:
                status_rows = rows
            else:
                status_rows = [
                    {
                        "route": route_label,
                        "section": "—",
                        "from": "—",
                        "to": "—",
                        "flow_kg_s": "—",
                        "pipe_dn": "—",
                        "dp_per_m": "—",
                        "length": "—",
                        "k": "—",
                        "section_dp": "—",
                        "iter": "—",
                        "status": (
                            "No matching pipe-section rows available for "
                            "selected route yet"
                        ),
                    }
                ]

        else:
            label_text = "Focused route: —"
            status_rows = [
                {
                    "route": "—",
                    "section": "—",
                    "from": "—",
                    "to": "—",
                    "flow_kg_s": "—",
                    "pipe_dn": "—",
                    "dp_per_m": "—",
                    "length": "—",
                    "k": "—",
                    "section_dp": "—",
                    "iter": "—",
                    "status": (
                        "Select a route row above to show its pipe sections"
                    ),
                }
            ]

        if hasattr(self, "_clean_proportioned_focused_section_label"):
            try:
                self._clean_proportioned_focused_section_label.setText(
                    label_text
                )
            except Exception:
                pass

        self._set_clean_proportioned_focused_section_rows_v1(status_rows)
        self._refresh_clean_proportioned_table_viewer_v1()



    def _apply_clean_proportioned_table_focus_style_v1(self, table: object) -> None:
        """
        H-S33-I:
        Apply the shared clean Proportioned table focus style.

        Visual polish only:
        • selected/focused row means "what I am looking at"
        • pale orange selected background
        • dark readable selected text
        • alternating rows remain active
        • no engineering colour meaning is added here
        • no ProjectState access
        • no pressure / authority calculation changes
        """
        if table is None:
            return

        try:
            table.setSelectionBehavior(
                QAbstractItemView.SelectionBehavior.SelectRows
            )
            table.setSelectionMode(
                QAbstractItemView.SelectionMode.SingleSelection
            )
        except AttributeError:
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)

        existing_style = str(table.styleSheet() or "")

        if "H-S33-I clean Proportioned focus style" in existing_style:
            return

        table.setStyleSheet(
            existing_style
            + """
/* H-S33-I clean Proportioned focus style */
QTableWidget {
    selection-background-color: rgb(246, 215, 168);
    selection-color: rgb(20, 20, 20);
}
QTableWidget::item:selected {
    background-color: rgb(246, 215, 168);
    color: rgb(20, 20, 20);
}
QTableWidget::item:selected:active {
    background-color: rgb(246, 215, 168);
    color: rgb(20, 20, 20);
}
QTableWidget::item:selected:!active {
    background-color: rgb(246, 215, 168);
    color: rgb(20, 20, 20);
}
"""
        )



    def _configure_clean_proportioned_output_summary_table_v1(self) -> None:
        """
        H-S33-H:
        Configure the clean Proportioned output summary table.

        Visual polish only:
        • no ProjectState access
        • no new preview calculations
        • no final proportioning commit
        • no valve product selection
        • no Kv / Kvs selection
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_clean_proportioned_output_table"):
            return

        table = self._clean_proportioned_output_table

        table.setWordWrap(False)
        table.setAlternatingRowColors(True)
        self._apply_clean_proportioned_table_focus_style_v1(table)
        table.setToolTip(
            "Clean Proportioned output summary — basis/projection output only; "
            "not final hydraulics."
        )

        widths = [
            190,  # Item
            760,  # Status
        ]

        for col_index, width in enumerate(widths):
            table.setColumnWidth(col_index, width)

        try:
            table.horizontalHeader().setStretchLastSection(True)
        except AttributeError:
            pass



    def _clean_proportioned_summary_status_v1(
            self,
            *,
            item: object,
            status: object,
    ) -> str:
        """
        H-S33-G:
        Build compact report-style status text for the clean Proportioned
        summary table.

        Wording polish only:
        • no ProjectState access
        • no new preview calculations
        • no final proportioning commit
        • no valve product selection
        • no Kv / Kvs selection
        • no pump selection
        • no pipe resizing
        """
        item_text = str(item or "").strip()
        status_text = str(status or "").strip()

        if not status_text:
            return "—"

        item_key = item_text.lower()
        status_key = status_text.lower()

        if item_key == "accepted return basis":
            if "committed basis snapshot:" in status_key:
                basis = status_text.split(":", 1)[1].split("—", 1)[0].strip()
                return f"Accepted basis — {basis} (basis only)"

            if "read-only preview available" in status_key:
                return "Waiting — accepted basis not committed"

            return status_text

        if item_key == "route pressure evidence":
            if "available" in status_key:
                return "Ready — route Δp evidence available"

            if "waiting" in status_key:
                return "Waiting — route Δp evidence"

            return status_text

        if item_key == "controlling / shortfall evidence":
            if "available" in status_key:
                return "Ready — controlling/shortfall evidence available"

            if "waiting" in status_key:
                return "Waiting — controlling/shortfall evidence"

            return status_text

        if item_key == "chosen-basis readiness":
            if "available" in status_key:
                return "Ready — chosen-basis readiness evidence available"

            return status_text

        if item_key == "basis-only export":
            if status_key.startswith("ready"):
                return "Ready — basis-only export; final hydraulics excluded"

            if status_key.startswith("not ready"):
                return "Not ready — commit accepted basis snapshot"

            return status_text

        if item_key == "valve authority preview":
            if status_key.startswith("ready with warnings"):
                return status_text

            if status_key.startswith("ready"):
                return status_text

            if "waiting" in status_key:
                return "Waiting — valve authority preview evidence"

            return status_text

        return status_text



    def set_clean_proportioned_output_rows(self, rows: list[dict]) -> None:
        """
        H-S20-A:
        Display future final-output status for the Proportioned tab.

        Display only:
        • no ProjectState access
        • no preview calculations
        • no final proportioning commit
        """
        if not hasattr(self, "_clean_proportioned_output_table"):
            return

        table = self._clean_proportioned_output_table
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

    def _configure_clean_proportioned_route_output_table_v1(self) -> None:
        """
        H-S33-E:
        Configure the clean Proportioned route-output table.

        Visual polish only:
        • no ProjectState access
        • no new preview calculations
        • no final proportioning commit
        • no valve product selection
        • no Kv / Kvs selection
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_clean_proportioned_route_output_table"):
            return

        table = self._clean_proportioned_route_output_table

        table.setWordWrap(False)
        table.setAlternatingRowColors(True)
        self._apply_clean_proportioned_table_focus_style_v1(table)
        self._wire_clean_proportioned_route_output_selection_v1(table)
        table.setToolTip(
            "Clean Proportioned route output projection only — "
            "not final hydraulics; no valve product, no Kv/Kvs, "
            "no pump selection, and no pipe resizing."
        )

        widths = [
            170,  # Route
            70,   # Basis
            75,   # Sections
            80,   # Flow kg/s
            80,   # Pipe DN
            75,   # Δp/m
            100,  # Chosen Δp
            110,  # Added Δp
            85,   # Authority
            360,  # Status
        ]

        for col_index, width in enumerate(widths):
            table.setColumnWidth(col_index, width)

        try:
            table.horizontalHeader().setStretchLastSection(True)
        except AttributeError:
            pass



    def set_clean_proportioned_route_output_rows(
            self,
            rows: list[dict],
    ) -> None:
        """
        H-S33-C:
        Display clean Proportioned route-output rows.

        Display shell only:
        • no ProjectState access
        • no new preview calculations
        • no final proportioning commit
        • no valve product selection
        • no Kv / Kvs selection
        • no pump selection
        • no pipe resizing
        """
        if not hasattr(self, "_clean_proportioned_route_output_table"):
            return

        if not rows:
            rows = [
                {
                    "route": "—",
                    "basis": "—",
                    "sections": "—",
                    "flow_kg_s": "—",
                    "pipe_dn": "—",
                    "dp_per_m": "—",
                    "route_dp": "—",
                    "added_dp": "—",
                    "authority": "—",
                    "status": (
                        "Waiting for clean Proportioned route output "
                        "projection"
                    ),
                }
            ]

        table = self._clean_proportioned_route_output_table
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get("route", "—"),
                row.get("basis", "—"),
                row.get("sections", "—"),
                row.get("flow_kg_s", "—"),
                row.get("pipe_dn", "—"),
                row.get("dp_per_m", "—"),
                row.get("route_dp", "—"),
                row.get("added_dp", "—"),
                row.get("authority", "—"),
                row.get("status", "—"),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        self._fit_table_height(table, min_height=150, max_height=260)
        self._configure_clean_proportioned_route_output_table_v1()
        self._refresh_clean_proportioned_focused_section_view_v1()
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

        if hasattr(self, "set_clean_proportioned_output_rows"):
            self.set_clean_proportioned_output_rows(rows)


    def set_route_shortfall_preview_rows(self, rows: list[dict]) -> None:
        """
        Display route-level Δp shortfall to the controlling route.
        """
        if not hasattr(self, "_route_shortfall_preview_table"):
            self._proportioning_snapshot_shortfall_rows = []
            return

        self._proportioning_snapshot_shortfall_rows = [
            dict(row)
            for row in (rows or [])
        ]

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
        self._refresh_proportioning_input_snapshot()

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
            (
                "Return arrangement basis",
                readiness.get("return_arrangement_basis", "—"),
            ),
            (
                "Return arrangement accepted",
                readiness.get("return_arrangement_accepted", "No"),
            ),
            (
                "Return arrangement status",
                readiness.get("return_arrangement_status", "—"),
            ),
            ("Proportioning status", readiness.get("status", "—")),
        ]

        table = self._proportioning_readiness_table
        table.setRowCount(len(rows))

        for row_index, (name, value) in enumerate(rows):
            table.setItem(row_index, 0, QTableWidgetItem(str(name)))
            table.setItem(row_index, 1, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()

    def set_commit_proportioning_callback(self, callback) -> None:
        """
        H-S26-G:
        Register adapter callback for Commit Proportioning.

        Panel remains observer/control surface only.
        """
        self._commit_proportioning_callback = callback

    def set_commit_proportioning_ready(
            self,
            *,
            ready: bool,
            reason: str = "",
    ) -> None:
        """
        H-S26-F:
        Display-only Commit Proportioning button gate.

        No ProjectState access.
        No proportioned-result write.
        No balancing mutation.
        No valve selection.
        No pump sizing.
        No pipe resizing.
        """
        button = getattr(self, "_commit_proportioning_button", None)
        if button is None:
            return

        ready = bool(ready)
        button.setEnabled(ready)

        if ready:
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: #43a047;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #2e7d32;
                    border-radius: 4px;
                    padding: 6px 10px;
                }
                QPushButton:hover {
                    background-color: #4caf50;
                }
                """
            )
            button.setToolTip(
                "Ready to commit proportioning basis. "
                "Final commit action is not implemented in this milestone."
            )
        else:
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: #e0e0e0;
                    color: #666666;
                    border: 1px solid #aaaaaa;
                    border-radius: 4px;
                    padding: 6px 10px;
                }
                """
            )
            button.setToolTip(
                reason
                or "Accept a Direct or Reverse return arrangement basis before "
                "committing proportioning."
            )

    def _on_commit_proportioning_button_clicked(self) -> None:
        """
        H-S26-G:
        Ask adapter to create the frozen accepted basis snapshot.

        Panel does not access ProjectState directly.
        """
        callback = getattr(
            self,
            "_commit_proportioning_callback",
            None,
        )

        if callable(callback):
            callback()
            return

        print(
            "H-S26-G Commit Proportioning callback is not registered."
        )

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

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """
        H-S19-M:
        Schematic click focus.

        Clicking a drawn room sends a focus payload back to the panel.
        Display/focus only; no engineering authority.
        """
        if event.button() != Qt.LeftButton:
            event.ignore()
            return

        pos = event.position()

        for rect, focus in reversed(self._room_hit_rects):
            if rect.contains(pos):
                self.set_focus(focus)

                if self._focus_callback is not None:
                    self._focus_callback(dict(focus))

                event.accept()
                return

        event.ignore()

    def set_focus(self, focus: dict | None) -> None:
        self._focus = {
            "leg_id": str((focus or {}).get("leg_id", "") or ""),
            "subleg_id": str((focus or {}).get("subleg_id", "") or ""),
            "room_id": str((focus or {}).get("room_id", "") or ""),
        }
        self.update()

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

    def _clear_preliminary_route_balancing_table_focus(self) -> None:
        table = getattr(self, "_preliminary_route_balancing_table", None)
        if table is None:
            return

        table.clearSelection()

        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item is not None:
                    item.setBackground(QBrush())

    def _focus_preliminary_route_balancing_row(self, row_index: int) -> None:
        table = getattr(self, "_preliminary_route_balancing_table", None)
        if table is None:
            return

        self._clear_preliminary_route_balancing_table_focus()

        if row_index < 0 or row_index >= table.rowCount():
            return

        focus_brush = QBrush(QColor(255, 238, 210))  # pale orange focus only

        for c in range(table.columnCount()):
            item = table.item(row_index, c)
            if item is not None:
                item.setBackground(focus_brush)

        first_item = table.item(row_index, 0)
        if first_item is not None:
            table.scrollToItem(
                first_item,
                QAbstractItemView.PositionAtCenter,
            )

    def _clear_common_main_leg_subleg_table_focus(self) -> None:
        table = getattr(self, "_common_main_leg_subleg_table", None)
        if table is None:
            return

        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item is not None:
                    item.setBackground(QBrush())
                    item.setForeground(QBrush())

    # ------------------------------------------------------------------
    # Mouse hover handling
    # ------------------------------------------------------------------

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
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