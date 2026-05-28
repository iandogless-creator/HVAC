# ======================================================================
# HVAC/gui_v3/adapters/basic_hydronics_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.basic_hydronics_panel import BasicHydronicsPanel
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.core.room_identity import room_short_label
from HVAC.hydronics.indexing.hydronic_index_intent_v1 import (
    apply_basic_hydronic_sizing_payload_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)

# ======================================================================
# BasicHydronicsPanelAdapter
# ======================================================================

class BasicHydronicsPanelAdapter:
    """
    GUI v3 — Basic Hydronics Panel Adapter

    Role
    ----
    Mediates between BasicHydronicsPanel user intent and ProjectState.

    Authority
    ---------
    • Reads ProjectState
    • Writes ProjectState.basic_hydronic_sizing_intent from panel intent
    • Does not perform pipe sizing
    • Does not perform pressure-loss calculation
    • Does not call Colebrook or Darcy-Weisbach
    • Does not mutate heat-loss state

    Panel remains an intent emitter only.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        panel: BasicHydronicsPanel,
        context: GuiProjectContext,
    ) -> None:
        self._panel = panel
        self._context = context

        self._panel.intent_committed.connect(self._on_intent_committed)

        self._last_project_identity: int | None = None
        self._has_primed_project: bool = False

        # Best-effort subscriptions.
        self._subscribe_if_present("room_state_changed", self.refresh)
        self._subscribe_if_present("current_room_changed", self.refresh)

        self.refresh()

    # ==================================================================
    # Refresh
    # ==================================================================

    def refresh(self, *args, **kwargs) -> None:
        project = self._context.project_state
        if project is None:
            self._panel.set_room_options([])
            self._panel.set_emitter_options([])
            self._panel.prime_intent(None)
            return

        intent = getattr(project, "basic_hydronic_sizing_intent", None)

        # --------------------------------------------------------------
        # Rooms
        # --------------------------------------------------------------
        room_options: list[tuple[str, str]] = []

        for room_id, room in (project.rooms or {}).items():
            display_name = self._room_display_name(room_id, room)
            room_options.append((room_id, display_name))

        project_identity = id(project)
        project_changed = project_identity != self._last_project_identity

        if project_changed:
            self._last_project_identity = project_identity
            self._has_primed_project = False

        selected_room_id = (
            intent.index_room_id
            if intent is not None
            else self._panel.current_index_room_id()
        )

        if not selected_room_id and not self._has_primed_project:
            selected_room_id = self._current_room_id()

        self._panel.set_room_options(
            room_options,
            selected_room_id=selected_room_id,
        )

        # --------------------------------------------------------------
        # Emitters
        # --------------------------------------------------------------
        emitter_options: list[tuple[str, str]] = []

        for emitter_id, emitter in (project.emitters or {}).items():
            display_name = self._emitter_display_name(
                emitter_id=emitter_id,
                emitter=emitter,
                project=project,
            )
            emitter_options.append((emitter_id, display_name))

        selected_emitter_id = (
            intent.index_emitter_id
            if intent is not None
            else self._panel.current_index_emitter_id()
        )

        self._panel.set_emitter_options(
            emitter_options,
            selected_emitter_id=selected_emitter_id,
        )
        self._refresh_basic_ps_sections(project)
        # --------------------------------------------------------------
        # Intent projection
        # --------------------------------------------------------------
        if intent is not None:
            self._panel.prime_intent(intent.to_dict())
            self._has_primed_project = True
        elif not self._has_primed_project:
            self._panel.prime_intent(None)
            self._has_primed_project = True

    def _refresh_basic_ps_sections(self, project) -> None:
        """
        Refresh read-only Basic PS topology section rows.

        H-S8-J:
        Calls the composed read-only Basic PS projection path:

        topology sections
        -> first-pass Haaland pipe sizing
        -> section Δp preview
        -> route Δp ranking

        The panel still displays the existing Basic PS section table only.
        """

        if not hasattr(self._panel, "set_basic_ps_sections"):
            return

        try:
            basic_ps_projection = build_basic_ps_readonly_projection_v1(
                project,
                leg_id="leg-001",
            )

        except Exception as exc:
            print("[BASIC PS SECTIONS ERROR]", repr(exc))
            self._panel.set_basic_ps_sections([])
            return
        if hasattr(self._panel, "set_pressure_preview_rows"):
            pressure_rows: list[dict] = []

            for preview_row in basic_ps_projection.pressure_preview_projection.rows:
                pressure_rows.append(
                    {
                        "order": preview_row.order,
                        "from_label": preview_row.from_label,
                        "to_room_label": preview_row.to_room_label,
                        "pressure_gradient_Pa_per_m": preview_row.pressure_gradient_Pa_per_m,
                        "section_length_m": preview_row.section_length_m,
                        "section_pressure_drop_Pa": preview_row.section_pressure_drop_Pa,
                        "status": preview_row.status,
                    }
                )

            self._panel.set_pressure_preview_rows(pressure_rows)
        rows: list[dict] = []
        if hasattr(self._panel, "set_candidate_ranking_rows"):
            ranking_rows: list[dict] = []

            for ranking_row in basic_ps_projection.route_ranking_projection.rows:
                ranking_rows.append(
                    {
                        "rank": ranking_row.rank,
                        "route_label": ranking_row.route_label,
                        "leg_id": ranking_row.leg_id,
                        "subleg_id": ranking_row.subleg_id,
                        "total_length_m": ranking_row.total_length_m,
                        "total_pressure_drop_Pa": ranking_row.total_pressure_drop_Pa,
                        "is_controlling_index": ranking_row.is_controlling_index,
                        "status": ranking_row.status,
                    }
                )

            self._panel.set_candidate_ranking_rows(ranking_rows)
        for result in basic_ps_projection.pipe_sizing_projection.results:
            rows.append(
                {
                    "order": result.order,
                    "from_label": result.from_label,
                    "to_room_label": result.to_room_label,
                    "carried_heat_W": result.carried_heat_W,
                    "carried_flow_kg_s": result.carried_flow_kg_s,
                    "pipe_size_label": result.pipe_size_label,
                    "velocity_m_s": result.velocity_m_s,
                    "pressure_gradient_Pa_per_m": result.pressure_gradient_Pa_per_m,
                    "is_index_room": result.is_index_room,
                    "is_terminal": result.is_terminal,
                }
            )

        self._panel.set_basic_ps_sections(rows)

    # ==================================================================
    # Intent commit
    # ==================================================================
    def _on_intent_committed(self, payload: dict) -> None:
        project = self._context.project_state
        if project is None:
            return

        apply_basic_hydronic_sizing_payload_v1(
            project,
            payload,
            leg_id="leg-001",
            update_topology_index=True,
            move_to_terminal=False,
        )

        # Hydronics assumptions changed. Existing calculated hydronics
        # output should no longer be considered authoritative.
        if hasattr(project, "hydronics_valid"):
            project.hydronics_valid = False

        # Notify the rest of GUI v3 if the context supports it.
        self._notify_project_changed()
        self.refresh()

    # ==================================================================
    # Display helpers
    # ==================================================================
    @staticmethod
    def _room_display_name(room_id: str, room: object) -> str:
        return room_short_label(room_id, room)

    def _emitter_display_name(
            self,
            *,
            emitter_id: str,
            emitter: object,
            project,
    ) -> str:
        name = getattr(emitter, "name", None) or emitter_id
        emitter_type = getattr(emitter, "emitter_type", None) or "emitter"
        room_id = getattr(emitter, "room_id", None)

        output_W = getattr(emitter, "design_output_W", None)
        output_label = self._fmt_output_W(output_W)

        if room_id:
            room = project.rooms.get(room_id)
            if room is not None:
                room_label = self._room_display_name(room_id, room)
                return f"{name} — {output_label} ({emitter_type}, {room_label})"

        return f"{name} — {output_label} ({emitter_type})"

    @staticmethod
    def _fmt_output_W(value) -> str:
        if value is None:
            return "output unset"

        try:
            return f"{float(value):.1f} W"
        except (TypeError, ValueError):
            return "output unset"

    def _current_room_id(self) -> Optional[str]:
        for attr in (
            "current_room_id",
            "selected_room_id",
            "_current_room_id",
        ):
            value = getattr(self._context, attr, None)
            if isinstance(value, str) and value:
                return value

        return None

    # ==================================================================
    # Context integration helpers
    # ==================================================================
    def _subscribe_if_present(self, signal_name: str, callback) -> None:
        signal = getattr(self._context, signal_name, None)
        if signal is None:
            return

        try:
            signal.connect(callback)
        except AttributeError:
            # Some context APIs use subscribe_* methods rather than Qt signals.
            subscribe_name = f"subscribe_{signal_name}"
            subscribe = getattr(self._context, subscribe_name, None)
            if callable(subscribe):
                subscribe(callback)

    def _notify_project_changed(self) -> None:
        """
        Best-effort GUI notification.

        Avoids coupling this adapter to one exact GuiProjectContext API shape.
        """
        for method_name in (
            "notify_project_state_changed",
            "notify_room_state_changed",
            "emit_room_state_changed",
        ):
            method = getattr(self._context, method_name, None)
            if callable(method):
                try:
                    method()
                    return
                except TypeError:
                    pass

        signal = getattr(self._context, "room_state_changed", None)
        if signal is not None:
            try:
                signal.emit("")
            except Exception:
                pass