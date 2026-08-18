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
from HVAC.heatloss.physics.room_paired_pipe_length_intent_v1 import (
    RoomPairedPipeLengthIntentV1,
)
from HVAC.hydronics.topology.topology_unassigned_room_inventory_v1 import (
    build_topology_unassigned_room_inventory_v1,
)
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
        self._panel.room_selected.connect(self._on_room_selected)
        self._panel.room_pipe_length_changed.connect(
            self._on_room_pipe_length_changed
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

        active_room_id = current_room_id or self._panel.current_room_id()
        self._project_room_pipework(active_room_id)

        self._panel.set_emitters(self._emitter_options())

        current_emitter_id = self._panel.current_emitter_id()

        if current_emitter_id:
            self._on_emitter_selected(current_emitter_id)
            self._panel.set_existing_emitter_available()
            self._panel.set_status("Hydronic control ready.")
            return

        self._panel.set_no_existing_emitter()

    # ------------------------------------------------------------------
    # H-S68-B2 — room-centric paired-pipe projection
    # ------------------------------------------------------------------

    def _room_pipework_applicability(
            self,
            room_id: str,
    ) -> tuple[bool, bool]:
        topology = getattr(self._project_state, "hydronic_topology", None)
        heat_source_room_id = str(
            getattr(topology, "heat_source_room_id", "") or ""
        )
        is_heat_source_room = bool(
            room_id and room_id == heat_source_room_id
        )
        is_terminal_room = False

        inventory = build_topology_unassigned_room_inventory_v1(
            self._project_state
        )
        if getattr(inventory, "ready", False):
            row = next(
                (
                    item
                    for item in getattr(inventory, "rows", ())
                    if str(getattr(item, "room_id", "") or "") == room_id
                ),
                None,
            )
            is_terminal_room = bool(
                getattr(row, "is_terminal", False)
            )
        else:
            # H-S68-B2C — blocked inventory fallback.  Use only exact
            # endpoints already stored on the accepted topology.  This is
            # read-only evidence: it neither migrates nor repairs topology.
            is_terminal_room = room_id in (
                self._stored_topology_terminal_room_ids(topology)
            )

        return is_heat_source_room, is_terminal_room

    @staticmethod
    def _stored_topology_terminal_room_ids(topology: Any) -> set[str]:
        terminal_room_ids: set[str] = set()

        def collect_route(owner: Any) -> None:
            route_room_ids = [
                str(value)
                for value in (
                    getattr(owner, "route_room_ids", []) or []
                )
                if str(value)
            ]
            if route_room_ids:
                terminal_room_ids.add(route_room_ids[-1])
            for child in getattr(owner, "sublegs", []) or []:
                collect_route(child)

        for leg in getattr(topology, "legs", []) or []:
            # Retain the legacy Leg endpoint during the current compatibility
            # period, then collect every stored Principal/Branch endpoint.
            legacy_route_room_ids = [
                str(value)
                for value in (
                    getattr(leg, "route_room_ids", []) or []
                )
                if str(value)
            ]
            if legacy_route_room_ids:
                terminal_room_ids.add(legacy_route_room_ids[-1])
            for subleg in getattr(leg, "sublegs", []) or []:
                collect_route(subleg)

        return terminal_room_ids

    def _project_room_pipework(self, room_id: str) -> None:
        room_id = str(room_id or "")
        intent = getattr(
            self._project_state,
            "hydronic_room_paired_pipe_length_intent",
            None,
        )
        entry = (
            intent.lengths_by_room_id.get(room_id)
            if isinstance(intent, RoomPairedPipeLengthIntentV1)
            else None
        )
        is_heat_source_room, is_terminal_room = (
            self._room_pipework_applicability(room_id)
            if room_id
            else (False, False)
        )
        before_enabled = bool(room_id) and not is_heat_source_room
        after_enabled = before_enabled and not is_terminal_room

        self._panel.set_room_pipework_projection(
            room_id=room_id,
            before_emitter_length_m=(
                getattr(entry, "before_emitter_length_m", None)
                if before_enabled
                else None
            ),
            after_emitter_length_m=(
                getattr(entry, "after_emitter_length_m", None)
                if after_enabled
                else None
            ),
            before_enabled=before_enabled,
            after_enabled=after_enabled,
            is_heat_source_room=is_heat_source_room,
            is_terminal_room=is_terminal_room,
        )

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

    def _on_room_selected(self, room_id: str) -> None:
        room_id = str(room_id or "")
        if not room_id:
            return
        context = getattr(self, "_context", None)
        set_current_room = getattr(context, "set_current_room", None)
        if callable(set_current_room):
            set_current_room(room_id)
        self.refresh()

    def _on_room_pipe_length_changed(
            self,
            room_id: str,
            position: str,
            length_m: object,
    ) -> None:
        room_id = str(room_id or "")
        position = str(position or "")
        rooms = getattr(self._project_state, "rooms", {}) or {}
        if room_id not in rooms or position not in {"before", "after"}:
            return

        is_heat_source_room, is_terminal_room = (
            self._room_pipework_applicability(room_id)
        )
        if is_heat_source_room:
            self._project_room_pipework(room_id)
            self._panel.set_status(
                "Room pipework is not entered for the Heat Source room."
            )
            return
        if position == "after" and is_terminal_room:
            self._project_room_pipework(room_id)
            self._panel.set_status(
                "After-emitter pipework is not entered for a terminal room."
            )
            return

        intent = getattr(
            self._project_state,
            "hydronic_room_paired_pipe_length_intent",
            None,
        )
        if not isinstance(intent, RoomPairedPipeLengthIntentV1):
            intent = RoomPairedPipeLengthIntentV1()

        current = intent.lengths_by_room_id.get(room_id)
        before_m = getattr(current, "before_emitter_length_m", None)
        after_m = getattr(current, "after_emitter_length_m", None)
        if position == "before":
            before_m = length_m
        else:
            after_m = length_m

        try:
            intent.set_room_lengths(
                room_id=room_id,
                before_emitter_length_m=before_m,
                after_emitter_length_m=after_m,
            )
        except (TypeError, ValueError) as exc:
            self._project_room_pipework(room_id)
            self._panel.set_status(f"Cannot save room pipework: {exc}")
            return

        self._project_state.hydronic_room_paired_pipe_length_intent = (
            intent if intent.lengths_by_room_id else None
        )
        mark_dirty = getattr(
            self._project_state,
            "mark_hydronics_dirty",
            None,
        )
        if callable(mark_dirty):
            mark_dirty()

        self._project_room_pipework(room_id)
        if self._refresh_all is not None:
            self._refresh_all()
        action = "Cleared" if length_m is None else "Saved"
        self._panel.set_status(
            f"{action} {position}-emitter room pipework."
        )

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