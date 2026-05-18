# ======================================================================
# HVAC/gui_v3/adapters/hydronic_control_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.project.project_state import ProjectState
from HVAC.gui_v3.panels.hydronic_control_panel import HydronicControlPanel
from HVAC.hydronics.emitter_v1 import EmitterV1
from HVAC.hydronics.adapters.emitter_candidate_builder_v1 import (
    EmitterCandidateBuilderV1,
)
from HVAC.core.room_identity import room_short_label
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
            context: Any | None = None,
            refresh_all: Any | None = None,
    ) -> None:
        self._panel = panel
        self._project_state = project_state
        self._context = context
        self._panel.add_emitter_requested.connect(
            self._on_add_emitter_requested
        )
        self._panel.update_emitter_requested.connect(
            self._on_update_emitter_requested
        )
        self._panel.remove_emitter_requested.connect(
            self._on_remove_emitter_requested
        )
        self._panel.emitter_selected.connect(
            self._on_emitter_selected
        )
        self._default_emitters_bootstrapped = False
        self._refresh_all = refresh_all
        self.refresh()

    def set_project_state(self, project_state: ProjectState) -> None:
        """
        Rebind adapter to the current ProjectState.

        Required when a project is loaded or DEV mode swaps ProjectState.
        """
        if project_state is self._project_state:
            return

        self._project_state = project_state
        self._default_emitters_bootstrapped = False

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Hydronic Control Panel refresh.

        H-O emitter authority rule:
        • ProjectState.emitters is the authority
        • Existing emitters are projected into the control panel
        • Missing emitters are shown as missing; they are not created here
        • No default emitter creation during refresh/load
        • No hydronic calculation
        • No pipe sizing
        """

        self._panel.set_rooms(self._room_options())

        current_room_id = self._current_room_id()
        if current_room_id:
            self._panel.set_active_room(current_room_id)

        self._panel.set_emitters(self._emitter_options())

        current_emitter_id = self._panel.current_emitter_id()

        if current_emitter_id:
            self._on_emitter_selected(current_emitter_id)
            self._panel.set_existing_emitter_available()
            self._panel.set_status("Hydronic control ready.")
            return

        self._panel.set_no_existing_emitter()

    def _room_options(self) -> list[tuple[str, str]]:
        rooms = getattr(self._project_state, "rooms", {}) or {}

        options: list[tuple[str, str]] = []

        for room_id, room in rooms.items():
            options.append((room_id, room_short_label(room_id, room)))

        return options

    def _room_name_for_display(self, room_id: str) -> str:
        rooms = getattr(self._project_state, "rooms", {}) or {}
        room = rooms.get(room_id)
        if room is None:
            return str(room_id)
        return room_short_label(room_id, room)

    def _emitter_options(self) -> list[tuple[str, str]]:
        """
        Existing emitter options for the currently selected room only.

        Hydronic Control is a room/emitter editor, so its emitter selector
        should follow the active room rather than listing unrelated emitters.
        """
        emitters = getattr(self._project_state, "emitters", {}) or {}

        active_room_id = self._panel.current_room_id()
        if not active_room_id:
            active_room_id = self._current_room_id()

        options: list[tuple[str, str]] = []

        for emitter_id, emitter in emitters.items():
            room_id = str(getattr(emitter, "room_id", "") or "")

            if active_room_id and room_id != active_room_id:
                continue

            emitter_type = getattr(emitter, "emitter_type", "emitter")
            name = getattr(emitter, "name", None) or emitter_id

            output_W = getattr(emitter, "design_output_W", None)
            output_label = self._fmt_output_W(output_W)

            room_label = self._room_name_for_display(room_id) if room_id else "room"

            label = f"{name} — {output_label} ({emitter_type}, {room_label})"

            options.append((emitter_id, label))

        return options

    def _on_emitter_selected(self, emitter_id: str) -> None:
        emitter_id = str(emitter_id or "")

        if not emitter_id:
            self._panel.set_no_existing_emitter()
            return

        emitters = getattr(self._project_state, "emitters", {}) or {}
        emitter = emitters.get(emitter_id)

        if emitter is None:
            self._panel.set_no_existing_emitter()
            return

        self._panel.set_emitter_editor_values(
            emitter_type=getattr(emitter, "emitter_type", "radiator"),
            design_output_W=getattr(emitter, "design_output_W", None),
            flow_temp_C=getattr(emitter, "flow_temp_C", None),
            return_temp_C=getattr(emitter, "return_temp_C", None),
        )

        self._panel.set_existing_emitter_available()

    def _optional_positive_float(self, value: Any) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None

        if result <= 0.0:
            return None

        return result

    def _make_emitter_id(
        self,
        *,
        room_id: str,
        emitter_type: str,
    ) -> str:
        safe_type = emitter_type.replace(" ", "_").replace("-", "_")
        base = f"emitter-{safe_type}-{room_id}"

        emitters = getattr(self._project_state, "emitters", {}) or {}

        index = 1
        while True:
            candidate = f"{base}-{index:03d}"
            if candidate not in emitters:
                return candidate

            index += 1

    def _current_room_id(self) -> str:
        context = getattr(self, "_context", None)
        if context is not None:
            value = getattr(context, "current_room_id", None)
            if value:
                return str(value)

        return ""

    def _display_emitter_type(self, emitter_type: str) -> str:
        return emitter_type.replace("_", " ").title()

    @staticmethod
    def _fmt_output_W(value) -> str:
        if value is None:
            return "output unset"

        try:
            return f"{float(value):.1f} W"
        except (TypeError, ValueError):
            return "output unset"

    @staticmethod
    def _fmt_output_W(value) -> str:
        if value is None:
            return "output unset"

        try:
            return f"{float(value):.1f} W"
        except (TypeError, ValueError):
            return "output unset"

    # ------------------------------------------------------------------
    # Intent handlers — shell only
    # ------------------------------------------------------------------

    def _on_add_emitter_requested(self, payload: dict) -> None:
        """
        Hydronics H-F.

        Create one or more EmitterV1 objects from panel intent.

        Authority
        ---------
        • Adapter receives intent
        • ProjectState.emitters owns the result
        • No hydronic calculation
        • No pipe sizing
        """
        room_id = str(payload.get("room_id") or "")
        if not room_id:
            self._panel.set_status("Cannot add emitter: no room selected.")
            return

        emitter_type = str(payload.get("emitter_type") or "radiator")
        quantity = int(payload.get("quantity") or 1)

        design_output_W = self._optional_positive_float(
            payload.get("design_output_W")
        )
        flow_temp_C = self._optional_positive_float(
            payload.get("flow_temp_C")
        )
        return_temp_C = self._optional_positive_float(
            payload.get("return_temp_C")
        )

        room_name = self._room_name_for_display(room_id)

        created_ids: list[str] = []

        for _ in range(quantity):
            emitter_id = self._make_emitter_id(
                room_id=room_id,
                emitter_type=emitter_type,
            )

            self._project_state.emitters[emitter_id] = EmitterV1(
                emitter_id=emitter_id,
                room_id=room_id,
                name=f"{self._display_emitter_type(emitter_type)} — {room_name}",
                emitter_type=emitter_type,
                design_output_W=design_output_W,
                flow_temp_C=flow_temp_C,
                return_temp_C=return_temp_C,
                room_temp_C=None,
                notes="Created from Hydronic Control Panel",
            )

            created_ids.append(emitter_id)

        print(
            "[HYDRONIC CONTROL] created emitter(s):",
            created_ids,
        )

        self.refresh()

        if self._refresh_all is not None:
            self._refresh_all()

        self._panel.set_status(
            f"Added {len(created_ids)} emitter(s) to {room_name}."
        )

    def _on_update_emitter_requested(self, payload: dict) -> None:
        """
        Hydronics H-H.

        Update selected EmitterV1 fields from panel intent.

        Authority
        ---------
        • Adapter receives intent
        • ProjectState.emitters owns the updated emitter
        • No hydronic calculation
        • No pipe sizing
        • No heat-loss calculation
        """
        emitter_id = str(payload.get("emitter_id") or "")

        if not emitter_id:
            self._panel.set_status("Cannot update emitter: none selected.")
            return

        emitters = getattr(self._project_state, "emitters", {}) or {}
        emitter = emitters.get(emitter_id)

        if emitter is None:
            self._panel.set_status(
                f"Cannot update emitter: {emitter_id} not found."
            )
            return

        room_id = str(payload.get("room_id") or getattr(emitter, "room_id", "") or "")
        emitter_type = str(payload.get("emitter_type") or getattr(emitter, "emitter_type", "radiator"))

        design_output_W = self._optional_positive_float(
            payload.get("design_output_W")
        )
        flow_temp_C = self._optional_positive_float(
            payload.get("flow_temp_C")
        )
        return_temp_C = self._optional_positive_float(
            payload.get("return_temp_C")
        )

        room_name = self._room_name_for_display(room_id)

        emitter.room_id = room_id
        emitter.emitter_type = emitter_type
        emitter.design_output_W = design_output_W
        emitter.flow_temp_C = flow_temp_C
        emitter.return_temp_C = return_temp_C
        emitter.name = f"{self._display_emitter_type(emitter_type)} — {room_name}"

        print(
            "[HYDRONIC CONTROL] updated emitter:",
            emitter_id,
            {
                "room_id": room_id,
                "emitter_type": emitter_type,
                "design_output_W": design_output_W,
                "flow_temp_C": flow_temp_C,
                "return_temp_C": return_temp_C,
            },
        )

        self.refresh()

        if self._refresh_all is not None:
            self._refresh_all()

        self._panel.set_status(
            f"Updated {emitter.name}."
        )

    def _on_remove_emitter_requested(self, emitter_id: str) -> None:
        """
        Hydronics H-G.

        Remove selected EmitterV1 from ProjectState.emitters.

        Authority
        ---------
        • Adapter receives intent
        • ProjectState.emitters owns the result
        • No hydronic calculation
        • No pipe sizing
        """
        emitter_id = str(emitter_id or "")

        if not emitter_id:
            self._panel.set_status("Cannot remove emitter: none selected.")
            return

        emitters = getattr(self._project_state, "emitters", {}) or {}

        emitter = emitters.get(emitter_id)
        if emitter is None:
            self._panel.set_status(
                f"Cannot remove emitter: {emitter_id} not found."
            )
            return

        room_id = getattr(emitter, "room_id", "")
        emitter_name = getattr(emitter, "name", None) or emitter_id

        del emitters[emitter_id]

        print(
            "[HYDRONIC CONTROL] removed emitter:",
            emitter_id,
        )

        self.refresh()

        if self._refresh_all is not None:
            self._refresh_all()

        self._panel.set_status(
            f"Removed {emitter_name} from {room_id or 'room'}."
        )