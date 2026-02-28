# ======================================================================
# HVAC/gui_v3/adapters/hlpe_overlay_adapter.py
# ======================================================================
# HVACgooee — HLPEOverlayAdapter (GUI v3)
# Phase: G-A — HLPE lifecycle skeleton
# Status: ACTIVE (skeleton)
# ======================================================================

from __future__ import annotations
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QEvent, Qt

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.hlpe_overlay_panel import HLPEOverlayPanel

class HLPEOverlayAdapter(QObject):
    """
    HLPEOverlayAdapter — GUI v3

    Phase G-A responsibilities:
    • Own HLPE overlay lifecycle (show / hide)
    • Observe GUI context (room focus, edit scope later)
    • NO editing logic
    • NO commit logic
    • NO calculations

    This is a structural skeleton only.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: HLPEOverlayPanel,
        context: GuiProjectContext,
    ) -> None:
        super().__init__()
        self._panel = panel
        self._context = context

        # Phase G-A:
        # No signals wired yet
        # Overlay remains hidden by default
        #self._panel.hide()

    # ------------------------------------------------------------------
    # Public API (future)
    # ------------------------------------------------------------------
    def show_overlay(self) -> None:
        """Show HLPE overlay (no scope yet)."""
        self._panel.show()

    def hide_overlay(self) -> None:
        """Hide HLPE overlay."""
        self._panel.hide()

    # ------------------------------------------------------------------
    # Edit mode control
    # ------------------------------------------------------------------
    def exit_edit_mode(self, *, reason: str) -> None:
        """
        Exit HLPE edit mode.

        Phase G-A.1:
        • Called on ESC
        • No commit
        • No mutation
        """

        if not self._panel.isVisible():
            return

        print("HLPE exited via ESC")
        self._hlpe_active = False
        self._notify_hlpe_changed(False)
        self._panel.hide()

    # ------------------------------------------------------------------
    # Qt event filter (ESC handling)
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.exit_edit_mode(reason="esc")
                return True

        return False
