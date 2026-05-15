# ======================================================================
# HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py
# ======================================================================

"""
HVACgooee — GUI v3
Hydronics Schematic Panel Adapter — Phase B → E

Reads ProjectState and translates hydronics topology into a
read-only schematic DTO.

• Topology only
• No physics
• No authority
• Phase B: empty-state safe
• Phase E adds visual hints (shape, orientation)
"""

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.gui_v3.panels.hydronics_schematic_panel import HydronicsSchematicPanel
from HVAC.gui_v3.schematic.dto import (
    HydronicsSchematicDTO,
    SchematicNodeDTO,
    SchematicEdgeDTO,
    SchematicLabelDTO,
    EdgeDirection,
    EdgeStyle,
    NodeRole,
)
from HVAC.hydronics.adapters.room_emitter_demand_adapter_v1 import (
    RoomEmitterDemandAdapterV1,
)
from HVAC.hydronics.builders.hydronic_skeleton_from_project_state_v1 import (
    build_hydronic_skeleton_from_project_state_v1,
)
from HVAC.hydronics.pipes.pipe_run_intent_builder_v1 import (
    build_pipe_run_intents_from_skeleton_v1,
)
from HVAC.core.room_identity import room_short_label

class HydronicsSchematicPanelAdapter:
    """
    Adapter responsibilities:
    • Read ProjectState (read-only)
    • Extract hydronic topology snapshot
    • Build schematic DTO
    • Push DTO into panel

    Phase B rule:
    • Missing snapshot is VALID
    """

    def __init__(
        self,
        *,
        panel: HydronicsSchematicPanel,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._project_state = project_state

        # Phase B: safe initial refresh
        self.refresh()

    def set_project_state(self, project_state: ProjectState) -> None:
        """
        Rebind adapter to the current ProjectState.

        Required when a project is loaded or DEV mode swaps ProjectState.
        """
        self._project_state = project_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Phase H-D/H-F refresh.

        • Demand rows are observer-only
        • Empty hydronics topology remains a valid schematic empty state
        • No emitter creation
        • No hydronic physics is executed here
        """

        rows = RoomEmitterDemandAdapterV1().build_rows(self._project_state)
        self._panel.set_emitter_demand_rows(rows)

        skeleton = build_hydronic_skeleton_from_project_state_v1(
            self._project_state
        )
        self._panel.set_hydronic_skeleton_rows(
            self._build_skeleton_rows(skeleton)
        )

        pipe_runs = build_pipe_run_intents_from_skeleton_v1(skeleton)
        self._panel.set_pipe_run_intent_rows(
            self._build_pipe_run_rows(skeleton, pipe_runs)
        )

        snapshot = self._resolve_topology_snapshot()

        if snapshot is None:
            self._panel.render_empty_state()
            return

        dto = self._build_schematic_dto(snapshot)
        self._panel._set_schematic(dto)

    # ------------------------------------------------------------------
    # Skeleton table projection
    # ------------------------------------------------------------------

    def _build_skeleton_rows(self, skeleton) -> list[dict]:
        rows: list[dict] = []

        for leg in skeleton.supply_legs.values():
            rows.append(
                {
                    "leg_id": leg.leg_id,
                    "from": self._node_label(skeleton, leg.from_node_id),
                    "to": self._node_label(skeleton, leg.to_node_id),
                    "type": "Supply",
                    "length_m": leg.length_m,
                }
            )

        for leg in skeleton.return_legs.values():
            rows.append(
                {
                    "leg_id": leg.leg_id,
                    "from": self._node_label(skeleton, leg.from_node_id),
                    "to": self._node_label(skeleton, leg.to_node_id),
                    "type": "Return",
                    "length_m": leg.length_m,
                }
            )

        return rows

    def _node_label(self, skeleton, node_id: str) -> str:
        if node_id == skeleton.boiler.boiler_id:
            return skeleton.boiler.name

        terminal = skeleton.terminals.get(node_id)
        if terminal is not None:
            room_id = getattr(terminal, "room_id", None)

            if room_id:
                room = self._project_state.rooms.get(room_id)
                if room is not None:
                    return room_short_label(room_id, room)

            return getattr(terminal, "room_name", None) or str(node_id)

        return str(node_id)

    def _build_pipe_run_rows(self, skeleton, pipe_runs) -> list[dict]:
        rows: list[dict] = []

        for pipe in pipe_runs:
            rows.append(
                {
                    "pipe_run_id": pipe.pipe_run_id,
                    "from": self._node_label(skeleton, pipe.from_node_id),
                    "to": self._node_label(skeleton, pipe.to_node_id),
                    "circuit_type": pipe.circuit_type,
                    "length_m": pipe.length_m,
                    "material_id": pipe.material_id,
                    "nominal_diameter_mm": pipe.nominal_diameter_mm,
                }
            )

        return rows

    # ------------------------------------------------------------------
    # DTO construction
    # ------------------------------------------------------------------

    def _build_schematic_dto(self, snapshot) -> HydronicsSchematicDTO:
        nodes: list[SchematicNodeDTO] = []
        edges: list[SchematicEdgeDTO] = []
        labels: list[SchematicLabelDTO] = []

        # --------------------------------------------------------------
        # Deterministic schematic layout (Phase C)
        # --------------------------------------------------------------
        x = 100.0
        y = 120.0
        x_step = 180.0

        for node in snapshot.nodes:
            role = self._map_node_role(node)

            # Phase E: shape semantics
            shape = "CIRCLE"
            if role == NodeRole.PLANT:
                shape = "OBLONG"
            elif role == NodeRole.PUMP:
                shape = "TRIANGLE"

            nodes.append(
                SchematicNodeDTO(
                    id=node.id,
                    x=x,
                    y=y,
                    role=role,
                    shape=shape,
                    orientation_deg=self._map_pump_orientation(node),
                )
            )
            x += x_step

        # --------------------------------------------------------------
        # Edges
        # --------------------------------------------------------------
        for edge in snapshot.edges:
            edges.append(
                SchematicEdgeDTO(
                    from_node_id=edge.from_node_id,
                    to_node_id=edge.to_node_id,
                    direction=self._map_edge_direction(edge),
                    style=self._map_edge_style(edge),
                )
            )

        # --------------------------------------------------------------
        # Minimal annotation
        # --------------------------------------------------------------
        labels.append(
            SchematicLabelDTO(
                x=20.0,
                y=20.0,
                text="Hydronics schematic (read-only)",
            )
        )

        return HydronicsSchematicDTO(
            nodes=nodes,
            edges=edges,
            annotations=labels,
        )

    # ------------------------------------------------------------------
    # Snapshot resolution (Phase B safe)
    # ------------------------------------------------------------------

    def _resolve_topology_snapshot(self):
        """
        Returns:
            • snapshot object
            • None if no hydronics data exists (VALID)
        """
        ps = self._project_state

        snapshot = getattr(ps, "hydronics_topology_snapshot", None)
        if snapshot is not None:
            return snapshot

        snapshot = getattr(ps, "topology_snapshot", None)
        if snapshot is not None:
            return snapshot

        return None

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _map_node_role(self, node) -> NodeRole:
        return {
            "plant": NodeRole.PLANT,
            "pump": NodeRole.PUMP,
            "emitter": NodeRole.EMITTER,
            "junction": NodeRole.JUNCTION,
            "sensor": NodeRole.SENSOR,
        }.get(node.kind, NodeRole.JUNCTION)

    def _map_edge_direction(self, edge) -> EdgeDirection:
        if getattr(edge, "direction", None) == "FLOW":
            return EdgeDirection.FLOW
        if getattr(edge, "direction", None) == "RETURN":
            return EdgeDirection.RETURN
        return EdgeDirection.BIDIRECTIONAL

    def _map_edge_style(self, edge) -> EdgeStyle:
        return {
            "primary": EdgeStyle.PRIMARY,
            "secondary": EdgeStyle.SECONDARY,
            "branch": EdgeStyle.BRANCH,
        }.get(edge.classification, EdgeStyle.SERVICE)

    # ------------------------------------------------------------------
    # Phase E — pump orientation
    # ------------------------------------------------------------------

    def _map_pump_orientation(self, node) -> float | None:
        """
        Phase E: determine pump orientation.

        Convention:
        - 0°   → pointing right (FLOW)
        - 180° → pointing left  (RETURN toward boiler)
        """
        if node.kind != "pump":
            return None

        if getattr(node, "circuit_role", None) == "RETURN":
            return 180.0

        return 0.0
