# ======================================================================
# HVAC/gui_v3/adapters/hlpe_overlay_adapter.py
# ======================================================================
# HVACgooee — HLPEOverlayAdapter (GUI v3)
# Phase: G-A — HLPE lifecycle skeleton
# Status: CANONICAL (clean)
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import QObject, QEvent, Qt

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.hlpe_overlay_panel import HLPEOverlayPanel


class HLPEOverlayAdapter(QObject):
    """
    HLPEOverlayAdapter — GUI v3

    Responsibilities (Phase G-A)
    ----------------------------
    • Own HLPE overlay lifecycle (show / hide)
    • Handle ESC exit
    • Remain UI-structural only

    Authority
    ---------
    • Does NOT perform edits
    • Does NOT mutate ProjectState
    • Does NOT perform calculations
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

        # Overlay starts hidden (explicit)
        self._panel.hide()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def show_overlay(self) -> None:
        """Show HLPE overlay."""
        if not self._panel.isVisible():
            self._panel.show()

    def hide_overlay(self) -> None:
        """Hide HLPE overlay."""
        if self._panel.isVisible():
            self._panel.hide()

    # ------------------------------------------------------------------
    # Edit mode control
    # ------------------------------------------------------------------
    def exit_edit_mode(self, *, reason: str) -> None:
        """
        Exit HLPE edit mode (ESC-driven).

        Phase G-A:
        • No commit
        • No mutation
        """

        if not self._panel.isVisible():
            return

        print(f"HLPE exited ({reason})")
        self._panel.hide()

    # ------------------------------------------------------------------
    # Qt event filter (ESC handling)
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.exit_edit_mode(reason="esc")
            return True

        return False