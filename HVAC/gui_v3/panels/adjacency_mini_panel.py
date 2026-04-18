# ======================================================================
# HVAC/gui_v3/panels/adjacency_mini_panel.py
# ======================================================================

from __future__ import annotations

from typing import Optional, List, Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
)


# ======================================================================
# AdjacencyMiniPanelV1
# ======================================================================

class AdjacencyMiniPanelV1(QWidget):
    """
    Adjacency editor (overlay panel)

    Authority
    ---------
    • Emits intent only (assign / clear / cancel)
    • Does NOT mutate ProjectState
    • Does NOT compute adjacency
    • Does NOT infer segment pairing

    Interaction Model
    -----------------
    • Step 1 → select room
    • Step 2 → select segment
    • Assign → emits explicit segment-to-segment mapping

    States
    ------
    • Unassigned → room + segment selection
    • Assigned   → display + clear option
    """
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QComboBox

    # ------------------------------------------------------------------
    # Signals (controller / adapter contract)
    # ------------------------------------------------------------------
    assign_requested = Signal(str, str)   # source_seg_id, target_seg_id
    clear_requested = Signal(str)         # source_seg_id
    cancel_requested = Signal()
    adjacency_committed = Signal(str)  # emits selected room_id
    cancelled = Signal()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self._source_segment_id: Optional[str] = None

        self._room_options = []
        self._segments_by_room: Dict[str, list] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # --- Header ---------------------------------------------------
        self._title = QLabel("Adjacency")
        self._title.setStyleSheet("font-weight: 600;")
        root.addWidget(self._title)

        # --- Assigned info -------------------------------------------
        self._assigned_label = QLabel("")
        self._assigned_label.setVisible(False)
        root.addWidget(self._assigned_label)

        # --- Room selector (PRIMARY CONTROL) -------------------------
        self._room_combo = QComboBox(self)
        self._room_combo.currentIndexChanged.connect(self._on_room_changed)
        root.addWidget(self._room_combo)

        # --- Segment selector (FUTURE – disabled for now) ------------
        self._segment_combo = QComboBox(self)
        self._segment_combo.setEnabled(False)  # not used yet
        root.addWidget(self._segment_combo)

        # --- Buttons -------------------------------------------------
        btn_row = QHBoxLayout()

        self._assign_btn = QPushButton("Assign")
        self._assign_btn.clicked.connect(self._on_assign)
        btn_row.addWidget(self._assign_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self._clear_btn)

        self._cancel_btn = QPushButton("Close")
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        btn_row.addWidget(self._cancel_btn)

        root.addLayout(btn_row)

        # --- Initial state -------------------------------------------
        self._set_unassigned_state()

        # Debug (safe to remove later)
        print("room_combo exists:", hasattr(self, "_room_combo"))

    # ------------------------------------------------------------------
    # Public API (adapter calls)
    # ------------------------------------------------------------------
    def load_unassigned(
        self,
        source_segment_id: str,
        room_options: List,
        segments_by_room: Dict[str, list],
    ) -> None:
        """
        Populate panel for new adjacency assignment.
        """
        self._source_segment_id = source_segment_id
        self._room_options = room_options
        self._segments_by_room = segments_by_room

        self._assigned_label.setVisible(False)

        self._room_combo.blockSignals(True)
        self._room_combo.clear()

        for opt in room_options:
            label = f"{opt.name} ({opt.available_count} free)"
            self._room_combo.addItem(label, opt.room_id)

            idx = self._room_combo.count() - 1
            self._room_combo.model().item(idx).setEnabled(opt.enabled)

        self._room_combo.blockSignals(False)

        self._segment_combo.clear()
        self._segment_combo.setEnabled(False)

        self._set_unassigned_state()

    # ------------------------------------------------------------------
    def load_assigned(
        self,
        source_segment_id: str,
        room_name: str,
        segment_label: str,
    ) -> None:
        """
        Populate panel for existing adjacency.
        """
        self._source_segment_id = source_segment_id

        self._assigned_label.setText(
            f"Inter-room → {room_name} ({segment_label})"
        )
        self._assigned_label.setVisible(True)

        self._room_combo.setEnabled(False)
        self._segment_combo.setEnabled(False)

        self._assign_btn.setEnabled(False)
        self._clear_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Internal state helpers
    # ------------------------------------------------------------------
    def _set_unassigned_state(self) -> None:
        self._room_combo.setEnabled(True)
        self._segment_combo.setEnabled(False)

        self._assign_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Interaction handlers
    # ------------------------------------------------------------------
    def _on_room_changed(self, index: int) -> None:
        room_id = self._room_combo.itemData(index)

        if not room_id:
            self._assign_btn.setEnabled(False)
            return

        # --------------------------------------------------
        # Phase IV-B: room-only adjacency → ENABLE assign
        # --------------------------------------------------
        self._assign_btn.setEnabled(True)

        # --------------------------------------------------
        # Segment combo is FUTURE (leave disabled)
        # --------------------------------------------------
        self._segment_combo.clear()
        self._segment_combo.setEnabled(False)

    # ------------------------------------------------------------------
    def _on_segment_changed(self, index: int) -> None:
        if index < 0:
            self._assign_btn.setEnabled(False)
            return

        model_item = self._segment_combo.model().item(index)
        self._assign_btn.setEnabled(model_item.isEnabled())

    # ------------------------------------------------------------------
    def _on_assign(self) -> None:
        if self._source_segment_id is None:
            return

        room_id = self._room_combo.currentData()
        if not room_id:
            return

        print(f"[UI ASSIGN] {self._source_segment_id} -> {room_id}")

        self.adjacency_committed.emit(room_id)

    # ------------------------------------------------------------------
    def _on_apply(self) -> None:
        room_id = self._combo.currentData()
        if room_id:
            print(f"[AdjPanel] commit → {room_id}")
            self.adjacency_committed.emit(room_id)

    def _on_clear(self) -> None:
        if self._source_segment_id is None:
            return

        self.clear_requested.emit(self._source_segment_id)

    def _on_cancel(self) -> None:
        self.cancelled.emit()

    def set_context(
            self,
            *,
            segment_id: str,
            current_adjacent_room_id: str | None,
            room_options: list[str],
    ) -> None:

        print(f"[AdjPanel] segment={segment_id} current_adj={current_adjacent_room_id} options={room_options}")

        self._source_segment_id = segment_id

        # --- Populate room combo --------------------------------------
        self._room_combo.blockSignals(True)
        self._room_combo.clear()

        # Optional placeholder
        self._room_combo.addItem("— Select room —", None)

        for room_id in room_options:
            self._room_combo.addItem(room_id, room_id)

        # --- Set current selection ------------------------------------
        if current_adjacent_room_id:
            index = self._room_combo.findData(current_adjacent_room_id)
            if index >= 0:
                self._room_combo.setCurrentIndex(index)
                self._assigned_label.setText(f"Assigned to: {current_adjacent_room_id}")
                self._assigned_label.setVisible(True)
            else:
                self._room_combo.setCurrentIndex(0)
                self._assigned_label.setVisible(False)
        else:
            self._room_combo.setCurrentIndex(0)
            self._assigned_label.setVisible(False)

        self._room_combo.blockSignals(False)

        self._set_unassigned_state()
        self._on_room_changed(self._room_combo.currentIndex())
        # TODO (next step): populate dropdown
        # TODO (next step):
        # populate dropdown with available rooms