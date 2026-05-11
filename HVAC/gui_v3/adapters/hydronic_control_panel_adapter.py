# ======================================================================
# HVAC/gui_v3/adapters/hydronic_control_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.project.project_state import ProjectState
from HVAC.gui_v3.panels.hydronic_control_panel import HydronicControlPanel


# ======================================================================
# HydronicControlPanelAdapter
# ======================================================================

class HydronicControlPanelAdapter:
    """
    Hydronics H-E — Hydronic Control Panel adapter shell.

    Responsibilities
    ----------------
    • Project ProjectState rooms/emitters into the panel
    • Receive panel intent
    • For now, log intent only

    Explicitly forbidden
    --------------------
    • no hydronic calculation
    • no heat-loss calculation
    • no pipe sizing
    • no pump sizing
    • no pressure-loss calculation
    """

    def __init__(
        self,
        *,
        panel: HydronicControlPanel,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._project_state = project_state

        self._panel.add_emitter_requested.connect(
            self._on_add_emitter_requested
        )
        self._panel.update_emitter_requested.connect(
            self._on_update_emitter_requested
        )
        self._panel.remove_emitter_requested.connect(
            self._on_remove_emitter_requested
        )

        self.refresh()

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self._panel.set_rooms(self._room_options())
        self._panel.set_emitters(self._emitter_options())
        self._panel.set_status("Hydronic control shell ready.")

    def _room_options(self) -> list[tuple[str, str]]:
        rooms = getattr(self._project_state, "rooms", {}) or {}

        options: list[tuple[str, str]] = []

        for room_id, room in rooms.items():
            label = (
                getattr(room, "name", None)
                or getattr(room, "label", None)
                or room_id
            )
            options.append((room_id, label))

        return options

    def _emitter_options(self) -> list[tuple[str, str]]:
        emitters = getattr(self._project_state, "emitters", {}) or {}

        options: list[tuple[str, str]] = []

        for emitter_id, emitter in emitters.items():
            room_id = getattr(emitter, "room_id", "")
            emitter_type = getattr(emitter, "emitter_type", "emitter")
            name = getattr(emitter, "name", None) or emitter_id

            label = f"{name} ({emitter_type}, {room_id})"
            options.append((emitter_id, label))

        return options

    # ------------------------------------------------------------------
    # Intent handlers — shell only
    # ------------------------------------------------------------------

    def _on_add_emitter_requested(self, payload: dict) -> None:
        print("[HYDRONIC CONTROL] add emitter intent:", payload)

    def _on_update_emitter_requested(self, payload: dict) -> None:
        print("[HYDRONIC CONTROL] update emitter intent:", payload)

    def _on_remove_emitter_requested(self, emitter_id: str) -> None:
        print("[HYDRONIC CONTROL] remove emitter intent:", emitter_id)