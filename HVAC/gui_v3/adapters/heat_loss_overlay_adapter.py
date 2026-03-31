# ======================================================================
# HVAC/gui_v3/adapters/heat_loss_overlay_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Optional, Any

from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QLabel, QDoubleSpinBox, QWidget

from HVAC.gui_v3.common.edit_context import EditContext
from HVAC.gui_v3.common.overlay_controller import OverlayController
from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3


class HeatLossOverlayAdapter(QObject):
    """
    Bridges HeatLossPanelV3 user edit intent to overlay editors.

    Authority
    ---------
    • Reads current room selection from GuiProjectContext
    • Opens overlay editors through OverlayController
    • Commits editor values into ProjectState
    • Triggers refresh callback after commit
    • Does NOT calculate physics
    • Does NOT directly populate HLP display rows

    Notes
    -----
    This adapter exists so HLP remains a pure projection/view panel.
    HLP emits intent only; this adapter interprets that intent.
    """

    def __init__(
        self,
        *,
        panel: HeatLossPanelV3,
        context: GuiProjectContext,
        overlay_controller: OverlayController,
        refresh_all_callback,
        topology_resolve_callback=None,
    ) -> None:
        super().__init__(panel)

        self._panel = panel
        self._context = context
        self._overlay = overlay_controller
        self._refresh_all_callback = refresh_all_callback
        self._topology_resolve_callback = topology_resolve_callback

        self._bind_panel_signals()

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------
    def _bind_panel_signals(self) -> None:
        """
        Preferred pattern:
        HLP should expose intent signals such as:
            • worksheet_cell_edit_requested(row, col)
            • ach_edit_requested()
            • geometry_edit_requested()

        If you do not have those yet, add them to the panel.
        """
        if hasattr(self._panel, "worksheet_cell_edit_requested"):
            self._panel.worksheet_cell_edit_requested.connect(
                self._on_worksheet_cell_edit_requested
            )

        if hasattr(self._panel, "ach_edit_requested"):
            self._panel.ach_edit_requested.connect(self._on_ach_edit_requested)

        if hasattr(self._panel, "geometry_edit_requested"):
            self._panel.geometry_edit_requested.connect(
                self._on_geometry_edit_requested
            )

    # ------------------------------------------------------------------
    # Intent handlers
    # ------------------------------------------------------------------
    def _on_worksheet_cell_edit_requested(self, row: int, column: int) -> None:
        room = self._get_current_room()
        if room is None:
            return

        ctx = EditContext(
            kind="cell",
            room_id=self._get_room_id(room),
            row=row,
            column=column,
            field=self._resolve_field_for_cell(row, column),
        )
        self._activate(ctx)

    def _on_ach_edit_requested(self) -> None:
        room = self._get_current_room()
        if room is None:
            return

        ctx = EditContext(
            kind="ach",
            room_id=self._get_room_id(room),
            field="air_changes_per_hour",
        )
        self._activate(ctx)

    def _on_geometry_edit_requested(self) -> None:
        room = self._get_current_room()
        if room is None:
            return

        ctx = EditContext(
            kind="geometry",
            room_id=self._get_room_id(room),
            field="geometry",
        )
        self._activate(ctx)

    # ------------------------------------------------------------------
    # Overlay activation
    # ------------------------------------------------------------------
    def _activate(self, ctx: EditContext) -> None:
        self._overlay.activate(ctx)
        editor = self._overlay.current_editor()
        if editor is None:
            return

        self._prime_editor(editor, ctx)
        self._bind_editor_commit(editor, ctx)

    # ------------------------------------------------------------------
    # Editor priming
    # ------------------------------------------------------------------
    def _prime_editor(self, editor: QWidget, ctx: EditContext) -> None:
        room = self._get_room_by_id(ctx.room_id)
        if room is None:
            return

        if ctx.kind == "ach":
            if isinstance(editor, QDoubleSpinBox):
                value = self._safe_float(
                    getattr(room, "air_changes_per_hour", None),
                    default=0.50,
                )
                editor.setValue(value)
                editor.selectAll()

        elif ctx.kind == "geometry":
            # Expect GeometryMiniPanel-like API if present
            geometry = getattr(room, "geometry", None)
            if geometry is None:
                return

            if hasattr(editor, "set_room_header"):
                room_name = getattr(room, "name", ctx.room_id)
                editor.set_room_header(room_name)

            if hasattr(editor, "set_values"):
                editor.set_values(
                    length_m=self._safe_float(getattr(geometry, "length_m", None)),
                    width_m=self._safe_float(getattr(geometry, "width_m", None)),
                    height_m=self._safe_float(getattr(geometry, "height_m", None)),
                )

        elif ctx.kind == "cell":
            if isinstance(editor, QDoubleSpinBox):
                value = self._resolve_cell_field_value(room=room, field=ctx.field)
                editor.setValue(self._safe_float(value))
                editor.selectAll()

    # ------------------------------------------------------------------
    # Commit wiring
    # ------------------------------------------------------------------
    def _bind_editor_commit(self, editor: QWidget, ctx: EditContext) -> None:
        if ctx.kind == "geometry":
            if hasattr(editor, "geometry_committed"):
                editor.geometry_committed.connect(
                    lambda values, x=ctx: self._commit_geometry(x, values)
                )
            return

        if isinstance(editor, QDoubleSpinBox):
            editor.editingFinished.connect(
                lambda e=editor, x=ctx: self._commit_spin_value(x, e.value())
            )
            editor.installEventFilter(self)

    # ------------------------------------------------------------------
    # Qt event filter
    # ------------------------------------------------------------------
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QDoubleSpinBox):
            if event.type() == QEvent.FocusOut:
                # allow editingFinished to handle commit
                pass
        return super().eventFilter(watched, event)

    # ------------------------------------------------------------------
    # Commit implementations
    # ------------------------------------------------------------------
    def _commit_spin_value(self, ctx: EditContext, value: float) -> None:
        room = self._get_room_by_id(ctx.room_id)
        if room is None:
            return

        if ctx.kind == "ach":
            setattr(room, "air_changes_per_hour", float(value))
            self._after_model_write(resolve_topology=False)
            return

        if ctx.kind == "cell":
            self._commit_cell_value(room=room, field=ctx.field, value=value)
            self._after_model_write(resolve_topology=False)
            return

    def _commit_geometry(self, ctx: EditContext, values: dict[str, Any]) -> None:
        room = self._get_room_by_id(ctx.room_id)
        if room is None:
            return

        geometry = getattr(room, "geometry", None)
        if geometry is None:
            return

        if "length_m" in values:
            geometry.length_m = float(values["length_m"])
        if "width_m" in values:
            geometry.width_m = float(values["width_m"])
        if "height_m" in values:
            geometry.height_m = float(values["height_m"])

        self._after_model_write(resolve_topology=True)

    # ------------------------------------------------------------------
    # Post-write refresh
    # ------------------------------------------------------------------
    def _after_model_write(self, *, resolve_topology: bool) -> None:
        if resolve_topology and self._topology_resolve_callback is not None:
            self._topology_resolve_callback()

        self._refresh_all_callback()
        self._overlay.clear()

    # ------------------------------------------------------------------
    # Cell field resolution
    # ------------------------------------------------------------------
    def _resolve_field_for_cell(self, row: int, column: int) -> Optional[str]:
        """
        Keep this conservative and explicit.

        Recommended:
        HLP should expose semantic row metadata so this adapter does NOT
        rely on visual row numbers long-term.

        For now:
            column 1 -> area_m2
            column 2 -> u_value_W_m2K
            column 3 -> delta_t_K (usually read-only; return None if locked)
        """
        if column == 1:
            return "area_m2"
        if column == 2:
            return "u_value_W_m2K"
        if column == 3:
            return None
        return None

    def _resolve_cell_field_value(self, *, room: Any, field: Optional[str]) -> float:
        if field is None:
            return 0.0

        worksheet_row = self._get_selected_surface_or_first_surface(room)
        if worksheet_row is None:
            return 0.0

        return self._safe_float(getattr(worksheet_row, field, 0.0))

    def _commit_cell_value(self, *, room: Any, field: Optional[str], value: float) -> None:
        if field is None:
            return

        surface = self._get_selected_surface_or_first_surface(room)
        if surface is None:
            return

        setattr(surface, field, float(value))

    # ------------------------------------------------------------------
    # Model helpers
    # ------------------------------------------------------------------
    def _get_current_room(self) -> Optional[Any]:
        if hasattr(self._context, "current_room") and self._context.current_room is not None:
            return self._context.current_room

        if hasattr(self._context, "current_room_id"):
            room_id = self._context.current_room_id
            if room_id:
                return self._get_room_by_id(room_id)

        return None

    def _get_room_by_id(self, room_id: str) -> Optional[Any]:
        project = getattr(self._context, "project_state", None)
        if project is None:
            return None

        rooms = getattr(project, "rooms", None)
        if rooms is None:
            return None

        if isinstance(rooms, dict):
            return rooms.get(room_id)

        return None

    def _get_room_id(self, room: Any) -> str:
        return str(getattr(room, "room_id", getattr(room, "id", "")))

    def _get_selected_surface_or_first_surface(self, room: Any) -> Optional[Any]:
        surfaces = getattr(room, "fabric_surfaces", None)
        if not surfaces:
            return None

        if isinstance(surfaces, list):
            return surfaces[0]

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)