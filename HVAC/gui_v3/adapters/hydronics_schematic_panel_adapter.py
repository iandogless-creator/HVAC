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
from HVAC.hydronics.pipes.pipe_authority_summary_v1 import (
    build_pipe_authority_summary_v1,
)
from HVAC.hydronics.proportioning.branch_proportioning_summary_v1 import (
    build_branch_proportioning_summary_v1,
)
from HVAC.hydronics.proportioning.proportioning_schematic_projection_v1 import (
    build_proportioning_schematic_v1,
)
from HVAC.hydronics.topology.leg_subleg_projection_v1 import (
    build_leg_subleg_topology_v1,
)
from HVAC.hydronics.topology.dev_hydronic_topology_builder_v1 import (
    DevHydronicTopologyBuilderV1,
)
from HVAC.hydronics.proportioning.proportioning_readiness_v1 import (
    build_proportioning_readiness_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.local_losses.local_k_pressure_preview_v1 import (
    build_local_k_pressure_preview_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    build_route_pressure_accumulator_v1,
)
from HVAC.hydronics.proportioning.route_proportioning_shortfall_preview_v1 import (
    build_route_proportioning_shortfall_preview_v1,
)
from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    build_circuit_return_path_comparison_v1,
)

from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicV1,
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
            context: object | None = None,
    ) -> None:
        self._panel = panel
        self._project_state = project_state
        self._context = context

        self._subscribe_if_present("room_state_changed", self.refresh)
        self._subscribe_if_present("project_state_changed", self.refresh)
        self._subscribe_arg_signal_if_present(
            "hydronic_section_focus_requested",
            self._on_hydronic_section_focus_requested,
        )
        self.refresh()

    def _subscribe_if_present(self, signal_name: str, callback) -> None:
        """
        Best-effort subscription to GuiProjectContext signals.

        Keeps this adapter tolerant of context API shape.
        """
        context = getattr(self, "_context", None)
        if context is None:
            return

        signal = getattr(context, signal_name, None)
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
        # Pipe authority summary
        # --------------------------------------------------
        index_route = build_index_route_accumulator_v1(
            self._project_state
        )

        pipe_authority_summary = build_pipe_authority_summary_v1(
            project_state=self._project_state,
            skeleton=skeleton,
            pipe_runs=pipe_runs,
            index_route=index_route,
        )

        self._panel.set_pipe_authority_summary_rows(
            self._build_pipe_authority_summary_rows(
                pipe_authority_summary
            )
        )

        # --------------------------------------------------
        # Proportioning readiness
        # --------------------------------------------------
        readiness = build_proportioning_readiness_v1(
            self._project_state
        )

        if hasattr(self._panel, "set_proportioning_readiness"):
            self._panel.set_proportioning_readiness(
                {
                    "index_room": readiness.index_room_label,
                    "terminal_room": readiness.terminal_room_label,
                    "terminal_alignment": readiness.terminal_alignment_status,
                    "basis_mode": readiness.basis_mode,
                    "total_index_length": readiness.total_index_length_label,
                    "nominal_gradient": readiness.nominal_gradient_label,
                    "status": readiness.proportioning_status,
                }
            )
        # --------------------------------------------------
        # Proportioning received Basic PS sections
        # --------------------------------------------------
        try:
            basic_ps_projection = build_basic_ps_readonly_projection_v1(
                self._project_state,
                leg_id="leg-001",
            )
            received_basic_ps_rows = (
                self._build_proportioning_basic_ps_sections(
                    basic_ps_projection
                )
            )
        except Exception as exc:
            print("[PROPORTIONING BASIC PS SECTIONS ERROR]", repr(exc))
            received_basic_ps_rows = []

        if hasattr(self._panel, "set_proportioning_basic_ps_sections"):
            self._panel.set_proportioning_basic_ps_sections(
                received_basic_ps_rows
            )

        # --------------------------------------------------
        # H-S14 — Route Δp preview
        # H-S18 — Route Δp shortfall preview
        # --------------------------------------------------
        route_pressure_rows = []
        route_shortfall_rows = []

        if getattr(self._project_state, "hydronic_topology", None) is not None:
            try:
                route_pressure_projection = (
                    build_route_pressure_accumulator_v1(
                        self._project_state,
                    )
                )

                route_pressure_rows = (
                    self._build_route_pressure_preview_rows(
                        route_pressure_projection
                    )
                )

                shortfall_preview = (
                    build_route_proportioning_shortfall_preview_v1(
                        route_pressure_projection
                    )
                )

                route_shortfall_rows = (
                    self._build_route_shortfall_preview_rows(
                        shortfall_preview
                    )
                )

            except Exception as exc:
                print("[ROUTE PRESSURE / SHORTFALL PREVIEW ERROR]", repr(exc))

        if hasattr(self._panel, "set_route_pressure_preview_rows"):
            self._panel.set_route_pressure_preview_rows(route_pressure_rows)

        if hasattr(self._panel, "set_route_shortfall_preview_rows"):
            self._panel.set_route_shortfall_preview_rows(route_shortfall_rows)

        # --------------------------------------------------
        # H-S19-H — Direct vs reverse return comparison
        # --------------------------------------------------
        return_path_comparison_rows = []

        if getattr(self._project_state, "hydronic_topology", None) is not None:
            try:
                return_path_comparison_projection = (
                    build_circuit_return_path_comparison_v1(
                        self._project_state,
                    )
                )
                return_path_comparison_rows = (
                    self._build_return_path_comparison_rows(
                        return_path_comparison_projection
                    )
                )
            except Exception as exc:
                print("[RETURN PATH COMPARISON ERROR]", repr(exc))

        if hasattr(self._panel, "set_return_path_comparison_rows"):
            self._panel.set_return_path_comparison_rows(
                return_path_comparison_rows
            )
        # --------------------------------------------------
        # Branch / proportioning summary
        # --------------------------------------------------
        proportioning_rows = build_branch_proportioning_summary_v1(
            self._project_state
        )
        self._panel.set_proportioning_rows(
            self._build_proportioning_rows(proportioning_rows)
        )

        if getattr(self._project_state, "hydronic_topology", None) is None:
            DevHydronicTopologyBuilderV1.install_single_leg_on_project(
                self._project_state,
                overwrite=False,
            )
        proportioning_schematic = build_proportioning_schematic_v1(
            self._project_state
        )
        self._panel.set_proportioning_schematic(proportioning_schematic)

        # --------------------------------------------------
        # Leg / subleg topology
        # --------------------------------------------------
        leg_subleg_topology = build_leg_subleg_topology_v1(
            self._project_state
        )
        self._panel.set_leg_subleg_topology_rows(
            self._build_leg_subleg_topology_rows(leg_subleg_topology)
        )
        # --------------------------------------------------
        # H-S19-J — DEV common-main / leg / subleg topology
        # --------------------------------------------------
        common_main_leg_subleg_rows = []

        if getattr(self._project_state, "hydronic_topology", None) is not None:
            try:
                common_main_leg_subleg_rows = (
                    self._build_common_main_leg_subleg_rows(
                        self._project_state.hydronic_topology
                    )
                )
            except Exception as exc:
                print("[COMMON MAIN / LEG / SUBLEG ERROR]", repr(exc))

        if hasattr(self._panel, "set_common_main_leg_subleg_rows"):
            self._panel.set_common_main_leg_subleg_rows(
                common_main_leg_subleg_rows
            )

        common_main_leg_subleg_schematic = None

        if getattr(self._project_state, "hydronic_topology", None) is not None:
            try:
                common_main_leg_subleg_schematic = (
                    self._build_common_main_leg_subleg_schematic(
                        self._project_state.hydronic_topology
                    )
                )
            except Exception as exc:
                print("[COMMON MAIN / LEG / SUBLEG SCHEMATIC ERROR]", repr(exc))

        if hasattr(self._panel, "set_common_main_leg_subleg_schematic"):
            self._panel.set_common_main_leg_subleg_schematic(
                common_main_leg_subleg_schematic
            )

        # --------------------------------------------------
        # Index route accumulator
        # --------------------------------------------------

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

    def _build_common_main_leg_subleg_schematic(
        self,
        topology,
    ) -> CommonMainLegSublegSchematicV1:
        routes: list[CommonMainLegSublegRouteV1] = []

        for leg in getattr(topology, "legs", []) or []:
            leg_id = str(getattr(leg, "leg_id", "") or "")
            leg_label = str(
                getattr(leg, "label", None)
                or getattr(leg, "name", None)
                or leg_id
                or "Leg"
            )

            for subleg in getattr(leg, "sublegs", []) or []:
                subleg_id = str(getattr(subleg, "subleg_id", "") or "")
                raw_subleg_label = str(
                    getattr(subleg, "label", None)
                    or getattr(subleg, "name", None)
                    or subleg_id
                    or "—"
                )

                subleg_label = self._display_subleg_label(
                    raw_subleg_label
                )

                subleg_label = self._display_subleg_label(raw_subleg_label)

                room_labels = tuple(
                    self._subleg_room_ids_for_display(subleg)
                )

                routes.append(
                    CommonMainLegSublegRouteV1(
                        leg_id=leg_id,
                        leg_label=leg_label,
                        subleg_id=subleg_id,
                        subleg_label=subleg_label,
                        role=self._subleg_role_label(subleg),
                        room_labels=room_labels,
                    )
                )

        return CommonMainLegSublegSchematicV1(
            heat_source_label="Boiler / Heat Source",
            common_main_label="Common main",
            routes=tuple(routes),
            status=(
                "DEV topology schematic preview only — common main feeds legs; "
                "legs feed sublegs; sublegs carry rooms"
            ),
        )

    def _build_route_pressure_preview_rows(self, projection) -> list[dict]:
        rows: list[dict] = []

        for row in getattr(projection, "rows", ()) or ():
            rows.append(
                {
                    "rank": (
                        "—"
                        if getattr(row, "rank", None) is None
                        else str(getattr(row, "rank"))
                    ),
                    "route": getattr(row, "route_label", "—"),
                    "sections": str(getattr(row, "section_count", "—")),
                    "straight_dp": self._format_pa(
                        getattr(row, "straight_pressure_drop_total_Pa", None)
                    ),
                    "local_dp": self._format_pa(
                        getattr(row, "local_pressure_drop_total_Pa", None)
                    ),
                    "route_dp": self._format_pa(
                        getattr(row, "route_pressure_drop_total_Pa", None)
                    ),
                    "complete": (
                        "Yes" if getattr(row, "complete", False) else "No"
                    ),
                    "controlling": (
                        "Yes"
                        if getattr(row, "is_controlling_candidate", False)
                        else "No"
                    ),
                    "status": getattr(row, "status", "—"),
                }
            )

        return rows

    def _build_return_path_comparison_rows(self, projection) -> list[dict]:
        rows: list[dict] = []

        for row in getattr(projection, "rows", ()) or ():
            rows.append(
                {
                    "route": getattr(row, "route_label", "—"),
                    "room": getattr(row, "room_id", "—"),
                    "emitter": getattr(row, "emitter_id", "—") or "—",
                    "direct_rank": (
                        "—"
                        if getattr(row, "direct_rank", None) is None
                        else str(getattr(row, "direct_rank"))
                    ),
                    "direct_total_dp": self._format_pa(
                        getattr(row, "direct_total_dp_Pa", None)
                    ),
                    "direct_total_dp_raw": getattr(
                        row,
                        "direct_total_dp_Pa",
                        None,
                    ),
                    "direct_controlling": (
                        "Yes"
                        if getattr(row, "controlling_direct", False)
                        else "No"
                    ),
                    "reverse_rank": (
                        "—"
                        if getattr(row, "reverse_return_rank", None) is None
                        else str(getattr(row, "reverse_return_rank"))
                    ),
                    "reverse_total_dp": self._format_pa(
                        getattr(row, "reverse_return_total_dp_Pa", None)
                    ),
                    "reverse_total_dp_raw": getattr(
                        row,
                        "reverse_return_total_dp_Pa",
                        None,
                    ),
                    "reverse_controlling": (
                        "Yes"
                        if getattr(
                            row,
                            "controlling_reverse_return",
                            False,
                        )
                        else "No"
                    ),
                    "rr_suitability": getattr(
                        row,
                        "rr_suitability_status",
                        "—",
                    ),
                    "status": getattr(row, "status", "—"),
                }
            )

        return rows

    def _build_route_shortfall_preview_rows(self, preview) -> list[dict]:
        rows: list[dict] = []

        for row in getattr(preview, "rows", []) or []:
            rows.append(
                {
                    "rank": (
                        "—"
                        if getattr(row, "rank", None) is None
                        else str(getattr(row, "rank"))
                    ),
                    "route": getattr(row, "route_label", "—"),
                    "route_dp": self._format_pa(
                        getattr(row, "route_dp_Pa", None)
                    ),
                    "controlling_dp": self._format_pa(
                        getattr(row, "controlling_dp_Pa", None)
                    ),
                    "shortfall_dp": self._format_pa(
                        getattr(row, "shortfall_dp_Pa", None)
                    ),
                    "action": getattr(row, "action", "—"),
                    "status": getattr(row, "status", "—"),
                }
            )

        return rows

    def _build_proportioning_basic_ps_sections(self, projection) -> list[dict]:
        """
        Convert composed Basic PS read-only projection into rows displayed
        on the Proportioning tab as received first-pass basis.

        H-S12-C:
        Also display persisted Local K preview values where present.

        Display only:
        - no ProjectState mutation
        - no new pipe sizing
        - no final balancing
        - no final proportioning
        """
        preview_by_section_id = {
            getattr(row, "section_id", ""): row
            for row in projection.pressure_preview_projection.rows
        }

        rows: list[dict] = []

        for result in projection.pipe_sizing_projection.results:
            section_id = str(getattr(result, "section_id", "") or "")
            preview = preview_by_section_id.get(section_id)

            section_length_m = (
                getattr(preview, "section_length_m", None)
                if preview is not None
                else None
            )
            section_pressure_drop_Pa = (
                getattr(preview, "section_pressure_drop_Pa", None)
                if preview is not None
                else None
            )
            preview_status = (
                getattr(preview, "status", "")
                if preview is not None
                else ""
            )

            local_k_preview = build_local_k_pressure_preview_v1(
                self._project_state,
                section_id=section_id,
                velocity_m_s=float(
                    getattr(result, "velocity_m_s", 0.0) or 0.0
                ),
                pressure_gradient_Pa_per_m=float(
                    getattr(result, "pressure_gradient_Pa_per_m", 0.0) or 0.0
                ),
            )

            display_length_m = (
                local_k_preview.length_m
                if local_k_preview.length_m is not None
                else section_length_m
            )

            display_section_dp = (
                local_k_preview.section_total_pressure_drop_Pa
                if local_k_preview.section_total_pressure_drop_Pa is not None
                else section_pressure_drop_Pa
            )

            status_parts = [
                str(getattr(result, "status", "") or ""),
                str(preview_status or ""),
                str(local_k_preview.status or ""),
            ]
            status = " / ".join(
                part for part in status_parts if part and part != "—"
            ) or "—"

            rows.append(
                {
                    "section_id": section_id,
                    "order": getattr(result, "order", "—"),
                    "from": getattr(result, "from_label", "—"),
                    "to": getattr(result, "to_room_label", "—"),
                    "q_carried": self._format_watts(
                        getattr(result, "carried_heat_W", None)
                    ),
                    "flow_kg_s": self._format_kg_s(
                        getattr(result, "carried_flow_kg_s", None)
                    ),
                    "pipe": str(getattr(result, "pipe_size_label", "") or "—"),
                    "velocity_m_s": self._format_velocity(
                        getattr(result, "velocity_m_s", None)
                    ),
                    "dp_per_m": self._format_dp_per_m(
                        getattr(result, "pressure_gradient_Pa_per_m", None)
                    ),
                    "length_m": self._format_length(display_length_m),
                    "k_total": f"{local_k_preview.k_total:.2f}",
                    "local_dp": self._format_pa(
                        local_k_preview.local_pressure_drop_Pa
                    ),
                    "straight_dp": self._format_pa(
                        local_k_preview.straight_pressure_drop_Pa
                    ),
                    "section_dp": self._format_pa(display_section_dp),
                    "status": status,
                }
            )

        return rows

    def _build_common_main_leg_subleg_rows(self, topology) -> list[dict]:
        rows: list[dict] = []

        for leg in getattr(topology, "legs", []) or []:
            leg_id = str(getattr(leg, "leg_id", "") or "")
            leg_label = str(
                getattr(leg, "label", None)
                or getattr(leg, "name", None)
                or leg_id
                or "—"
            )

            for subleg in getattr(leg, "sublegs", []) or []:
                subleg_id = str(getattr(subleg, "subleg_id", "") or "")
                raw_subleg_label = str(
                    getattr(subleg, "label", None)
                    or getattr(subleg, "name", None)
                    or subleg_id
                    or "—"
                )

                subleg_label = self._display_subleg_label(raw_subleg_label)

                room_ids = self._subleg_room_ids_for_display(subleg)
                rooms_label = " → ".join(room_ids) if room_ids else "—"

                rows.append(
                    {
                        "common_main": "Common main",
                        "leg": leg_label,
                        "subleg": subleg_label,
                        "role": self._subleg_role_label(subleg),
                        "rooms": rooms_label,
                        "status": (
                            "DEV topology preview — common main feeds leg; "
                            "subleg carries rooms"
                        ),
                    }
                )

        return rows

    @staticmethod
    def _subleg_room_ids_for_display(subleg) -> list[str]:
        for field_name in (
            "route_room_ids",
            "room_ids",
            "rooms",
            "room_sequence",
            "terminal_room_ids",
        ):
            value = getattr(subleg, field_name, None)

            if not value:
                continue

            result: list[str] = []

            for item in value:
                if isinstance(item, str):
                    result.append(item)
                else:
                    room_id = (
                        getattr(item, "room_id", None)
                        or getattr(item, "id", None)
                    )
                    if room_id:
                        result.append(str(room_id))

            if result:
                return result

        return []

    @staticmethod
    def _subleg_role_label(subleg) -> str:
        subleg_id = str(getattr(subleg, "subleg_id", "") or "").lower()
        label = str(
            getattr(subleg, "label", None)
            or getattr(subleg, "name", None)
            or ""
        ).lower()

        source_text = f"{subleg_id} {label}"

        if "primary" in source_text or "common" in source_text:
            return "Common"

        if "branch" in source_text or "subleg-b" in source_text:
            return "Branch"

        return "Subleg"

    @staticmethod
    def _display_subleg_label(label: str) -> str:
        text = str(label or "")

        replacements = {
            "Leg 1A Common subleg": "Subleg 1A",
            "Leg 1B Branch subleg": "Subleg 1B",
            "Leg 2A Common subleg": "Subleg 2A",
            "Leg 2B Branch subleg": "Subleg 2B",
            "Leg 3A Common subleg": "Subleg 3A",
            "Leg 3B Branch subleg": "Subleg 3B",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    @staticmethod
    def _format_watts(value: object) -> str:
        try:
            if value is None:
                return "—"
            return f"{float(value):.1f} W"
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _format_kg_s(value: object) -> str:
        try:
            if value is None:
                return "—"
            return f"{float(value):.4f} kg/s"
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _format_velocity(value: object) -> str:
        try:
            if value is None:
                return "—"
            return f"{float(value):.3f}"
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _format_dp_per_m(value: object) -> str:
        try:
            if value is None:
                return "—"
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _format_length(value: object) -> str:
        try:
            if value is None:
                return "Not set"
            return f"{float(value):.2f} m"
        except (TypeError, ValueError):
            return "Not set"

    @staticmethod
    def _format_pa(value: object) -> str:
        try:
            if value is None:
                return "—"
            return f"{float(value):.1f} Pa"
        except (TypeError, ValueError):
            return "—"

    def _build_pipe_authority_summary_rows(self, summary) -> list[dict]:
        rows: list[dict] = []

        role_order = {
            "COMMON_MAIN": 0,
            "INDEX_ROUTE_SECTION": 1,
            "NON_INDEX_BRANCH_TERMINAL": 2,
            "NO_EMITTER_UNRESOLVED": 3,
        }
        role_display = {
            "COMMON_MAIN": "Common main",
            "INDEX_ROUTE_SECTION": "Selected index route",
            "NON_INDEX_BRANCH_TERMINAL": "Non-index branch terminal",
            "NO_EMITTER_UNRESOLVED": "No-emitter / unresolved",
        }
        authority_rows = list(getattr(summary, "rows", []) or [])

        authority_rows.sort(
            key=lambda row: (
                role_order.get(getattr(row, "pipe_role", ""), 99),
                getattr(row, "from_label", ""),
                getattr(row, "to_label", ""),
            )
        )

        for row in authority_rows:
            rows.append(
                {
                    "pipe_role": role_display.get(
                        getattr(row, "pipe_role", "—"),
                        getattr(row, "pipe_role", "—"),
                    ),
                    "from_label": getattr(row, "from_label", "—"),
                    "to_label": getattr(row, "to_label", "—"),
                    "flow_basis": getattr(row, "flow_basis", "—"),
                    "mass_flow": self._fmt_mass_flow(
                        getattr(row, "mass_flow_kg_s", None)
                    ),
                    "sizing_scope": getattr(row, "sizing_scope", "—"),
                    "status": getattr(row, "status", "—"),
                }
            )

        return rows

    def _build_proportioning_rows(self, rows) -> list[dict]:
        """
        Convert H-R1 branch/proportioning DTO rows into panel rows.

        Adapter responsibility:
        • DTO → display dict only
        • no physics
        • no ProjectState mutation
        """

        out: list[dict] = []

        for row in rows or []:
            out.append(
                {
                    "group": str(getattr(row, "group", "") or ""),
                    "role": str(getattr(row, "role", "") or ""),
                    "from": str(getattr(row, "from_label", "") or ""),
                    "to": str(getattr(row, "to_label", "") or ""),
                    "flow": str(getattr(row, "flow_label", "") or ""),
                    "basis": str(getattr(row, "basis", "") or ""),
                    "status": str(getattr(row, "status", "") or ""),
                }
            )

        return out

    def _build_leg_subleg_topology_rows(self, topology) -> list[dict]:
        """
        Convert H-T2 leg/subleg topology DTO into read-only panel rows.

        Adapter responsibility:
        • DTO → display dict only
        • no pressure loss
        • no pipe sizing
        • no ProjectState mutation
        """

        nodes_by_id = {
            getattr(node, "node_id", ""): node
            for node in getattr(topology, "nodes", []) or []
        }

        out: list[dict] = []

        for section in getattr(topology, "sections", []) or []:
            from_node = nodes_by_id.get(getattr(section, "from_node_id", ""))
            to_node = nodes_by_id.get(getattr(section, "to_node_id", ""))

            flow = getattr(section, "flow_kg_s", None)
            flow_label = "—" if flow is None else f"{float(flow):.4f} kg/s"

            out.append(
                {
                    "section": str(getattr(section, "label", "") or getattr(section, "section_id", "")),
                    "role": self._display_leg_subleg_role(
                        getattr(section, "role", "")
                    ),
                    "from": str(getattr(from_node, "label", "") or getattr(section, "from_node_id", "")),
                    "to": str(getattr(to_node, "label", "") or getattr(section, "to_node_id", "")),
                    "flow": flow_label,
                    "termination": str(getattr(section, "termination", "") or ""),
                    "basis": str(getattr(section, "flow_basis", "") or ""),
                }
            )

        return out

    def _display_leg_subleg_role(self, role: str) -> str:
        role_display = {
            "COMMON_LEG": "Leg 1 / Common leg",
            "SUBLEG_CIRCUIT": "Subleg circuit",
            "TERMINAL_BRANCH": "Terminal/radiator branch",
            "INTERMEDIATE_BRANCH": "Intermediate branch",
        }

        return role_display.get(str(role), str(role))

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

    def _subscribe_arg_signal_if_present(self, signal_name: str, callback) -> None:
        """
        Subscribe to a context signal while preserving emitted arguments.
        Used for focus signals such as section_id.
        """
        context = getattr(self, "_context", None)
        if context is None:
            return

        signal = getattr(context, signal_name, None)
        if signal is None:
            return

        connect = getattr(signal, "connect", None)
        if callable(connect):
            try:
                connect(callback)
            except TypeError:
                pass

    def _on_hydronic_section_focus_requested(
        self,
        section_id: str,
    ) -> None:
        if hasattr(self._panel, "focus_proportioning_basic_ps_section"):
            self._panel.focus_proportioning_basic_ps_section(section_id)

    @staticmethod
    def _short_subleg_label(subleg_id: str, label: str) -> str:
        source = f"{subleg_id} {label}".lower()

        if "1a" in source or "primary" in source and "leg-001" in source:
            return "Subleg 1A"
        if "1b" in source or "subleg-b" in source and "leg-001" in source:
            return "Subleg 1B"
        if "2a" in source or "primary" in source and "leg-002" in source:
            return "Subleg 2A"
        if "2b" in source or "subleg-b" in source and "leg-002" in source:
            return "Subleg 2B"

        return label.replace("Leg", "Subleg")

    @staticmethod
    def _display_subleg_label(label: str) -> str:
        text = str(label or "")

        replacements = {
            "Leg 1A Common subleg": "Subleg 1A",
            "Leg 1B Branch subleg": "Subleg 1B",
            "Leg 2A Common subleg": "Subleg 2A",
            "Leg 2B Branch subleg": "Subleg 2B",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text
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

    @staticmethod
    def _fmt_mass_flow(value) -> str:
        if value is None:
            return "—"

        try:
            return f"{float(value):.5f} kg/s"
        except (TypeError, ValueError):
            return "—"