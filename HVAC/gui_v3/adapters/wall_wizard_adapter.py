# ======================================================================
# HVAC/gui_v3/adapters/wall_wizard_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.wizards.wall_wizard import (
    WallWizardDialog,
    WallWizardProjection,
)
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
)
from HVAC.gui_v3.wizards.wall_wizard import (
    WallWizardDialog,
    WallWizardProjection,
    OpeningPreview,
)

from HVAC.core.opening_schedule_v1 import OpeningScheduleItemV1

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
    • resolve display data from ProjectState
    • open read-only WallWizardDialog

    Explicitly forbidden
    --------------------
    • no ProjectState mutation
    • no U-value calculation
    • no surface U-value writes
    • no heat-loss calculation
    """
    opening_requested = Signal(str, str)  # surface_id, opening_type

    def __init__(
        self,
        *,
        context: GuiProjectContext,
        parent: QWidget | None = None,
    ) -> None:
        self._context = context
        self._parent = parent
        self._dialog: Optional[WallWizardDialog] = None
        self._dialog_project_state: Any = None

        self._context.wall_wizard_requested.connect(
            self._open_for_surface
        )
        self._context.project_changed.connect(
            self._on_project_changed
        )
        self._context.current_room_changed.connect(
            self._on_current_room_changed
        )



    # ------------------------------------------------------------------
    # Dialog lifecycle
    # ------------------------------------------------------------------

    def _project_state_from_context(self) -> Any:
        ps = _safe_get(self._context, "project_state", None)
        if ps is None:
            ps = _safe_get(self._context, "_project_state", None)
        return ps

    def _dismiss_dialog(self) -> None:
        dialog = self._dialog
        self._dialog = None
        self._dialog_project_state = None
        if dialog is not None:
            dialog.close()

    def _on_project_changed(self) -> None:
        if self._dialog is None:
            return
        if self._dialog_project_state is self._project_state_from_context():
            return
        self._dismiss_dialog()

    def _on_current_room_changed(self, _room_id: Any) -> None:
        self._dismiss_dialog()

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

            self._dialog.opening_requested.connect(
                self._on_opening_requested
            )
            self._dialog.opening_remove_requested.connect(
                self._on_opening_remove_requested
            )
            self._dialog.openings_clear_requested.connect(
                self._on_openings_clear_requested
            )

        self._dialog_project_state = self._project_state_from_context()
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

        boundary_segments = _safe_get(ps, "boundary_segments", {}) or {}
        seg = boundary_segments.get(surface_id) if surface_id else None

        room_id = _safe_get(seg, "owner_room_id", None)
        room_label = self._resolve_room_label(ps, room_id)
        boundary_kind = _safe_get(seg, "boundary_kind", None)

        # --------------------------------------------------
        # Element label
        # --------------------------------------------------
        if boundary_kind == "INTER_ROOM":
            element_label = "Internal Wall"
        elif boundary_kind == "EXTERNAL":
            element_label = "External Wall"
        else:
            element_label = "Wall"

        # --------------------------------------------------
        # Area
        # --------------------------------------------------
        if boundary_kind == "EXTERNAL":
            # V1 rule:
            # clicking any external wall opens the room-level external opening schedule.
            area_m2 = self._external_wall_gross_area_for_room(ps, room_id)
        else:
            # Internal walls remain selected-segment based for now.
            area_m2 = self._segment_wall_area(ps, seg, room_id)

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
            openings=self._opening_previews_for_room(ps, room_id),
            opening_construction_choices=self._opening_construction_choices(ps),
        )

    def _external_wall_gross_area_for_room(self, ps: Any, room_id: str | None) -> Optional[float]:
        if not room_id:
            return None

        rooms = _safe_get(ps, "rooms", {}) or {}
        room = rooms.get(room_id)
        if room is None:
            return None

        geometry = _safe_get(room, "geometry", None)
        height_m = _safe_get(geometry, "height_m", None)

        if height_m is None:
            env = _safe_get(ps, "environment", None)
            height_m = _safe_get(env, "default_room_height_m", None)

        if height_m is None:
            return None

        boundary_segments = _safe_get(ps, "boundary_segments", {}) or {}

        total_length_m = 0.0

        for seg in boundary_segments.values():
            if _safe_get(seg, "owner_room_id", None) != room_id:
                continue

            if _safe_get(seg, "boundary_kind", None) != "EXTERNAL":
                continue

            length_m = _safe_get(seg, "length_m", None)
            if length_m is None:
                continue

            try:
                total_length_m += float(length_m)
            except (TypeError, ValueError):
                continue

        if total_length_m <= 0.0:
            return None

        return total_length_m * float(height_m)

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

    def _external_wall_gross_area_for_room(
            self,
            ps: Any,
            room_id: str | None,
    ) -> Optional[float]:
        """
        V1 external-opening rule.

        Any external wall click opens the room-level external wall schedule.
        Therefore gross area is the total external wall area for the room,
        not only the selected segment area.
        """
        if not room_id:
            return None

        height_m = self._resolve_room_height(ps, room_id)
        if height_m is None:
            return None

        boundary_segments = _safe_get(ps, "boundary_segments", {}) or {}

        total_length_m = 0.0

        for seg in boundary_segments.values():
            if _safe_get(seg, "owner_room_id", None) != room_id:
                continue

            if _safe_get(seg, "boundary_kind", None) != "EXTERNAL":
                continue

            length_m = _safe_get(seg, "length_m", None)
            if length_m is None:
                continue

            try:
                total_length_m += float(length_m)
            except (TypeError, ValueError):
                continue

        if total_length_m <= 0.0:
            return None

        return total_length_m * float(height_m)

    def _segment_wall_area(
            self,
            ps: Any,
            seg: Any,
            room_id: str | None,
    ) -> Optional[float]:
        """
        Selected-segment wall area.

        Used for internal walls for now.
        """
        length_m = _safe_get(seg, "length_m", None)
        height_m = self._resolve_room_height(ps, room_id)

        if length_m is None or height_m is None:
            return None

        try:
            return float(length_m) * float(height_m)
        except (TypeError, ValueError):
            return None

    def _resolve_room_height(
            self,
            ps: Any,
            room_id: str | None,
    ) -> Optional[float]:
        if not room_id:
            return None

        rooms = _safe_get(ps, "rooms", {}) or {}
        room = rooms.get(room_id)

        geometry = _safe_get(room, "geometry", None)
        height_m = _safe_get(geometry, "height_m", None)

        if height_m is not None:
            return height_m

        env = _safe_get(ps, "environment", None)
        return _safe_get(env, "default_room_height_m", None)

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

    # ------------------------------------------------------------------
    # Opening intent
    # ------------------------------------------------------------------
    def _room_id_for_surface(
            self,
            ps: Any,
            surface_id: str,
    ) -> Optional[str]:
        boundary_segments = _safe_get(ps, "boundary_segments", {}) or {}
        seg = boundary_segments.get(surface_id)

        return _safe_get(seg, "owner_room_id", None)

    def _opening_construction_choices(
            self,
            ps: Any,
    ) -> list[tuple[str, str, str]]:
        choices: list[tuple[str, str, str]] = []
        constructions = _safe_get(ps, "constructions", {}) or {}
        for construction_id, construction in constructions.items():
            cid = str(construction_id)
            cid_upper = cid.upper()
            if cid_upper.startswith("USR-DECLARED-WINDOW-") or cid_upper == "DEV-WINDOW":
                opening_type = "WINDOW"
            elif cid_upper.startswith("USR-DECLARED-DOOR-") or cid_upper in {
                "DEV-EXT-DOOR",
                "DEV-INT-DOOR",
            }:
                opening_type = "DOOR"
            else:
                continue
            name = str(
                _safe_get(construction, "name", None)
                or _safe_get(construction, "display_name", None)
                or cid
            )
            choices.append((cid, name, opening_type))
        return sorted(choices, key=lambda row: (row[2], row[1].lower(), row[0]))

    def _opening_previews_for_room(
            self,
            ps: Any,
            room_id: str | None,
    ) -> list[OpeningPreview]:
        if not room_id:
            return []
        schedules = _safe_get(ps, "room_opening_schedules", {}) or {}
        schedule = schedules.get(room_id)
        if schedule is None:
            return []
        constructions = _safe_get(ps, "constructions", {}) or {}
        previews: list[OpeningPreview] = []
        for item in _safe_get(schedule, "openings", []) or []:
            construction_id = str(_safe_get(item, "construction_id", "") or "")
            construction = constructions.get(construction_id)
            construction_name = str(
                _safe_get(construction, "name", None)
                or _safe_get(construction, "display_name", None)
                or construction_id
                or "—"
            )
            previews.append(OpeningPreview(
                opening_type=str(_safe_get(item, "opening_type", "") or ""),
                profile_id=str(_safe_get(item, "profile_id", "") or ""),
                profile_name=str(_safe_get(item, "profile_name", "") or ""),
                width_m=float(_safe_get(item, "width_m", 0.0) or 0.0),
                height_m=float(_safe_get(item, "height_m", 0.0) or 0.0),
                quantity=int(_safe_get(item, "quantity", 1) or 1),
                construction_id=construction_id,
                construction_name=construction_name,
            ))
        return previews

    def _construction_id_for_opening(self, opening: OpeningPreview) -> str:
        if opening.opening_type == "WINDOW":
            return "DEV-WINDOW"

        if opening.opening_type == "DOOR":
            if opening.profile_id == "INTERNAL_DOOR":
                return "DEV-INT-DOOR"

            return "DEV-EXT-DOOR"

        return ""

    def _notify_opening_schedule_changed(
            self,
            ps: Any,
            room_id: str,
    ) -> None:
        """Invalidate committed Heat-Loss and refresh room observers."""
        ps.mark_heatloss_dirty()
        self._context.room_state_changed.emit(room_id)

    def _on_opening_requested(
            self,
            surface_id: str,
            opening: OpeningPreview,
    ) -> None:
        """
        Wall Wizard F1-B/F1-C.

        Writes room-level opening schedule items into ProjectState.
        Does not change HLP physics yet.
        """
        ps = _safe_get(self._context, "project_state", None)
        if ps is None:
            ps = _safe_get(self._context, "_project_state", None)

        if ps is None:
            return

        room_id = self._room_id_for_surface(ps, surface_id)
        if not room_id:
            return

        schedule = ps.get_or_create_room_opening_schedule(room_id)

        item = OpeningScheduleItemV1(
            opening_type=opening.opening_type,
            profile_id=opening.profile_id,
            profile_name=opening.profile_name,
            width_m=opening.width_m,
            height_m=opening.height_m,
            quantity=opening.quantity,
            construction_id=(
                opening.construction_id
                or self._construction_id_for_opening(opening)
            ),
        )

        schedule.add_item(item)
        self._notify_opening_schedule_changed(ps, room_id)

        print(
            "[WALL WIZARD] saved opening schedule item:",
            "room_id=", room_id,
            "profile=", opening.profile_name,
            "qty=", opening.quantity,
            "area=", f"{opening.area_m2:.2f}",
        )

    def _on_opening_remove_requested(
            self,
            surface_id: str,
            opening: OpeningPreview,
    ) -> None:
        """
        Wall Wizard F1-C.

        Remove a grouped opening schedule row from ProjectState.
        HLP physics remains untouched.
        """
        ps = _safe_get(self._context, "project_state", None)
        if ps is None:
            ps = _safe_get(self._context, "_project_state", None)

        if ps is None:
            return

        room_id = self._room_id_for_surface(ps, surface_id)
        if not room_id:
            return

        schedules = _safe_get(ps, "room_opening_schedules", {}) or {}
        schedule = schedules.get(room_id)

        if schedule is None:
            return

        schedule.remove_matching_items(
            profile_id=opening.profile_id,
            width_m=opening.width_m,
            height_m=opening.height_m,
            construction_id=opening.construction_id or None,
        )
        self._notify_opening_schedule_changed(ps, room_id)

        print(
            "[WALL WIZARD] removed opening schedule group:",
            "room_id=", room_id,
            "profile=", opening.profile_name,
        )

    def _on_openings_clear_requested(self, surface_id: str) -> None:
        """
        Wall Wizard F1-C.

        Clear all room-level opening schedule rows from ProjectState.
        HLP physics remains untouched.
        """
        ps = _safe_get(self._context, "project_state", None)
        if ps is None:
            ps = _safe_get(self._context, "_project_state", None)

        if ps is None:
            return

        room_id = self._room_id_for_surface(ps, surface_id)
        if not room_id:
            return

        schedules = _safe_get(ps, "room_opening_schedules", {}) or {}
        schedule = schedules.get(room_id)

        if schedule is None:
            return

        schedule.clear()
        self._notify_opening_schedule_changed(ps, room_id)

        print(
            "[WALL WIZARD] cleared opening schedule:",
            "room_id=", room_id,
        )