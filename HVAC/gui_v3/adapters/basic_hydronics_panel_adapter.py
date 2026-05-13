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

        # Best-effort subscriptions.
        #
        # Context signal APIs have evolved during GUI v3, so keep this
        # defensive rather than making this adapter brittle.
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

        selected_room_id = (
            intent.index_room_id
            if intent is not None
            else self._current_room_id()
        )

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
            else None
        )

        self._panel.set_emitter_options(
            emitter_options,
            selected_emitter_id=selected_emitter_id,
        )

        # --------------------------------------------------------------
        # Intent projection
        # --------------------------------------------------------------
        self._panel.prime_intent(
            intent.to_dict()
            if intent is not None
            else None
        )

    # ==================================================================
    # Intent commit
    # ==================================================================
    def _on_intent_committed(self, payload: dict) -> None:
        project = self._context.project_state
        if project is None:
            return

        project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1(
            basis_mode=str(payload.get("basis_mode") or "INDEX_LENGTH"),
            index_room_id=payload.get("index_room_id"),
            index_emitter_id=payload.get("index_emitter_id"),
            total_index_length_m=payload.get("total_index_length_m"),
            nominal_pressure_gradient_Pa_per_m=payload.get(
                "nominal_pressure_gradient_Pa_per_m"
            ),
            length_source=str(payload.get("length_source") or "unset"),
            pressure_gradient_source=str(
                payload.get("pressure_gradient_source") or "unset"
            ),
            notes=str(payload.get("notes") or ""),
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
        name = getattr(room, "name", None)
        if name:
            return str(name)

        display_name = getattr(room, "display_name", None)
        if display_name:
            return str(display_name)

        return str(room_id)

    @staticmethod
    def _emitter_display_name(
            *,
            emitter_id: str,
            emitter: object,
            project: object,
    ) -> str:
        emitter_name = getattr(emitter, "name", None) or "Emitter"
        emitter_type = getattr(emitter, "emitter_type", None) or "emitter"
        room_id = getattr(emitter, "room_id", None)

        room_name = None
        if room_id and hasattr(project, "rooms"):
            room = project.rooms.get(room_id)
            if room is not None:
                room_name = getattr(room, "name", None) or getattr(
                    room,
                    "display_name",
                    None,
                )

        # Avoid labels like:
        #   Emitter — Kitchen (DEV) — Kitchen (DEV)
        if room_name and str(room_name) not in str(emitter_name):
            return f"{emitter_name} — {room_name}"

        if emitter_type:
            return f"{emitter_name} ({emitter_type})"

        return str(emitter_id)

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
                signal.emit()
            except Exception:
                pass