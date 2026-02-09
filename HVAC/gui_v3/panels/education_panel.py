# ======================================================================
# HVAC/gui_v3/panels/education_panel.py
# ======================================================================

"""
HVACgooee — GUI v3
Education Panel — Education v1 (CANONICAL)

Read-only educational text panel.

Rules
-----
• Presentation only
• No resolver imports
• No ProjectState access
• No calculations
• Mode toggle is UI-only
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
)


class EducationPanel(QWidget):
    """
    Education display panel.

    Shows:
    - Title
    - Body text
    - Standard / Classical toggle
    """

    # Emitted when user toggles mode
    mode_changed = Signal(str)  # "standard" | "classical"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._mode: str = "standard"

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # --------------------------------------------------------------
        # Header row
        # --------------------------------------------------------------
        header = QHBoxLayout()

        self._title = QLabel("Education")
        self._title.setStyleSheet(
            "font-weight: bold; font-size: 14px;"
        )

        header.addWidget(self._title)
        header.addStretch()

        self._btn_standard = QPushButton("Standard")
        self._btn_classical = QPushButton("Classical")

        for btn in (self._btn_standard, self._btn_classical):
            btn.setCheckable(True)
            btn.setFixedHeight(22)

        self._btn_standard.clicked.connect(
            lambda: self._set_mode("standard")
        )
        self._btn_classical.clicked.connect(
            lambda: self._set_mode("classical")
        )

        header.addWidget(self._btn_standard)
        header.addWidget(self._btn_classical)

        root.addLayout(header)

        # --------------------------------------------------------------
        # Divider
        # --------------------------------------------------------------
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        root.addWidget(divider)

        # --------------------------------------------------------------
        # Body text
        # --------------------------------------------------------------
        self._body = QTextEdit()
        self._body.setReadOnly(True)
        self._body.setFrameStyle(QFrame.NoFrame)
        self._body.setAcceptRichText(False)
        self._body.setStyleSheet(
            "QTextEdit { background: transparent; }"
        )

        root.addWidget(self._body, stretch=1)

        # Default state
        self._apply_mode_buttons()

    # ------------------------------------------------------------------
    # Adapter ingress
    # ------------------------------------------------------------------

    def set_content(
        self,
        *,
        title: str,
        body: str,
        mode: str,
    ) -> None:
        """
        Replace displayed education content.

        Called by EducationPanelAdapter only.
        """
        self._title.setText(title)
        self._body.setPlainText(body)

        self._mode = mode
        self._apply_mode_buttons()

    # ------------------------------------------------------------------
    # Mode handling (UI only)
    # ------------------------------------------------------------------

    def _set_mode(self, mode: str) -> None:
        if mode == self._mode:
            return

        self._mode = mode
        self._apply_mode_buttons()

        # Notify adapter
        self.mode_changed.emit(mode)

    def _apply_mode_buttons(self) -> None:
        self._btn_standard.setChecked(self._mode == "standard")
        self._btn_classical.setChecked(self._mode == "classical")

        if self._mode == "standard":
            self._btn_standard.setStyleSheet(
                "font-weight: bold;"
            )
            self._btn_classical.setStyleSheet("")
        else:
            self._btn_classical.setStyleSheet(
                "font-weight: bold;"
            )
            self._btn_standard.setStyleSheet("")
