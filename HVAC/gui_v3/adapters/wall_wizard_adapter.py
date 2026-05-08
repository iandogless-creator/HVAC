# ======================================================================
# HVAC/gui_v3/adapters/wall_wizard_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QWidget

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.wizards.wall_wizard import (
    WallWizardDialog,
    WallWizardProjection,
)


# ======================================================================
# Helpers
# ======================================================================

def _safe_get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    return getattr(obj, name, default)


def _normalise_element_label(value: Any) -> str:
    if value is None:
        return "—"

    text = str(value).replace("_", " ").strip()

    aliases = {
        "external wall": "External Wall",
        "internal wall": "Internal Wall",
        "inter room wall": "Internal Wall",
        "wall": "Wall",
        "roof": "Roof / Ceiling",
        "ceiling": "Roof / Ceiling",
        "floor": "Floor",
        "window": "Window / Door",
        "door": "Window / Door",
    }

    return aliases.get(text.lower(), text.title())


def _is_wall_label(label: str) -> bool:
    text = label.lower()
    return "wall" in text


# ======================================================================
# WallWizardAdapter
# ======================================================================

class WallWizardAdapter:
    """
    Opens the Wall Wizard in response to context intent.

    Responsibilities
    ----------------
    • listen for wall_wizard_requested(surface_id)
    • resolve display data from ProjectState / row projection
    • open read-only WallWizardDialog

    Explicitly forbidden
    --------------------
    • no ProjectState mutation
    • no U-value calculation
    • no surface U-value writes
    • no heat-loss calculation
    """

    def __init__(
        self,
        *,
        context: GuiProjectContext,
        parent: QWidget | None = None,
    ) -> None:
        self._context = context
        self._parent = parent
        self._dialog: Optional[WallWizardDialog] = None

        context.wall_wizard_requested.connect(self._open_for_surface)

    # ------------------------------------------------------------------
    # Open
    # ------------------------------------------------------------------

    def _open_for_surface(self, surface_id: str) -> None:

        projection = self._build_projection(surface_id)

        if projection is None:
            print("[WALL WIZARD ADAPTER] no projection")
            return

        if not _is_wall_label(projection.element_label):
            print("[WALL WIZARD ADAPTER] not wall:", projection.element_label)
            return

        if self._dialog is None:
            self._dialog = WallWizardDialog(parent=self._parent)

        self._dialog.set_projection(projection)
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def _build_projection(self, surface_id: str) -> Optional[WallWizardProjection]:
        ps = _safe_get(self._context, "project_state", None)
        if ps is None:
            ps = _safe_get(self._context, "_project_state", None)

        if ps is None:
            return None

        seg = None
        boundary_segments = _safe_get(ps, "boundary_segments", {}) or {}
        if surface_id:
            seg = boundary_segments.get(surface_id)

        room_id = _safe_get(seg, "owner_room_id", None)
        room_label = self._resolve_room_label(ps, room_id)

        # --------------------------------------------------
        # Element label
        # --------------------------------------------------
        boundary_kind = _safe_get(seg, "boundary_kind", None)

        if boundary_kind == "INTER_ROOM":
            element_label = "Internal Wall"
        elif boundary_kind == "EXTERNAL":
            element_label = "External Wall"
        else:
            # Wall Wizard A is launched only from wall rows, so fallback is OK.
            element_label = "Wall"

        # --------------------------------------------------
        # Area
        # --------------------------------------------------
        area_m2 = None

        length_m = _safe_get(seg, "length_m", None)

        room = None
        if room_id:
            rooms = _safe_get(ps, "rooms", {}) or {}
            room = rooms.get(room_id)

        height_m = None
        geometry = _safe_get(room, "geometry", None)
        if geometry is not None:
            height_m = _safe_get(geometry, "height_m", None)

        if height_m is None:
            env = _safe_get(ps, "environment", None)
            height_m = _safe_get(env, "default_room_height_m", None)

        if length_m is not None and height_m is not None:
            try:
                area_m2 = float(length_m) * float(height_m)
            except (TypeError, ValueError):
                area_m2 = None

        # --------------------------------------------------
        # Construction
        # --------------------------------------------------
        construction_id = self._resolve_construction_id(ps, surface_id, None)

        if construction_id is None and boundary_kind == "INTER_ROOM":
            construction_id = "DEV-INT-WALL"
        elif construction_id is None and boundary_kind == "EXTERNAL":
            construction_id = "DEV-EXT-WALL"

        construction = None
        if construction_id:
            constructions = _safe_get(ps, "constructions", {}) or {}
            construction = constructions.get(construction_id)

        construction_name = (
                _safe_get(construction, "name", None)
                or _safe_get(construction, "display_name", None)
                or construction_id
                or "—"
        )

        u_value = (
            _safe_get(construction, "u_value_W_m2K", None)
            if construction is not None
            else None
        )

        return WallWizardProjection(
            surface_id=surface_id,
            room_label=room_label,
            element_label=element_label,
            area_m2=area_m2,
            construction_id=construction_id,
            construction_name=construction_name,
            u_value_W_m2K=u_value,
        )

    def _find_row_for_surface(self, ps: Any, surface_id: str) -> Any:
        """
        Locate the current surface row.

        This is intentionally tolerant because row DTO shape has evolved
        across phases.
        """
        current_room_id = _safe_get(self._context, "current_room_id", None)
        if current_room_id is None:
            current_room_id = _safe_get(self._context, "_current_room_id", None)

        room = None
        if current_room_id:
            rooms = _safe_get(ps, "rooms", {}) or {}
            room = rooms.get(current_room_id)

        try:
            from HVAC.heatloss.fabric.row_builder_v1 import build_rows_with_meta

            rows_with_meta = build_rows_with_meta(ps, room)

            for item in rows_with_meta:
                row = item[0] if isinstance(item, tuple) else item
                sid = self._row_value(row, "surface_id", None)
                if sid == surface_id:
                    return row

        except Exception:
            pass

        return None

    def _resolve_construction_id(self, ps: Any, surface_id: str, row: Any = None) -> Optional[str]:
        surface_map = _safe_get(ps, "surface_construction_map", {}) or {}

        if surface_id in surface_map:
            return surface_map[surface_id]

        construction_id = self._row_value(row, "construction_id", None)
        if construction_id:
            return construction_id

        return None

    def _resolve_room_label(self, ps: Any, room_id: Optional[str]) -> str:
        if not room_id:
            return "—"

        rooms = _safe_get(ps, "rooms", {}) or {}
        room = rooms.get(room_id)

        return (
            _safe_get(room, "name", None)
            or _safe_get(room, "label", None)
            or room_id
        )

    def _row_value(self, row: Any, name: str, default: Any = None) -> Any:
        if row is None:
            return default

        if isinstance(row, dict):
            return row.get(name, default)

        return getattr(row, name, default)