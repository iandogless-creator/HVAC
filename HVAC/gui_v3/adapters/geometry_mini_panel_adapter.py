# ======================================================================
# HVAC/gui_v3/adapters/geometry_mini_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.geometry_mini_panel import GeometryMiniPanel

from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1

# ✅ NEW: canonical derived geometry
from HVAC.core.derived_geometry import (
    resolve_floor_area_m2,
    resolve_volume_m3,
)


class GeometryMiniPanelAdapter:
    """
    Geometry Mini Panel Adapter (GUI v3 — Overlay Model)

    Responsibilities
    ----------------
    • Prime panel from ProjectState
    • Apply committed geometry
    • Trigger fabric rebuild
    • Mark heat-loss dirty
    • Trigger global refresh

    Authority
    ---------
    • Reads/writes ProjectState
    • NO calculations (delegates to resolution layer)
    """

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

        # Context → refresh
        self._context.current_room_changed.connect(self._on_room_changed)

        # Internal temp
        self._panel.internal_temp_changed.connect(self._on_internal_temp_changed)

        self._prime_from_context()

    # ------------------------------------------------------------------
    # Context → Panel
    # ------------------------------------------------------------------
    def _on_internal_temp_changed(self, value: float) -> None:
        ps = self._context.project_state
        room_id = self._context.current_room_id

        if ps is None or not room_id:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        room.internal_temp_override_C = value

        # ✅ FIXED: correct signal usage
        self._context.room_state_changed.emit(room_id)
        self._context.room_state_changed.emit(room_id)

        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

        self._context.current_room_changed.emit(room_id)

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

        g = room.geometry

        # --------------------------------------------------
        # Geometry → panel
        # --------------------------------------------------
        if g:
            self._panel._spin_length.blockSignals(True)
            self._panel._spin_width.blockSignals(True)
            self._panel._spin_height.blockSignals(True)

            self._panel._spin_length.setValue(float(g.length_m or 0.0))
            self._panel._spin_width.setValue(float(g.width_m or 0.0))
            self._panel._spin_height.setValue(float(g.height_m or 0.0))

            self._panel._spin_length.blockSignals(False)
            self._panel._spin_width.blockSignals(False)
            self._panel._spin_height.blockSignals(False)

        # --------------------------------------------------
        # Internal temp resolution
        # --------------------------------------------------
        from HVAC.core.value_resolution import resolve_effective_internal_temp_C

        ti, _ = resolve_effective_internal_temp_C(ps, room)

        if ti is None:
            env = ps.environment
            ti = getattr(env, "default_internal_temp_C", 21.0) if env else 21.0

        self._panel._ti_spin.blockSignals(True)
        self._panel._ti_spin.setValue(float(ti))
        self._panel._ti_spin.blockSignals(False)

        # --------------------------------------------------
        # ✅ DERIVED VALUES (CANONICAL — NO INLINE MATH)
        # --------------------------------------------------
        floor_area = resolve_floor_area_m2(room)
        volume = resolve_volume_m3(room, ps)

        # ✅ SAFE API ONLY (no private label access)
        self._panel.set_floor_area(floor_area)
        self._panel.set_volume(volume)

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
        # 1. Authoritative write
        # --------------------------------------------------
        try:
            g.length_m = float(values.get("length_m"))
            g.width_m = float(values.get("width_m"))
            g.height_m = float(values.get("height_m"))
        except (TypeError, ValueError):
            return

        # --------------------------------------------------
        # 2. Fabric rebuild (derived pipeline)
        # --------------------------------------------------
        for r in ps.rooms.values():
            r.fabric_elements = FabricFromSegmentsV1.build_rows_for_room(ps, r)

        # --------------------------------------------------
        # Debug
        # --------------------------------------------------
        room_segments = ps.get_boundary_segments_for_room(room_id)
        print("Segments:", len(room_segments))

        fabric = getattr(room, "fabric_elements", [])
        print("Fabric:", len(fabric))

        # --------------------------------------------------
        # 3. Lifecycle
        # --------------------------------------------------
        if hasattr(ps, "mark_heatloss_dirty"):
            ps.mark_heatloss_dirty()

        # --------------------------------------------------
        # 4. Refresh
        # --------------------------------------------------
        self._refresh_all()