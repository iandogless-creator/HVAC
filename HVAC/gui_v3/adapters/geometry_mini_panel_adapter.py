# ======================================================================
# HVAC/gui_v3/adapters/geometry_mini_panel_adapter.py
# ======================================================================

from __future__ import annotations

from HVAC.heatloss.fabric.simple_fabric_generator import (
    generate_simple_fabric_elements,
)
from HVAC.topology.topology_resolver_v1 import TopologyResolverV1

class GeometryMiniPanelAdapter:
    """
    Geometry Mini Panel Adapter (Phase IV-A)

    Responsibilities
    ----------------
    • Synchronise panel fields with RoomGeometryV1 (rectangular)
    • Commit user edits into ProjectState
    • Trigger SIMPLE fabric generation when geometry becomes valid
    • Mark heat-loss state dirty

    Authority
    ---------
    • Does NOT construct UI
    • Does NOT perform heat-loss calculations
    • Owns NO geometry logic (only transfers intent)
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, panel, context):

        self._panel = panel
        self._context = context

        # --------------------------------------------------
        # Panel edit signals → commit geometry
        # --------------------------------------------------

        panel._edit_length.editingFinished.connect(self._commit)
        panel._edit_width.editingFinished.connect(self._commit)
        panel._edit_height.editingFinished.connect(self._commit)
        panel._edit_ext.editingFinished.connect(self._commit)
        panel._edit_ti.editingFinished.connect(self._commit)

        # --------------------------------------------------
        # Room selection → refresh panel
        # --------------------------------------------------

        panel.geometry_changed.connect(self._on_geometry_changed)
        self._context.room_state_changed.connect(self.refresh)
        self._context.current_room_changed.connect(lambda _: self.refresh())

        self.refresh()

    # ------------------------------------------------------------------
    # Refresh panel from ProjectState
    # ------------------------------------------------------------------

    def refresh(self) -> None:

        ps = self._context.project_state
        room = getattr(self._context, "current_room", None)

        if ps is None or room is None:
            return

        g = room.geometry
        env = ps.environment

        # --------------------------------------------------
        # Length / Width (authoritative geometry)
        # --------------------------------------------------

        self._panel._edit_length.setText(
            "" if g.length_m is None else str(g.length_m)
        )

        self._panel._edit_width.setText(
            "" if g.width_m is None else str(g.width_m)
        )

        # --------------------------------------------------
        # External wall length (user intent)
        # --------------------------------------------------

        self._panel._edit_ext.setText(
            "" if g.external_wall_length_m is None else str(g.external_wall_length_m)
        )

        # --------------------------------------------------
        # Height (room override → environment default)
        # --------------------------------------------------

        height = (
            g.height_m
            if g.height_m is not None
            else (env.default_room_height_m if env else None)
        )

        self._panel._edit_height.setText(
            "" if height is None else str(height)
        )

        # --------------------------------------------------
        # Internal temperature (room override → environment default)
        # --------------------------------------------------

        ti = (
            room.internal_temp_override_C
            if room.internal_temp_override_C is not None
            else (env.default_internal_temp_C if env else None)
        )

        self._panel._edit_ti.setText(
            "" if ti is None else str(ti)
        )

    # ------------------------------------------------------------------
    # Commit panel edits to ProjectState
    # ------------------------------------------------------------------

    def _commit(self) -> None:

        print("GMP commit fired")

        ps = self._context.project_state
        room_id = self._context.current_room_id

        if ps is None or room_id is None:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        g = room.geometry

        def num(edit):
            try:
                return float(edit.text())
            except Exception:
                return None

        # --------------------------------------------------
        # Read panel values
        # --------------------------------------------------

        g.length_m = num(self._panel._edit_length)
        g.width_m = num(self._panel._edit_width)
        g.height_m = num(self._panel._edit_height)
        g.external_wall_length_m = num(self._panel._edit_ext)
        TopologyResolverV1.resolve_project(ps)
        room.internal_temp_override_C = num(self._panel._edit_ti)

        # --------------------------------------------------
        # SIMPLE auto-fabric generation (rectangular trigger)
        # --------------------------------------------------

        if (
            g.length_m is not None
            and g.width_m is not None
            and g.height_m is not None
            and not room.fabric_elements
        ):
            generate_simple_fabric_elements(room)

        # --------------------------------------------------
        # Mark heat-loss state dirty
        # --------------------------------------------------

        ps.mark_heatloss_dirty()

        # --------------------------------------------------
        # Trigger UI refresh
        # --------------------------------------------------

        self._context.room_state_changed.emit(room.room_id)

    # ------------------------------------------------------------------
    # External geometry change hook (future-safe)
    # ------------------------------------------------------------------

    def _on_geometry_changed(self, data):

        ps = self._context.project_state
        room_id = self._context.current_room_id

        if ps is None or room_id is None:
            return

        room = ps.rooms.get(room_id)
        if room is None:
            return

        g = room.geometry

        # --------------------------------------------------
        # Apply incoming geometry (rectangular only)
        # --------------------------------------------------

        g.length_m = data.get("length_m")
        g.width_m = data.get("width_m")
        g.height_m = data.get("height_m")

        room.internal_temp_override_C = data.get("ti_C")

        # --------------------------------------------------
        # Regenerate simple fabric (explicit reset)
        # --------------------------------------------------

        room.fabric_elements.clear()
        generate_simple_fabric_elements(room)

        ps.mark_heatloss_dirty()

        self._context.room_state_changed.emit(room.room_id)