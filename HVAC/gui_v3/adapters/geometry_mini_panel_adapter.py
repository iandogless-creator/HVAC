# ======================================================================
# HVAC/gui_v3/adapters/geometry_mini_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Any

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel

from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1

class GeometryMiniPanelAdapter:
    """
    Geometry Mini Panel Adapter (GUI v3 — Overlay Model)

    Responsibilities
    ----------------
    • Prime GeometryMiniPanel from ProjectState
    • Prime GeometryMiniPanel from ProjectState
    • Receive committed geometry values
    • Apply geometry to ProjectState (authoritative)
    • Trigger topology resolution
    • Mark heat-loss dirty
    • Trigger global refresh

    Authority
    ---------
    • Reads and writes ProjectState
    • Does NOT construct polygons
    • Does NOT perform heat-loss calculations
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: GeometryMiniPanel,
        context: GuiProjectContext,
        refresh_all_callback,
    ) -> None:

        self._panel = panel
        self._context = context
        self._refresh_all = refresh_all_callback

        # Panel → commit
        self._panel.geometry_committed.connect(self._on_geometry_committed)
        self._panel.ti_changed.connect(self._on_ti_changed)
        # Context → refresh
        self._context.current_room_changed.connect(self._on_room_changed)

        self._prime_from_context()

    # ------------------------------------------------------------------
    # Context → Panel
    # ------------------------------------------------------------------
    def _on_ti_changed(self, value: float):
        room = self._context.current_room
        if room is None:
            return

        room.internal_temp_override_C = value

        self._context.project_state.mark_heatloss_dirty()
        self._context.emit_room_changed()

    def _on_room_changed(self, _room_id: Optional[str]) -> None:
        self._prime_from_context()

    def _prime_from_context(self) -> None:
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if ps is None or not room_id:
            self._panel.clear()
            return

        room = ps.rooms.get(room_id)
        if room is None:
            self._panel.clear()
            return

        # Header
        if hasattr(self._panel, "set_room_header"):
            self._panel.set_room_header(getattr(room, "name", ""))

        g = getattr(room, "geometry", None)

        if g is None:
            self._panel.set_values(None, None, None)
            return

        self._panel.set_values(
            length_m=g.length_m,
            width_m=g.width_m,
            height_m=g.height_m,
        )

    # ------------------------------------------------------------------
    # Panel → ProjectState
    # ------------------------------------------------------------------
    def _on_geometry_committed(self, values: dict) -> None:
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if ps is None or not room_id:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        g = getattr(room, "geometry", None)
        if g is None:
            return

        # --------------------------------------------------
        # 1. Authoritative geometry write
        # --------------------------------------------------
        try:
            L = float(values.get("length_m"))
            W = float(values.get("width_m"))
            H = float(values.get("height_m"))
        except (TypeError, ValueError):
            return

        g.length_m = L
        g.width_m = W
        g.height_m = H

        # --------------------------------------------------
        # 2. Topology resolution
        # --------------------------------------------------
        TopologyResolverV1.resolve_project(ps)

        # --------------------------------------------------
        # 3. Fabric rebuild (CORRECT)
        # --------------------------------------------------
        for r in ps.rooms.values():
            rows = FabricFromSegmentsV1.build_rows_for_room(ps, r)
            r.fabric_elements = rows

        # --------------------------------------------------
        # DEBUG (AFTER pipeline — this is critical)
        # --------------------------------------------------
        room_segments = ps.get_boundary_segments_for_room(room_id)
        print("Segments:", len(room_segments))

        fabric = getattr(room, "fabric_elements", [])
        print("Fabric:", len(fabric))
        # --------------------------------------------------
        # 4. Mark heat-loss dirty
        # --------------------------------------------------
        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

        # --------------------------------------------------
        # 5. Global refresh
        # --------------------------------------------------
        self._refresh_all()