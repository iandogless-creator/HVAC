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
from HVAC.hydronics.worksheets.basic_hydronics_worksheet_v1 import (
    build_basic_hydronics_worksheet_v1,
)
from HVAC.hydronics.sizing.emitter_sizing_suggestion_v1 import (
    build_emitter_sizing_suggestion_v1,
)
from HVAC.hydronics.routing.index_route_accumulator_v1 import (
    build_index_route_accumulator_v1,
)
from HVAC.hydronics.sizing.basic_pipe_size_suggestion_v1 import (
    build_basic_pipe_size_suggestion_v1,
)

class HydronicsSchematicPanelAdapter:
    """
    GUI v3 — Hydronics Schematic Panel Adapter.

    Responsibilities
    ----------------
    • Read ProjectState
    • Build hydronics projection rows
    • Build read-only schematic DTO when available
    • Push projection data into HydronicsSchematicPanel

    Explicitly forbidden
    --------------------
    • No ProjectState mutation
    • No emitter creation
    • No hydronic authority
    • No heat-loss calculation
    • No pressure-loss calculation
    """

    def __init__(
        self,
        *,
        panel: HydronicsSchematicPanel,
        project_state: ProjectState,
    ) -> None:
        self._panel = panel
        self._project_state = project_state

        self.refresh()

    def set_project_state(self, project_state: ProjectState) -> None:
        """
        Rebind adapter to the current ProjectState.

        Required when a project is loaded or ProjectState is swapped.
        """
        if project_state is self._project_state:
            return

        self._project_state = project_state
        self.refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Hydronics schematic panel refresh.

        Projection only:
        • demand summary
        • hydronic skeleton
        • pipe-run intent
        • index route accumulator
        • index route pipe size suggestion
        • linear index route trace
        • basic hydronics worksheet
        • legacy schematic DTO if available

        No ProjectState mutation.
        No emitter creation.
        No hydronic physics.
        """

        # --------------------------------------------------
        # Emitter demand summary
        # --------------------------------------------------
        demand_rows = RoomEmitterDemandAdapterV1().build_rows(
            self._project_state
        )
        self._panel.set_emitter_demand_rows(demand_rows)

        # --------------------------------------------------
        # Hydronic skeleton
        # --------------------------------------------------
        skeleton = build_hydronic_skeleton_from_project_state_v1(
            self._project_state
        )
        self._panel.set_hydronic_skeleton_rows(
            self._build_skeleton_rows(skeleton)
        )

        # --------------------------------------------------
        # Pipe-run intent
        # --------------------------------------------------
        pipe_runs = build_pipe_run_intents_from_skeleton_v1(skeleton)
        self._panel.set_pipe_run_intent_rows(
            self._build_pipe_run_rows(skeleton, pipe_runs)
        )

        # --------------------------------------------------
        # Index route accumulator
        # --------------------------------------------------
        index_route = build_index_route_accumulator_v1(
            self._project_state
        )
        self._panel.set_index_route_accumulator_rows(
            self._build_index_route_rows(index_route)
        )

        # --------------------------------------------------
        # Index route pipe size suggestion
        # --------------------------------------------------
        pipe_size_suggestion = build_basic_pipe_size_suggestion_v1(
            self._project_state
        )
        self._panel.set_pipe_size_suggestion_rows(
            self._build_pipe_size_suggestion_rows(pipe_size_suggestion)
        )

        # --------------------------------------------------
        # Linear index route trace
        # --------------------------------------------------
        self._panel.set_index_route_trace(
            **self._build_index_route_trace(
                index_route,
                pipe_size_suggestion,
            )
        )

        # --------------------------------------------------
        # Basic hydronics worksheet
        # --------------------------------------------------
        worksheet = build_basic_hydronics_worksheet_v1(
            self._project_state
        )
        sizing_suggestion = build_emitter_sizing_suggestion_v1(
            self._project_state,
            allowance_percent=self._resolve_emitter_allowance_percent(),
            rounding_step_W=50.0,
        )

        self._panel.set_basic_hydronics_worksheet_rows(
            self._build_basic_hydronics_rows(
                worksheet,
                sizing_suggestion,
            )
        )

        # --------------------------------------------------
        # Legacy drawn topology schematic
        # --------------------------------------------------
        snapshot = self._resolve_topology_snapshot()

        if snapshot is None:
            self._panel.render_empty_state()
            return

        dto = self._build_schematic_dto(snapshot)
        self._panel._set_schematic(dto)

    def _build_pipe_size_suggestion_rows(self, suggestion) -> list[dict]:
        rows: list[dict] = []

        for row in getattr(suggestion, "rows", []):
            rows.append(
                {
                    "section": str(row.section_index),
                    "from": row.from_room_label,
                    "to": row.to_room_label,
                    "flow": self._fmt_kg_s(
                        row.accumulated_mass_flow_kg_s
                    ),
                    "size": self._fmt_mm(
                        row.suggested_nominal_size_mm
                    ),
                    "capacity": self._fmt_kg_s(
                        row.capacity_mass_flow_kg_s
                    ),
                    "status": row.status,
                }
            )

        return rows

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

    def _build_index_route_trace(self, index_route, pipe_size_suggestion=None) -> dict:
        """
        Build display data for the H-N8c linear index route trace.

        Projection only.
        Route authority remains IndexRouteAccumulatorV1.
        Pipe size suggestion authority remains BasicPipeSizeSuggestionV1.
        """
        sections = list(getattr(index_route, "sections", []) or [])

        pipe_rows = (
            list(getattr(pipe_size_suggestion, "rows", []) or [])
            if pipe_size_suggestion is not None
            else []
        )

        pipe_by_section = {
            row.section_index: row
            for row in pipe_rows
        }

        if not sections:
            return {
                "nodes": [],
                "link_labels": [],
                "excluded": list(
                    getattr(index_route, "excluded_room_labels", tuple())
                    or tuple()
                ),
                "basis": str(getattr(index_route, "route_basis", "") or ""),
            }

        nodes: list[str] = [sections[0].from_room_label]
        link_labels: list[str] = []

        for section in sections:
            nodes.append(section.to_room_label)

            pipe_row = pipe_by_section.get(section.section_index)

            flow_text = self._fmt_kg_s(
                section.accumulated_mass_flow_kg_s
            )

            size_text = (
                self._fmt_mm(pipe_row.suggested_nominal_size_mm)
                if pipe_row is not None
                else "—"
            )

            link_labels.append(f"{flow_text}\n{size_text}")

        excluded = list(
            getattr(index_route, "excluded_room_labels", tuple()) or tuple()
        )

        return {
            "nodes": nodes,
            "link_labels": link_labels,
            "excluded": excluded,
            "basis": str(getattr(index_route, "route_basis", "") or ""),
        }
    def _build_index_route_rows(self, index_route) -> list[dict]:
        rows: list[dict] = []

        for section in getattr(index_route, "sections", []):
            rows.append(
                {
                    "section": str(section.section_index),
                    "from": section.from_room_label,
                    "to": section.to_room_label,
                    "accumulated_flow": self._fmt_kg_s(
                        section.accumulated_mass_flow_kg_s
                    ),
                    "included": self._compact_included_labels(
                        section.included_room_labels
                    ),
                }
            )

        # Optional compact note row for excluded rooms.
        excluded = getattr(index_route, "excluded_room_labels", tuple()) or tuple()
        if excluded:
            rows.append(
                {
                    "section": "—",
                    "from": "Excluded",
                    "to": "",
                    "accumulated_flow": "",
                    "included": ", ".join(excluded),
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

    def _build_basic_hydronics_rows(
            self,
            worksheet,
            sizing_suggestion,
    ) -> list[dict]:
        rows: list[dict] = []

        sizing_by_room_id = {
            row.room_id: row
            for row in getattr(sizing_suggestion, "rows", [])
        }

        for row in worksheet.rows:
            sizing = sizing_by_room_id.get(row.room_id)

            rows.append(
                {
                    "room": row.room_label,
                    "heat_load": self._fmt_w(row.heat_load_W),
                    "required_output": (
                        self._fmt_w(sizing.required_output_W)
                        if sizing is not None
                        else "—"
                    ),
                    "suggested_output": (
                        self._fmt_w(sizing.suggested_rounded_output_W)
                        if sizing is not None
                        else "—"
                    ),
                    "emitter": row.emitter_summary,
                    "output": self._fmt_w(row.emitter_output_W),
                    "status": row.emitter_status,
                    "sizing_status": (
                        sizing.status
                        if sizing is not None
                        else "—"
                    ),
                    "flow_temp": self._fmt_c(row.flow_temp_C),
                    "return_temp": self._fmt_c(row.return_temp_C),
                    "water_delta_t": self._fmt_k(row.water_delta_t_K),
                    "mass_flow": self._fmt_kg_s(row.mass_flow_kg_s),
                }
            )

        return rows

    def _resolve_emitter_allowance_percent(self) -> float:
        """
        Resolve emitter sizing allowance.

        Current authority
        -----------------
        ProjectState.basic_hydronic_sizing_intent.allowance_percent

        Fallback
        --------
        12.0 %

        Notes
        -----
        This is a read-only projection helper. It does not mutate ProjectState.
        Later this may move to Environment / Hydronic Design Conditions.
        """
        intent = getattr(
            self._project_state,
            "basic_hydronic_sizing_intent",
            None,
        )

        if intent is None:
            return 12.0

        value = getattr(intent, "allowance_percent", None)

        if value is None:
            return 12.0

        try:
            value = float(value)
        except (TypeError, ValueError):
            return 12.0

        if value < 0.0:
            return 12.0

        return value

    @staticmethod
    def _compact_included_labels(labels) -> str:
        """
        Compact display for included route rooms.

        For short paths:
            R5
            R5 + R4
            R5 + R4 + R3

        For longer paths:
            R5–R2
        """
        labels = list(labels or [])

        if not labels:
            return "—"

        refs: list[str] = []

        for label in labels:
            text = str(label)
            ref = text.split(" ", 1)[0] if text else ""
            refs.append(ref or text)

        if len(refs) <= 3:
            return " + ".join(refs)

        return f"{refs[0]}–{refs[-1]}"

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

    @staticmethod
    def _fmt_w(value) -> str:
        return "—" if value is None else f"{float(value):.1f} W"

    @staticmethod
    def _fmt_c(value) -> str:
        return "—" if value is None else f"{float(value):.1f} °C"

    @staticmethod
    def _fmt_k(value) -> str:
        return "—" if value is None else f"{float(value):.1f} K"

    @staticmethod
    def _fmt_kg_s(value) -> str:
        return "—" if value is None else f"{float(value):.5f} kg/s"

    @staticmethod
    def _fmt_mm(value) -> str:
        return "—" if value is None else f"{float(value):.0f} mm"