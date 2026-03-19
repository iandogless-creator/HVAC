# ======================================================================
# HVAC/gui_v3/controllers/overlay_editor_controller.py
# ======================================================================

from __future__ import annotations


class OverlayEditorController:
    """
    Manages temporary mini-panel editors launched from HLP.

    Responsibilities
    ----------------
    • Show geometry editor
    • Show ACH editor
    • Ensure only one overlay active
    • Position overlay relative to HLP
    """

    def __init__(self, main_window, context):

        self._main_window = main_window
        self._context = context

        self._active_editor = None

    # ------------------------------------------------------------------
    # Geometry editor
    # ------------------------------------------------------------------

    def open_geometry_editor(self):

        from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel
        from HVAC.gui_v3.adapters.geometry_mini_panel_adapter import GeometryMiniPanelAdapter

        if self._active_editor:
            self._active_editor.close()

        panel = GeometryMiniPanel(self._main_window)
        GeometryMiniPanelAdapter(panel, self._context)

        panel.setWindowFlags(panel.windowFlags() | panel.Tool)

        panel.show()

        self._active_editor = panel

    # ------------------------------------------------------------------
    # ACH editor
    # ------------------------------------------------------------------

    def open_ach_editor(self):

        from HVAC.gui_v3.panels.ach_mini_panel import ACHMiniPanel
        from HVAC.gui_v3.adapters.ach_mini_panel_adapter import ACHMiniPanelAdapter

        if self._active_editor:
            self._active_editor.close()

        panel = ACHMiniPanel(self._main_window)
        ACHMiniPanelAdapter(panel, self._context)

        panel.setWindowFlags(panel.windowFlags() | panel.Tool)

        panel.show()

        self._active_editor = panel