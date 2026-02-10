# ======================================================================
# HVAC/gui_v2/header/top_mode_bar.py
# ======================================================================

"""
Top Mode Bar — GUI v2

Provides:
- Mode selection buttons (Comfort / Heatloss / Hydronics / Fenestration / About)
- Education toggle (non-exclusive)

Rules:
- GUI only (no engines, no physics)
- Reflects GuiViewState
- Owns its own visual state
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QButtonGroup,
    QSizePolicy,
)

from HVAC.gui_v2.common.gui_view_state import GuiViewState


# ============================================================================
# Top Mode Bar
# ============================================================================

class TopModeBar(QWidget):
    """
    Top mode selector for GUI v2.
    """

    # Emitted when a MODE button is clicked
    mode_changed = Signal(str)
    education_toggled = Signal(bool)

    def __init__(self, view_state: GuiViewState, parent=None):
        super().__init__(parent)

        # Shared GUI state (read/write)
        self.view_state = view_state

        # Internal visual state (NOT authoritative)
        self._active_mode: str = "comfort"
        self._education_enabled: bool = False

        # Build UI FIRST
        self._build_ui()

        # Apply initial visual state
        self.set_active_mode(self._active_mode)
        self.set_education_enabled(self._education_enabled)

    # ------------------------------------------------------------------
    # UI Construction (single source of truth)
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Exclusive mode buttons
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        self._mode_buttons: dict[str, QPushButton] = {}

        for mode in (
            "comfort",
            "heatloss",
            "hydronics",
            "fenestration",
            "about",
        ):
            btn = QPushButton(mode.capitalize())
            btn.setCheckable(True)

            # --- Size correctly for bold text ---
            font = btn.font()
            font.setBold(True)
            btn.setFont(font)
            btn.adjustSize()
            min_width = btn.width()

            font.setBold(False)
            btn.setFont(font)

            btn.setMinimumWidth(min_width)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            # -----------------------------------

            btn.clicked.connect(
                lambda _, m=mode: self._on_mode_clicked(m)
            )

            self._mode_group.addButton(btn)
            self._mode_buttons[mode] = btn
            layout.addWidget(btn)

        # ------------------------------------------------------------
        # Education toggle (NON-exclusive)
        # ------------------------------------------------------------
        self.education_btn = QPushButton("Education")
        self.education_btn.setCheckable(True)
        self.education_btn.toggled.connect(self._on_education_toggled)
        layout.addWidget(self.education_btn)

        layout.addStretch(1)

    # ------------------------------------------------------------------
    # Mode handling
    # ------------------------------------------------------------------

    def _on_mode_clicked(self, mode: str) -> None:
        """
        User clicked a MODE button.
        """
        self._active_mode = mode
        self.set_active_mode(mode)
        self.mode_changed.emit(mode)
        education_toggled = Signal(bool)

    def set_active_mode(self, mode: str) -> None:
        """
        Visually select active MODE button (no signals).
        """
        btn = self._mode_buttons.get(mode)
        if btn:
            btn.setChecked(True)

    # ------------------------------------------------------------------
    # Education handling
    # ------------------------------------------------------------------

    def _on_education_toggled(self, checked: bool) -> None:
        self._education_enabled = checked
        self.set_education_enabled(checked)
        self.education_toggled.emit(checked)

    def set_education_enabled(self, enabled: bool) -> None:
        """
        Sync education toggle visually without emitting signals.
        """
        self.education_btn.blockSignals(True)
        self.education_btn.setChecked(enabled)
        self.education_btn.blockSignals(False)


# ======================================================================
# END FILE
# ======================================================================
