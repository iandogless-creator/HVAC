# ======================================================================
# HVAC/gui_v3/controllers/overlay_editor_controller.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Qt

from HVAC.gui_v3.panels.adjacency_mini_panel import AdjacencyMiniPanelV1
from HVAC.gui_v3.adapters.adjacency_mini_panel_adapter import (
    AdjacencyMiniPanelAdapter,
)

# ======================================================================
# OverlayEditorController
# ======================================================================

class OverlayEditorController:
    """
    Overlay editor controller (Phase IV-B stable)

    Authority
    ---------
    • Owns overlay lifecycle
    • Ensures single active overlay
    • Delegates logic to adapters
    • Does NOT mutate ProjectState directly
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, main_window, context):

        self._main_window = main_window
        self._context = context

        self._active_overlay = None

    # ------------------------------------------------------------------
    # Geometry editor
    # ------------------------------------------------------------------
    def open_geometry_editor(self):

        from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
        from HVAC.gui_v3.adapters.geometry_mini_panel_adapter import (
            GeometryMiniPanelAdapter,
        )

        self._close_active()

        panel = GeometryMiniPanel(self._main_window)
        GeometryMiniPanelAdapter(panel, self._context)

        self._show_overlay(panel)

    # ------------------------------------------------------------------
    # ACH editor
    # ------------------------------------------------------------------
    def open_ach_editor(self):

        from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel
        from HVAC.gui_v3.adapters.ach_mini_panel_adapter import (
            ACHMiniPanelAdapter,
        )

        self._close_active()

        panel = ACHMiniPanel(self._main_window)
        ACHMiniPanelAdapter(panel, self._context)

        self._show_overlay(panel)

    # ------------------------------------------------------------------
    # Adjacency editor (CANONICAL)
    # ------------------------------------------------------------------
    def show_adjacency_editor(self, surface_id: str) -> None:

        self._close_active()

        adapter = AdjacencyMiniPanelAdapter(
            context=self._context,
            refresh_all_callback=self._main_window._refresh_all_adapters,
        )

        ctx = adapter.build_context(surface_id)
        if not ctx:
            return

        panel = AdjacencyMiniPanelV1(parent=self._main_window)

        panel.set_context(
            segment_id=ctx["segment_id"],
            current_adjacent_room_id=ctx["current_adjacent_room_id"],
            room_options=ctx["room_options"],
        )

        # Commit → adapter handles everything (symmetry + state)
        panel.adjacency_committed.connect(
            lambda rid: adapter.commit(surface_id, rid)
        )

        panel.cancelled.connect(panel.close)

        self._show_overlay(panel)

    # ------------------------------------------------------------------
    # Overlay management
    # ------------------------------------------------------------------
    def _close_active(self):
        if self._active_overlay:
            try:
                self._active_overlay.close()
            except Exception:
                pass
            self._active_overlay = None

    def _show_overlay(self, panel) -> None:
        """
        Minimal overlay display (stable)
        """

        self._active_overlay = panel

        panel.setWindowFlags(panel.windowFlags() | Qt.Tool)
        panel.setAttribute(Qt.WA_DeleteOnClose)

        # Position near main window (nice UX)
        mw = self._main_window
        if mw:
            geo = mw.geometry()
            x = geo.x() + geo.width() // 2 - 150
            y = geo.y() + geo.height() // 2 - 100
            panel.move(x, y)

        panel.show()