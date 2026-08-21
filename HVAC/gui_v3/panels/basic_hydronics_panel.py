# ======================================================================
# HVAC/gui_v3/panels/basic_hydronics_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QGroupBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QScrollArea,
    QFrame,
    QSizePolicy,
)

from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegSchematicV1,
    CommonMainLegSublegSchematicWidgetV1,
)


# ======================================================================
# BasicHydronicsPanel
# ======================================================================

class BasicHydronicsPanel(QWidget):
    """
    GUI v3 — Basic Hydronics Panel

    Role
    ----
    User-editable first-pass hydronic sizing assumptions.

    Authority
    ---------
    • Emits user intent only
    • Does not mutate ProjectState directly
    • Does not perform pipe sizing
    • Does not perform pressure-loss calculation
    • Does not call Colebrook or Darcy-Weisbach

    Basic method
    ------------
    Stores/edit assumptions for:

        nominal pipework dp ≈ index length × nominal pressure gradient

    The adapter owns ProjectState read/write.
    """

    intent_committed = Signal(dict)
    pass_to_proportioning_requested = Signal(dict)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_priming = False

        root = QVBoxLayout(self)

        title = QLabel("Basic Hydronics")
        title.setObjectName("BasicHydronicsTitle")
        root.addWidget(title)

        self._workspace_tabs = QTabWidget()
        self._workspace_tabs.setDocumentMode(True)
        self._workspace_tabs.tabBar().setExpanding(False)
        self._workspace_tabs.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )
        root.addWidget(self._workspace_tabs, 1)

        setup_tab = QWidget()
        setup_layout = QVBoxLayout(setup_tab)
        setup_layout.setContentsMargins(6, 6, 6, 6)
        setup_layout.setSpacing(6)
        self._workspace_tabs.addTab(setup_tab, "Setup")

        # --------------------------------------------------------------
        # Intent group
        # --------------------------------------------------------------
        intent_box = QGroupBox("First-pass sizing intent")
        intent_layout = QFormLayout(intent_box)

        self._basis_mode = QComboBox()
        # H-S69-A2: INDEX_LENGTH is the sole new-user v1 method.
        # Legacy persisted identities remain load-compatible in the model.
        self._basis_mode.addItem("INDEX_LENGTH")
        intent_layout.addRow("Method:", self._basis_mode)

        self._index_room = QComboBox()
        intent_layout.addRow("Index room:", self._index_room)

        self._index_emitter = QComboBox()
        intent_layout.addRow("Index emitter:", self._index_emitter)

        self._total_index_length = QDoubleSpinBox()
        self._total_index_length.setRange(0.0, 10000.0)
        self._total_index_length.setDecimals(2)
        self._total_index_length.setSuffix(" m")
        intent_layout.addRow("Index length:", self._total_index_length)

        self._nominal_gradient = QDoubleSpinBox()
        self._nominal_gradient.setRange(0.0, 100000.0)
        self._nominal_gradient.setDecimals(2)
        self._nominal_gradient.setSuffix(" Δp/m")
        intent_layout.addRow("Nominal Δp/m:", self._nominal_gradient)

        self._length_source = QComboBox()
        self._length_source.addItems(["unset", "user", "default", "derived"])
        intent_layout.addRow("Length source:", self._length_source)

        self._pressure_gradient_source = QComboBox()
        self._pressure_gradient_source.addItems(
            ["unset", "user", "default", "derived"]
        )
        intent_layout.addRow("Gradient source:", self._pressure_gradient_source)

        setup_layout.addWidget(intent_box)

        # --------------------------------------------------------------
        # Basic PS topology section projection
        # --------------------------------------------------------------
        self._ps_sections_table = QTableWidget(0, 10)
        self._ps_sections_table.setMinimumHeight(160)
        self._ps_sections_table.setHorizontalHeaderLabels(
            [
                "Order",
                "From",
                "To",
                "Q carried",
                "Flow kg/s",
                "Pipe",
                "v m/s",
                "Δp/m",
                "Index",
                "Terminal",
            ]
        )

        self._ps_sections_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._ps_sections_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._ps_sections_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._ps_sections_table.verticalHeader().setVisible(False)
        self._ps_sections_table.setAlternatingRowColors(True)

        ps_header = self._ps_sections_table.horizontalHeader()
        ps_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(1, QHeaderView.Stretch)
        ps_header.setSectionResizeMode(2, QHeaderView.Stretch)
        ps_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        ps_header.setSectionResizeMode(9, QHeaderView.ResizeToContents)

        # --------------------------------------------------------------
        # Read-only Basic PS projection tabs
        # --------------------------------------------------------------
        # Compatibility alias retained for existing projection tests.
        self._projection_tabs = self._workspace_tabs

        sections_tab = QWidget()
        sections_layout = QVBoxLayout(sections_tab)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.addWidget(self._ps_sections_table)

        self._projection_tabs.addTab(sections_tab, "Sections")

        schematic_tab = QWidget()
        schematic_layout = QVBoxLayout(schematic_tab)
        schematic_layout.setContentsMargins(0, 0, 0, 0)

        self._basic_ps_schematic_widget = (
            CommonMainLegSublegSchematicWidgetV1(self)
        )
        self._basic_ps_schematic_widget.set_hover_enabled_v1(True)
        self._basic_ps_schematic_scroll = QScrollArea(self)
        self._basic_ps_schematic_scroll.setWidgetResizable(False)
        self._basic_ps_schematic_scroll.setFrameShape(QFrame.NoFrame)
        self._basic_ps_schematic_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._basic_ps_schematic_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._basic_ps_schematic_scroll.setWidget(
            self._basic_ps_schematic_widget
        )
        schematic_layout.addWidget(self._basic_ps_schematic_scroll)
        self._projection_tabs.addTab(schematic_tab, "Schematic")

        pressure_preview_tab = QWidget()
        pressure_preview_layout = QVBoxLayout(pressure_preview_tab)
        pressure_preview_layout.setContentsMargins(0, 0, 0, 0)

        self._pressure_preview_table = QTableWidget(0, 7)
        self._pressure_preview_table.setHorizontalHeaderLabels(
            [
                "Order",
                "From",
                "To",
                "Δp/m",
                "Length m",
                "Section Δp",
                "Status",
            ]
        )
        self._pressure_preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._pressure_preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._pressure_preview_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._pressure_preview_table.verticalHeader().setVisible(False)
        self._pressure_preview_table.setAlternatingRowColors(True)

        pressure_header = self._pressure_preview_table.horizontalHeader()
        pressure_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        pressure_header.setSectionResizeMode(1, QHeaderView.Stretch)
        pressure_header.setSectionResizeMode(2, QHeaderView.Stretch)
        pressure_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        pressure_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        pressure_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        pressure_header.setSectionResizeMode(6, QHeaderView.Stretch)

        pressure_preview_layout.addWidget(self._pressure_preview_table)

        candidate_ranking_tab = QWidget()
        candidate_ranking_layout = QVBoxLayout(candidate_ranking_tab)
        candidate_ranking_layout.setContentsMargins(0, 0, 0, 0)

        self._candidate_ranking_table = QTableWidget(0, 8)
        self._candidate_ranking_table.setHorizontalHeaderLabels(
            [
                "Rank",
                "Candidate",
                "Leg",
                "Subleg",
                "Total length",
                "Total Δp",
                "Control",
                "Status",
            ]
        )
        self._candidate_ranking_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._candidate_ranking_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._candidate_ranking_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._candidate_ranking_table.verticalHeader().setVisible(False)
        self._candidate_ranking_table.setAlternatingRowColors(True)

        ranking_header = self._candidate_ranking_table.horizontalHeader()
        ranking_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        ranking_header.setSectionResizeMode(1, QHeaderView.Stretch)
        ranking_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        ranking_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        ranking_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        ranking_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        ranking_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        ranking_header.setSectionResizeMode(7, QHeaderView.Stretch)

        candidate_ranking_layout.addWidget(self._candidate_ranking_table)

        self._projection_tabs.addTab(pressure_preview_tab, "Pressure")
        self._projection_tabs.addTab(candidate_ranking_tab, "Candidates")

        self._basic_ps_flow_basis_label = QLabel(
            "Hydronic mass-flow basis: —"
        )
        self._basic_ps_flow_basis_label.setWordWrap(True)
        sections_layout.insertWidget(0, self._basic_ps_flow_basis_label)

        # --------------------------------------------------------------
        # Derived display group
        # --------------------------------------------------------------
        derived_box = QGroupBox("Read-only derived allowance")
        derived_layout = QFormLayout(derived_box)

        self._derived_allowance = QLabel("— Pa")
        derived_layout.addRow("Nominal pipework allowance:", self._derived_allowance)

        setup_layout.addWidget(derived_box)

        # --------------------------------------------------------------
        # Notes
        # --------------------------------------------------------------
        notes_box = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_box)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText(
            "Basic hydronic sizing notes. No pipe sizing is performed here."
        )
        notes_layout.addWidget(self._notes)

        self._notes.setMaximumHeight(82)
        setup_layout.addWidget(notes_box)

        # --------------------------------------------------------------
        # Actions
        # --------------------------------------------------------------
        action_row = QHBoxLayout()
        action_row.addStretch(1)

        self._commit_button = QPushButton("Apply")
        self._commit_button.setObjectName("basicHydronicsApplyAction")
        action_row.addWidget(self._commit_button)

        self._pass_to_proportioning_button = QPushButton("Pass to Proportioning")
        self._pass_to_proportioning_button.setObjectName(
            "basicHydronicsPassToProportioningAction"
        )
        action_row.addWidget(self._pass_to_proportioning_button)

        purpose_button_base = (
            "QPushButton { padding: 4px 14px; font-weight: 600; "
            "border-radius: 3px; } "
            "QPushButton:disabled { background: #eeeeee; color: #888888; "
            "border: 1px solid #cccccc; }"
        )
        self._commit_button.setStyleSheet(
            purpose_button_base
            + " QPushButton:enabled { background: #d9ead3; color: #1f3d1f; "
              "border: 1px solid #78a66a; }"
        )
        self._pass_to_proportioning_button.setStyleSheet(
            purpose_button_base
            + " QPushButton:enabled { background: #dbe9f6; color: #1d3550; "
              "border: 1px solid #7aa7cc; }"
        )

        self._handoff_status = QLabel("")
        self._handoff_status.setObjectName(
            "basicHydronicsPassToProportioningStatus"
        )
        self._handoff_status.setWordWrap(True)
        self._handoff_status.setVisible(False)
        root.addWidget(self._handoff_status)
        root.addLayout(action_row)
        setup_layout.addStretch(1)

        # H-S69-A2 — purpose-sized inputs and concise wrapped help.
        for control, width in (
            (self._basis_mode, 180),
            (self._index_room, 390),
            (self._index_emitter, 460),
            (self._total_index_length, 150),
            (self._nominal_gradient, 150),
            (self._length_source, 180),
            (self._pressure_gradient_source, 180),
        ):
            control.setMaximumWidth(width)

        self._basis_mode.setToolTip(
            "Basic PS v1 uses index length.\n"
            "Section-based selection remains deferred."
        )
        self._total_index_length.setToolTip(
            "Total paired route length used by the\n"
            "first-pass nominal allowance."
        )
        self._nominal_gradient.setToolTip(
            "Nominal pressure gradient for the\n"
            "first-pass index-length allowance."
        )
        self._commit_button.setToolTip(
            "Store the displayed Basic PS intent."
        )
        self._pass_to_proportioning_button.setToolTip(
            "Apply this intent, align the selected index terminal,\n"
            "then open the downstream Proportioning workspace."
        )

        # --------------------------------------------------------------
        # Signals
        # --------------------------------------------------------------
        self._commit_button.clicked.connect(self._emit_commit)
        self._pass_to_proportioning_button.clicked.connect(
            self._emit_pass_to_proportioning
        )

        self._total_index_length.valueChanged.connect(
            self._refresh_local_derived_display
        )
        self._nominal_gradient.valueChanged.connect(
            self._refresh_local_derived_display
        )

    def set_handoff_status(
            self,
            message: str,
            *,
            success: bool = False,
    ) -> None:
        """Show concise navigation feedback without owning its authority."""
        message = str(message or "")
        self._handoff_status.setText(message)
        self._handoff_status.setVisible(bool(message))
        self._handoff_status.setStyleSheet(
            "color: #2e7d32; font-weight: 600; padding: 3px 2px;"
            if success
            else "color: #9b3a24; font-weight: 600; padding: 3px 2px;"
        )

    # ==================================================================
    # Priming API — called by adapter
    # ==================================================================
    def set_room_options(
        self,
        options: list[tuple[str, str]],
        selected_room_id: Optional[str] = None,
    ) -> None:
        """
        options: [(room_id, display_name), ...]
        """
        self._is_priming = True
        try:
            self._index_room.clear()

            for room_id, display_name in options:
                self._index_room.addItem(display_name, room_id)

            if selected_room_id:
                index = self._index_room.findData(selected_room_id)
                if index >= 0:
                    self._index_room.setCurrentIndex(index)
        finally:
            self._is_priming = False

    def set_emitter_options(
        self,
        options: list[tuple[str, str]],
        selected_emitter_id: Optional[str] = None,
    ) -> None:
        """
        options: [(emitter_id, display_name), ...]
        """
        self._is_priming = True
        try:
            self._index_emitter.clear()

            for emitter_id, display_name in options:
                self._index_emitter.addItem(display_name, emitter_id)

            if selected_emitter_id:
                index = self._index_emitter.findData(selected_emitter_id)
                if index >= 0:
                    self._index_emitter.setCurrentIndex(index)
        finally:
            self._is_priming = False

    def prime_intent(self, intent: Optional[dict]) -> None:
        """
        Prime panel from adapter-owned DTO projection.

        The panel receives a plain dict to avoid owning ProjectState models.
        """
        self._is_priming = True
        try:
            intent = intent or {}

            basis_mode = str(intent.get("basis_mode") or "INDEX_LENGTH")

            if basis_mode == "ADVANCED_PROPORTIONING":
                basis_mode = "INDEX_LENGTH"

            self._set_combo_text(
                self._basis_mode,
                basis_mode,
            )

            self._set_optional_float(
                self._total_index_length,
                intent.get("total_index_length_m"),
            )
            self._set_optional_float(
                self._nominal_gradient,
                intent.get("nominal_pressure_gradient_Pa_per_m"),
            )

            self._set_combo_text(
                self._length_source,
                str(intent.get("length_source") or "unset"),
            )
            self._set_combo_text(
                self._pressure_gradient_source,
                str(intent.get("pressure_gradient_source") or "unset"),
            )

            self._notes.setPlainText(str(intent.get("notes") or ""))

            index_room_id = intent.get("index_room_id")
            if index_room_id:
                index = self._index_room.findData(index_room_id)
                if index >= 0:
                    self._index_room.setCurrentIndex(index)

            index_emitter_id = intent.get("index_emitter_id")
            if index_emitter_id:
                index = self._index_emitter.findData(index_emitter_id)
                if index >= 0:
                    self._index_emitter.setCurrentIndex(index)

        finally:
            self._is_priming = False

        self._refresh_local_derived_display()

    def set_basic_ps_flow_basis(self, text: str) -> None:
        """
        Display the read-only hydronic mass-flow basis used by Basic PS.

        H-S21-C:
        This is display only. Derived ΔT is not stored here.
        """
        if not hasattr(self, "_basic_ps_flow_basis_label"):
            return

        self._basic_ps_flow_basis_label.setText(
            text or "Hydronic mass-flow basis: —"
        )

    def set_basic_ps_sections(self, rows: list[dict[str, Any]]) -> None:
        """
        Replace read-only Basic PS topology section rows.

        Expected row keys:
        - order
        - from_label
        - to_room_label
        - carried_heat_W
        - carried_flow_kg_s
        - is_index_room
        - is_terminal
        """

        self._ps_sections_table.setRowCount(0)

        for row_data in rows:
            row_index = self._ps_sections_table.rowCount()
            self._ps_sections_table.insertRow(row_index)

            order = row_data.get("order", "")
            from_label = str(row_data.get("from_label", "") or "")
            to_room_label = str(row_data.get("to_room_label", "") or "")
            carried_heat_W = float(row_data.get("carried_heat_W") or 0.0)
            carried_flow_kg_s = float(row_data.get("carried_flow_kg_s") or 0.0)
            pipe_size_label = str(row_data.get("pipe_size_label", "") or "")
            velocity_m_s = float(row_data.get("velocity_m_s") or 0.0)
            pressure_gradient_Pa_per_m = float(
                row_data.get("pressure_gradient_Pa_per_m") or 0.0
            )
            is_index_room = bool(row_data.get("is_index_room", False))
            is_terminal = bool(row_data.get("is_terminal", False))

            values = [
                str(order),
                from_label,
                to_room_label,
                f"{carried_heat_W:.1f} W",
                f"{carried_flow_kg_s:.4f}",
                pipe_size_label,
                f"{velocity_m_s:.3f}",
                f"{pressure_gradient_Pa_per_m:.1f}",
                "⚑" if is_index_room else "",
                "Terminal" if is_terminal else "",
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col in (0, 3, 4, 5, 6, 7, 8, 9):
                    item.setTextAlignment(Qt.AlignCenter)

                self._ps_sections_table.setItem(row_index, col, item)

        self._ps_sections_table.resizeRowsToContents()

    def set_basic_ps_schematic(
        self,
        schematic: CommonMainLegSublegSchematicV1 | None,
    ) -> None:
        """Replace the read-only Basic PS schematic projection."""
        self._basic_ps_schematic_widget.set_schematic(schematic)

    def set_pressure_preview_rows(self, rows: list[dict[str, Any]]) -> None:
        """
        Replace read-only Basic PS pressure preview rows.

        Expected row keys:
        - order
        - from_label
        - to_room_label
        - pressure_gradient_Pa_per_m
        - section_length_m
        - section_pressure_drop_Pa
        - status
        """

        if not hasattr(self, "_pressure_preview_table"):
            return

        self._pressure_preview_table.setRowCount(0)

        for row_data in rows:
            row_index = self._pressure_preview_table.rowCount()
            self._pressure_preview_table.insertRow(row_index)

            order = row_data.get("order", "")
            from_label = str(row_data.get("from_label", "") or "")
            to_room_label = str(row_data.get("to_room_label", "") or "")

            pressure_gradient = row_data.get("pressure_gradient_Pa_per_m")
            section_length = row_data.get("section_length_m")
            section_pressure_drop = row_data.get("section_pressure_drop_Pa")
            status = str(row_data.get("status", "") or "")

            gradient_text = (
                "—"
                if pressure_gradient is None
                else f"{float(pressure_gradient):.1f}"
            )
            length_text = (
                "—"
                if section_length is None
                else f"{float(section_length):.1f}"
            )
            pressure_drop_text = (
                "—"
                if section_pressure_drop is None
                else f"{float(section_pressure_drop):.1f} Pa"
            )

            values = [
                str(order),
                from_label,
                to_room_label,
                gradient_text,
                length_text,
                pressure_drop_text,
                status,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col in (0, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)

                self._pressure_preview_table.setItem(row_index, col, item)

    def set_candidate_ranking_rows(self, rows: list[dict[str, Any]]) -> None:
        """
        Replace read-only Basic PS candidate ranking rows.

        Expected row keys:
        - rank
        - route_label
        - leg_id
        - subleg_id
        - total_length_m
        - total_pressure_drop_Pa
        - is_controlling_index
        - status
        """

        if not hasattr(self, "_candidate_ranking_table"):
            return

        self._candidate_ranking_table.setRowCount(0)

        for row_data in rows:
            row_index = self._candidate_ranking_table.rowCount()
            self._candidate_ranking_table.insertRow(row_index)

            rank = row_data.get("rank")
            route_label = str(row_data.get("route_label", "") or "")
            leg_id = str(row_data.get("leg_id", "") or "")
            subleg_id = str(row_data.get("subleg_id", "") or "")

            total_length_m = row_data.get("total_length_m")
            total_pressure_drop_Pa = row_data.get("total_pressure_drop_Pa")
            is_controlling = bool(row_data.get("is_controlling_index", False))
            status = str(row_data.get("status", "") or "")

            rank_text = "—" if rank is None else str(rank)
            total_length_text = (
                "—"
                if total_length_m is None
                else f"{float(total_length_m):.1f} m"
            )
            total_pressure_drop_text = (
                "—"
                if total_pressure_drop_Pa is None
                else f"{float(total_pressure_drop_Pa):.1f} Pa"
            )

            values = [
                rank_text,
                route_label,
                leg_id,
                subleg_id,
                total_length_text,
                total_pressure_drop_text,
                "Yes" if is_controlling else "",
                status,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col in (0, 2, 3, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignCenter)

                self._candidate_ranking_table.setItem(row_index, col, item)

    # ==================================================================
    # Display helpers
    # ==================================================================
    def set_derived_allowance_Pa(self, value: Optional[float]) -> None:
        if value is None:
            self._derived_allowance.setText("— Pa")
            return

        self._derived_allowance.setText(f"{value:.1f} Pa")

    def _refresh_local_derived_display(self) -> None:
        """
        Local display only.

        This is not real pressure-loss calculation.
        It merely previews the basic nominal allowance:
            length × nominal Δp/m
        """
        length = self._total_index_length.value()
        gradient = self._nominal_gradient.value()

        if length <= 0.0 or gradient <= 0.0:
            self.set_derived_allowance_Pa(None)
            return

        self.set_derived_allowance_Pa(length * gradient)

    def current_index_room_id(self) -> str:
        return str(self._index_room.currentData() or "")

    def current_index_emitter_id(self) -> str:
        return str(self._index_emitter.currentData() or "")

    # ==================================================================
    # Intent emission
    # ==================================================================
    def _current_intent_payload(self) -> dict:
        return {
            "basis_mode": self._basis_mode.currentText(),
            "index_room_id": self._index_room.currentData(),
            "index_emitter_id": self._index_emitter.currentData(),
            "total_index_length_m": self._optional_spin_value(
                self._total_index_length
            ),
            "nominal_pressure_gradient_Pa_per_m": self._optional_spin_value(
                self._nominal_gradient
            ),
            "length_source": self._length_source.currentText(),
            "pressure_gradient_source": self._pressure_gradient_source.currentText(),
            "notes": self._notes.toPlainText(),
        }

    def _emit_commit(self) -> None:
        if self._is_priming:
            return

        self.intent_committed.emit(self._current_intent_payload())

    def _emit_pass_to_proportioning(self) -> None:
        """
        Emit a Basic → Proportioning handoff request.

        H-S8-L-B:
        The panel does not perform proportioning or mutate topology.
        It only emits the current Basic intent payload.
        """
        if self._is_priming:
            return

        self.pass_to_proportioning_requested.emit(
            self._current_intent_payload()
        )

    def clear_basic_ps_sections(self) -> None:
        self._ps_sections_table.setRowCount(0)

    # ==================================================================
    # Small helpers
    # ==================================================================
    @staticmethod
    def _optional_spin_value(spin: QDoubleSpinBox) -> Optional[float]:
        value = float(spin.value())
        if value <= 0.0:
            return None
        return value

    @staticmethod
    def _set_optional_float(spin: QDoubleSpinBox, value: object) -> None:
        try:
            if value is None:
                spin.setValue(0.0)
            else:
                spin.setValue(float(value))
        except (TypeError, ValueError):
            spin.setValue(0.0)

    @staticmethod
    def _set_combo_text(combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
