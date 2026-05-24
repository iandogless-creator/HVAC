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