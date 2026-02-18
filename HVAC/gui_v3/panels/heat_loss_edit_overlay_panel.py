# ======================================================================
# HVAC/gui_v3/panels/heat_loss_edit_overlay_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from HVAC.heatloss.dto.heatloss_edit_intent_DTO import HeatLossEditIntentDTO


class HeatLossEditOverlayPanel(QWidget):
    """
    HLPE — Heat-Loss Edit Overlay Panel (GUI v3)

    Rules:
    - GUI-only, non-authoritative editor shell
    - Amber visual cue (edit mode)
    - ESC cancels always (handled by parent via signal or direct close)
    """

    apply_requested = Signal()
    cancel_requested = Signal()
    edit_intent_committed = Signal(object)  # HeatLossEditIntent

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Amber header strip (style kept minimal and local)
        header = QFrame(self)
        header.setObjectName("hlpe_header")
        header.setFrameShape(QFrame.StyledPanel)

        h = QHBoxLayout(header)
        h.setContentsMargins(10, 8, 10, 8)

        self._title = QLabel("EDIT MODE — Heat-Loss")
        self._title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        h.addWidget(self._title, 1)

        self._btn_apply = QPushButton("Apply")
        self._btn_cancel = QPushButton("Cancel")
        h.addWidget(self._btn_apply)
        h.addWidget(self._btn_cancel)

        self._btn_apply.clicked.connect(self.apply_requested.emit)
        self._btn_cancel.clicked.connect(self.cancel_requested.emit)

        root.addWidget(header)

        # Body placeholder (we’ll populate per scope)
        self._body = QLabel("Edit controls will appear here (geometry / assumptions / construction).")
        self._body.setWordWrap(True)
        self._body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        root.addWidget(self._body, 1)

        # Minimal styling: amber header only
        self.setStyleSheet(
            """
            QFrame#hlpe_header {
                background: rgba(255, 165, 0, 40);   /* amber tint */
                border: 1px solid rgba(255, 165, 0, 120);
                border-radius: 6px;
            }
            """
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_heading(self, text: str) -> None:
        self._title.setText(text)

    def set_body_text(self, text: str) -> None:
        self._body.setText(text)
