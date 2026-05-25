# ======================================================================
# HVAC/gui_v3/adapters/topology_arranger_panel_adapter.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC.gui_v3.panels.topology_arranger_panel import TopologyArrangerPanel
from HVAC.hydronics.topology.dev_hydronic_topology_builder_v1 import (
    DevHydronicTopologyBuilderV1,
)
from HVAC.hydronics.topology.topology_arranger_projection_v1 import (
    TopologyArrangerProjectionV1,
    build_topology_arranger_projection_v1,
)

from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.topology.hydronic_topology_editor_v1 import (
    HydronicTopologyEditorV1,
)
from HVAC.hydronics.indexing.hydronic_index_intent_v1 import (
    set_hydronic_index_room_v1,
)

# ======================================================================
# TopologyArrangerPanelAdapter
# ======================================================================

class TopologyArrangerPanelAdapter:
    """
    GUI v3 — Topology Arranger Panel Adapter.

    Responsibilities
    ----------------
    • Read ProjectState.hydronic_topology
    • Build TopologyArrangerProjectionV1
    • Push read-only route rows to the panel

    DEV behaviour
    -------------
    • If no hydronic_topology exists, seed a simple single-leg topology
      from the current ProjectState room list.

    Explicitly forbidden
    --------------------
    • No pipe sizing
    • No pressure-drop calculation
    • No proportioning calculation
    • No heat-loss calculation
    • No direct room identity mutation
    • No widget painting
    """

    def __init__(
        self,
        *,
        panel: TopologyArrangerPanel,
        context: GuiProjectContext,
        leg_id: str = "leg-001",
    ) -> None:
        self._panel = panel
        self._context = context
        self._leg_id = leg_id

        self._subscribe_if_present("room_state_changed", self.refresh)
        self._subscribe_if_present("current_room_changed", self.refresh)
        self._panel.move_up_requested.connect(self._on_move_up_requested)
        self._panel.move_down_requested.connect(self._on_move_down_requested)
        self._panel.make_terminal_requested.connect(self._on_make_terminal_requested)
        self._panel.set_index_requested.connect(self._on_set_index_requested)
        self.refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self, *args: Any, **kwargs: Any) -> None:
        """
        Refresh panel projection from current ProjectState.
        """

        project = self._context.project_state

        if project is None:
            self._panel.set_status("No project loaded")
            self._panel.set_rows([])
            return

        self._ensure_dev_topology(project)

        try:
            projection = build_topology_arranger_projection_v1(
                project,
                leg_id=self._leg_id,
            )
        except Exception as exc:
            self._panel.set_status(f"Topology Arranger unavailable: {exc}")
            self._panel.set_rows([])
            return

        self._apply_projection(projection)

    def set_leg_id(self, leg_id: str) -> None:
        """
        Select which leg the arranger projects.

        DEV v1 normally uses leg-001 only.
        """

        self._leg_id = str(leg_id or "leg-001")
        self.refresh()

    # ------------------------------------------------------------------
    # Projection application
    # ------------------------------------------------------------------

    def _apply_projection(
        self,
        projection: TopologyArrangerProjectionV1,
    ) -> None:
        rows: list[dict[str, Any]] = []

        for row in projection.rows:
            rows.append(
                {
                    "order": row.order,
                    "room_id": row.room_id,
                    "label": row.label,
                    "is_index": row.is_index,
                    "is_terminal": row.is_terminal,
                }
            )

        self._panel.set_title(
            f"Topology Arranger — {projection.leg_label}"
        )

        self._panel.set_status(
            f"Heat source: {projection.heat_source_room_id} | "
            f"Index: {projection.selected_index_room_id or '—'}"
        )

        self._panel.set_rows(rows)

    # ------------------------------------------------------------------
    # DEV topology seed
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_dev_topology(project: Any) -> None:
        """
        Ensure a DEV hydronic topology exists.

        Temporary bridge until the real Topology Arranger can create and edit
        topology explicitly.
        """

        if getattr(project, "hydronic_topology", None) is not None:
            return

        DevHydronicTopologyBuilderV1.install_single_leg_on_project(
            project,
            overwrite=False,
        )

    # ------------------------------------------------------------------
    # Signal subscription helper
    # ------------------------------------------------------------------

    def _subscribe_if_present(self, signal_name: str, callback) -> None:
        """
        Best-effort subscription to GuiProjectContext signals.
        """

        signal = getattr(self._context, signal_name, None)

        if signal is None:
            return

        connect = getattr(signal, "connect", None)
        if callable(connect):
            try:
                connect(lambda *args, **kwargs: callback())
            except TypeError:
                pass
            return

        subscribe = getattr(signal, "subscribe", None)
        if callable(subscribe):
            try:
                subscribe(lambda *args, **kwargs: callback())
            except TypeError:
                pass

    def _on_move_up_requested(self, room_id: str) -> None:
        project = self._context.project_state
        if project is None:
            return

        self._ensure_dev_topology(project)

        HydronicTopologyEditorV1.move_room_up(
            topology=project.hydronic_topology,
            leg_id=self._leg_id,
            room_id=room_id,
        )

        self._notify_changed()
        self.refresh()
        self._panel.select_room_id(room_id)

    def _on_move_down_requested(self, room_id: str) -> None:
        project = self._context.project_state
        if project is None:
            return

        self._ensure_dev_topology(project)

        HydronicTopologyEditorV1.move_room_down(
            topology=project.hydronic_topology,
            leg_id=self._leg_id,
            room_id=room_id,
        )

        self._notify_changed()
        self.refresh()
        self._panel.select_room_id(room_id)

    def _on_make_terminal_requested(self, room_id: str) -> None:
        self._apply_index_room_change(
            room_id=room_id,
            move_to_terminal=True,
        )

    def _on_set_index_requested(self, room_id: str) -> None:
        self._apply_index_room_change(
            room_id=room_id,
            move_to_terminal=False,
        )

    def _apply_index_room_change(
            self,
            *,
            room_id: str,
            move_to_terminal: bool,
    ) -> None:
        project = self._context.project_state
        if project is None:
            return

        room_id = str(room_id or "").strip()
        if not room_id:
            return

        self._ensure_dev_topology(project)

        result = set_hydronic_index_room_v1(
            project,
            room_id,
            leg_id=self._leg_id,
            move_to_terminal=move_to_terminal,
        )

        print(
            "[TOPOLOGY ARRANGER INDEX]",
            "room_id=",
            result.index_room_id,
            "emitter_id=",
            result.index_emitter_id,
            "move_to_terminal=",
            move_to_terminal,
            "status=",
            result.status,
        )

        self._notify_changed(room_id)
        self.refresh()
        self._panel.select_room_id(room_id)

    @staticmethod
    def _ensure_basic_hydronic_intent(project: Any) -> None:
        if getattr(project, "basic_hydronic_sizing_intent", None) is not None:
            return

        project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1()

    def _notify_changed(self, room_id: str | None = None) -> None:
        signal = getattr(self._context, "room_state_changed", None)

        if signal is None:
            return

        for emitted_room_id in (room_id or "", ""):
            try:
                signal.emit(str(emitted_room_id))
            except Exception:
                pass