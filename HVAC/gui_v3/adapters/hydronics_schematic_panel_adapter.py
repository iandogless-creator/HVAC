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
from PySide6.QtGui import QColor, QBrush

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
from HVAC.hydronics.proportioning.branch_aware_route_summary_audit_v1 import (
    build_branch_aware_route_summary_audit_v1,
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
from HVAC.hydronics.proportioning.chosen_basis_route_pressure_preview_v1 import (
    build_chosen_basis_route_pressure_preview_v1,
)
from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicV1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    INHERIT,
    ReturnArrangementIntentV1,
    resolve_system_return_arrangement_v1,
    resolve_leg_return_arrangement_v1,
    resolve_subleg_return_arrangement_v1,
)
from HVAC.hydronics.proportioning.effective_return_arrangement_resolver_v1 import (
    resolve_effective_return_arrangements_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    build_proportioned_basis_snapshot_v1,
)
from HVAC.hydronics.proportioning.chosen_basis_route_pressure_preview_v1 import (
    build_chosen_basis_route_pressure_preview_v1,
)
from HVAC.hydronics.proportioning.chosen_basis_controlling_route_preview_v1 import (
    build_chosen_basis_controlling_route_preview_v1,
)
from HVAC.hydronics.proportioning.chosen_basis_proportioned_readiness_summary_v1 import (
    build_chosen_basis_proportioned_readiness_summary_v1,
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

        # --------------------------------------------------
        # H-S26-C — User return-arrangement acceptance callback
        # --------------------------------------------------
        if hasattr(
                self._panel,
                "set_system_return_arrangement_acceptance_callback",
        ):
            self._panel.set_system_return_arrangement_acceptance_callback(
                self.set_system_return_arrangement_acceptance
            )

        # --------------------------------------------------
        # H-S26-I5 — Scoped return-arrangement override callback
        # --------------------------------------------------
        if hasattr(
                self._panel,
                "set_scoped_return_arrangement_acceptance_callback",
        ):
            self._panel.set_scoped_return_arrangement_acceptance_callback(
                self.set_scoped_return_arrangement_acceptance
            )

        # --------------------------------------------------
        # H-S29-M — RR length basis mode callback
        # --------------------------------------------------
        if hasattr(
                self._panel,
                "set_rr_length_basis_mode_callback",
        ):
            self._panel.set_rr_length_basis_mode_callback(
                self.set_rr_length_basis_mode
            )

        if hasattr(
                self._panel,
                "set_rr_manual_extra_length_callback",
        ):
            self._panel.set_rr_manual_extra_length_callback(
                self.set_rr_manual_extra_length_m
            )

        # --------------------------------------------------
        # H-S26-G — Commit Proportioning basis snapshot callback
        # --------------------------------------------------
        if hasattr(
                self._panel,
                "set_commit_proportioning_callback",
        ):
            self._panel.set_commit_proportioning_callback(
                self.commit_proportioning_basis_snapshot
            )

        self.refresh()



    def _restore_return_arrangement_acceptance_basis_to_panel(self) -> None:
        """
        H-S26-D:
        Restore the persisted system-wide return-arrangement basis into the
        radio buttons during adapter refresh.

        Display restore only:
        • no ProjectState mutation
        • no final Proportioned commit
        • no valve selection
        • no pump selection
        • no pipe resizing
        • no automatic choice from F+R / F+RR evidence
        """
        return_intent = self._get_return_arrangement_acceptance_intent()

        basis = getattr(
            return_intent,
            "system_arrangement",
            "UNDECIDED",
        )

        if hasattr(
                self._panel,
                "set_system_return_arrangement_acceptance_basis",
        ):
            self._panel.set_system_return_arrangement_acceptance_basis(
                basis
            )

    @staticmethod
    def _normalise_rr_length_basis_mode_v1(mode: str) -> str:
        mode = (
            str(mode or "")
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if mode in {
                "downstream",
                "downstream_proxy",
                "derived_downstream",
                "downstream_allowance",
        }:
            return "downstream_proxy"

        if mode in {
                "manual",
                "manual_allowance",
                "manual_length",
                "manual_extra",
        }:
            return "manual_allowance"

        return "physical_loop_zero_extra"

    def _current_rr_length_basis_mode_v1(self) -> str:
        """
        H-S29-M1:
        RR length basis mode is stored on the return-arrangement intent.
        Fall back to the old temporary ProjectState attribute only for
        tolerance during development.
        """
        project = getattr(self, "_project_state", None)

        if project is None:
            return "physical_loop_zero_extra"

        intent = getattr(
            project,
            "hydronic_return_arrangement_intent",
            None,
        )

        return self._normalise_rr_length_basis_mode_v1(
            getattr(
                intent,
                "rr_added_length_basis_mode",
                getattr(
                    project,
                    "hydronic_rr_added_length_basis_mode",
                    "physical_loop_zero_extra",
                ),
            )
        )

    def _current_rr_manual_extra_length_m_v1(self) -> float:
        """
        H-S29-N:
        Manual RR extra length is stored on return-arrangement intent.
        Legacy loose ProjectState attributes remain fallback only.
        """
        project = getattr(self, "_project_state", None)

        if project is None:
            return 0.0

        intent = getattr(
            project,
            "hydronic_return_arrangement_intent",
            None,
        )

        if isinstance(intent, dict):
            value = intent.get("rr_added_length_m")
        else:
            value = getattr(intent, "rr_added_length_m", None)

        if value is None:
            for attr_name in (
                "hydronic_rr_added_length_m",
                "hydronic_reverse_return_added_length_m",
                "rr_added_length_m",
            ):
                value = getattr(project, attr_name, None)

                if value is not None:
                    break

        try:
            return max(float(value), 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _restore_rr_manual_extra_length_to_panel(self) -> None:
        """
        H-S29-N:
        Restore ProjectState-backed manual RR length into panel control.
        """
        if hasattr(self._panel, "set_rr_manual_extra_length_m"):
            self._panel.set_rr_manual_extra_length_m(
                self._current_rr_manual_extra_length_m_v1()
            )

    def _restore_rr_length_basis_mode_to_panel(self) -> None:
        """
        H-S29-M:
        Restore the ProjectState-backed RR length basis mode into the
        acceptance-panel combo.
        """
        if hasattr(self._panel, "set_rr_length_basis_mode"):
            self._panel.set_rr_length_basis_mode(
                self._current_rr_length_basis_mode_v1()
            )

    def set_rr_manual_extra_length_m(self, value: float) -> None:
        """
        H-S29-N:
        Persist manual RR added length in return-arrangement intent.
        """
        project = getattr(self, "_project_state", None)

        if project is None:
            print(
                "H-S29-N warning: no ProjectState available for "
                "manual RR extra length"
            )
            return

        try:
            value = max(float(value), 0.0)
        except (TypeError, ValueError):
            value = 0.0

        intent = self._get_return_arrangement_acceptance_intent()

        if isinstance(intent, dict):
            next_intent = dict(intent)
            next_intent["rr_added_length_m"] = value
        else:
            try:
                from dataclasses import replace

                next_intent = replace(intent, rr_added_length_m=value)
            except Exception:
                setattr(intent, "rr_added_length_m", value)
                next_intent = intent

        project.hydronic_return_arrangement_intent = next_intent

        if hasattr(project, "mark_dirty"):
            project.mark_dirty()

        self.refresh()

    def set_rr_length_basis_mode(self, mode: str) -> None:
        """
        H-S29-M:
        User-facing RR length basis mode selection.

        ProjectState preview basis only:
        • no manual metre entry yet
        • no pump / valve / balancing / pipe resize
        • no final hydraulic result
        """
        mode = self._normalise_rr_length_basis_mode_v1(mode)

        project = getattr(self, "_project_state", None)

        if project is None:
            print(
                "H-S29-M warning: no ProjectState available for "
                "RR length basis mode"
            )
            return

        from dataclasses import replace

        intent = self._get_return_arrangement_acceptance_intent()

        if isinstance(intent, dict):
            next_intent = dict(intent)
            next_intent["rr_added_length_basis_mode"] = mode
            self._return_arrangement_acceptance_intent = next_intent
        else:
            try:
                self._return_arrangement_acceptance_intent = replace(
                    intent,
                    rr_added_length_basis_mode=mode,
                )
            except TypeError:
                setattr(intent, "rr_added_length_basis_mode", mode)
                self._return_arrangement_acceptance_intent = intent

        project.hydronic_return_arrangement_intent = (
            self._return_arrangement_acceptance_intent
        )

        print("H-S29-M RR length basis mode set:", mode)

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
        self._restore_return_arrangement_acceptance_basis_to_panel()
        self._restore_rr_length_basis_mode_to_panel()
        self._restore_rr_manual_extra_length_to_panel()

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
                    "return_arrangement_basis": (
                        readiness.return_arrangement_basis_label
                    ),
                    "return_arrangement_accepted": (
                        "Yes"
                        if readiness.return_arrangement_basis_ready
                        else "No"
                    ),
                    "return_arrangement_status": (
                        readiness.return_arrangement_basis_status
                    ),
                    "status": readiness.proportioning_status,
                }
            )

        if hasattr(self._panel, "set_commit_proportioning_ready"):
            self._panel.set_commit_proportioning_ready(
                ready=readiness.return_arrangement_basis_ready,
                reason=readiness.proportioning_status,
            )
        # --------------------------------------------------
        # H-S20-F2 — Proportioning received Basic PS sections
        # Route-aware section-flow basis for all known sublegs.
        #
        # Preview/input basis only:
        # - no balancing
        # - no valve selection
        # - no pump sizing
        # - no pipe resizing
        # - branch take-off remains TBA
        # --------------------------------------------------
        # --------------------------------------------------
        # H-S29-G — route pressure authority first
        # --------------------------------------------------
        route_pressure_projection = None
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

        route_section_by_id = (
            self._route_pressure_section_contribution_by_id_v1(
                route_pressure_projection
            )
        )

        received_basic_ps_rows = []

        try:
            route_specs = self._build_basic_ps_route_specs_for_proportioning()

            for leg_id, subleg_id in route_specs:
                basic_ps_projection = build_basic_ps_readonly_projection_v1(
                    self._project_state,
                    leg_id=leg_id,
                    subleg_id=subleg_id,
                )

                built_rows = self._build_proportioning_basic_ps_sections(
                    basic_ps_projection,
                    route_section_by_id=route_section_by_id,
                )

                flow_basis_text = _hydronic_mass_flow_basis_text(
                    self._project_state,
                    basic_ps_projection,
                )

                for row in built_rows:
                    status = str(row.get("status", "") or "")
                    row["status"] = (
                        f"{status} | {flow_basis_text}"
                        if status
                        else flow_basis_text
                    )

                received_basic_ps_rows.extend(built_rows)

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

        if hasattr(self._panel, "set_route_pressure_preview_rows"):
            self._panel.set_route_pressure_preview_rows(route_pressure_rows)

        if hasattr(self._panel, "set_route_shortfall_preview_rows"):
            self._panel.set_route_shortfall_preview_rows(route_shortfall_rows)

        # --------------------------------------------------
        # H-S19-H — Direct vs reverse return comparison
        # --------------------------------------------------
        return_path_comparison_rows = []
        return_path_comparison_evidence_rows = []

        if getattr(self._project_state, "hydronic_topology", None) is not None:
            try:
                return_path_comparison_projection = (
                    build_circuit_return_path_comparison_v1(
                        self._project_state,
                    )
                )

                return_path_comparison_evidence_rows = list(
                    getattr(return_path_comparison_projection, "rows", ()) or ()
                )

                return_path_comparison_evidence_rows = list(
                    getattr(return_path_comparison_projection, "rows", ()) or ()
                )

                return_path_comparison_rows = (
                    self._build_return_path_comparison_rows(
                        return_path_comparison_projection
                    )
                )

                hs27c_display_evidence_rows = (
                    self._build_hs27c_return_comparison_evidence_rows(
                        return_path_comparison_rows
                    )
                )

                if hs27c_display_evidence_rows:
                    return_path_comparison_evidence_rows = (
                        hs27c_display_evidence_rows
                    )

                if not return_path_comparison_evidence_rows:
                    return_path_comparison_evidence_rows = return_path_comparison_rows

            except Exception as exc:
                print("[RETURN PATH COMPARISON ERROR]", repr(exc))

        if hasattr(self._panel, "set_return_path_comparison_rows"):
            self._panel.set_return_path_comparison_rows(
                return_path_comparison_rows
            )
        # --------------------------------------------------
        # Branch / proportioning summary
        # --------------------------------------------------
        proportioning_rows = build_branch_aware_route_summary_audit_v1(
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
        selected_route_trace_target = (
            self._selected_route_trace_target_from_route_pressure_projection(
                route_pressure_projection
            )
        )

        proportioning_schematic = build_proportioning_schematic_v1(
            self._project_state,
            selected_leg_id=selected_route_trace_target.get("leg_id"),
            selected_subleg_id=selected_route_trace_target.get("subleg_id"),
            selected_route_label=selected_route_trace_target.get("route_label"),
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

        # --------------------------------------------------
        # H-S26-I6 — restore scoped return-arrangement overrides
        # after target combos are populated.
        # --------------------------------------------------
        if hasattr(
                self._panel,
                "set_scoped_return_arrangement_acceptance_basis",
        ):
            intent = self._get_return_arrangement_acceptance_intent()

            if isinstance(intent, dict):
                leg_arrangements = dict(
                    intent.get("leg_arrangements", {}) or {}
                )
                subleg_arrangements = dict(
                    intent.get("subleg_arrangements", {}) or {}
                )
            else:
                leg_arrangements = dict(
                    getattr(intent, "leg_arrangements", {}) or {}
                )
                subleg_arrangements = dict(
                    getattr(intent, "subleg_arrangements", {}) or {}
                )

            self._panel.set_scoped_return_arrangement_acceptance_basis(
                leg_arrangements=leg_arrangements,
                subleg_arrangements=subleg_arrangements,
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
        # H-S25-F — Final Proportioning snapshot refresh
        # --------------------------------------------------
        # Some Proportioning preview tables depend on several row feeds:
        # received Basic PS sections, route Δp rows, shortfall rows, and
        # return comparison rows. Refresh once at the end of the adapter
        # pass so preliminary balancing previews see the complete snapshot.
        if hasattr(self._panel, "_refresh_proportioning_input_snapshot"):
            self._panel._refresh_proportioning_input_snapshot()

        # --------------------------------------------------
        # H-S27-B — resolved return arrangement basis feed
        # --------------------------------------------------
        self._refresh_effective_return_arrangement_basis_rows(
            return_path_comparison_rows=return_path_comparison_evidence_rows,
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

    # --------------------------------------------------
    # H-S27-B — Proportioned resolved return-arrangement basis rows
    # --------------------------------------------------
    @staticmethod
    def _return_arrangement_basis_display_label(basis: object) -> str:
        basis = str(basis or "").strip().upper()

        if basis == "DIRECT_RETURN":
            return "F&R"

        if basis == "REVERSE_RETURN":
            return "F+RR"

        if basis == "INHERIT":
            return "Inherit"

        if basis == "UNDECIDED":
            return "Undecided"

        return basis or "—"

    @staticmethod
    def _return_arrangement_scope_display_label(scope: object) -> str:
        scope = str(scope or "").strip().upper()

        return {
            "SYSTEM": "System",
            "LEG": "Leg",
            "COMMON_SUBLEG": "Common",
            "BRANCH_SUBLEG": "Branch",
        }.get(scope, scope or "—")


    @staticmethod
    def _hs27c_row_value(row, *keys):
        if isinstance(row, dict):
            for key in keys:
                if key in row:
                    return row.get(key)
            return None

        for key in keys:
            if hasattr(row, key):
                return getattr(row, key)

        return None

    @staticmethod
    def _hs27c_parse_pa_text(value):
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text or text == "—":
            return None

        lowered = text.lower().replace(",", "").strip()

        factor = 1.0
        if "kpa" in lowered:
            factor = 1000.0
            lowered = lowered.replace("kpa", "")
        else:
            lowered = lowered.replace("pa", "")

        lowered = lowered.strip()

        try:
            return float(lowered) * factor
        except (TypeError, ValueError):
            return None

    def _build_hs27c_return_comparison_evidence_rows(
            self,
            return_path_comparison_rows,
    ) -> list[dict]:
        """
        H-S27-C:
        Normalise the visible H-S19 F+R / F+RR comparison table rows into
        numeric route pressure evidence for chosen-basis preview.

        This deliberately consumes the same display-row source seen by the
        user in the Proportioning comparison table.
        """
        evidence_rows: list[dict] = []

        for row in list(return_path_comparison_rows or ()):
            route_id = self._hs27c_row_value(
                row,
                "route_id",
                "route_key",
                "target_id",
            )
            subleg_id = self._hs27c_row_value(
                row,
                "subleg_id",
            )
            route_label = self._hs27c_row_value(
                row,
                "route",
                "route_label",
                "target_label",
            )

            direct_dp = self._hs27c_parse_pa_text(
                self._hs27c_row_value(
                    row,
                    "direct_total_dp",
                    "direct_route_dp",
                    "direct_dp",
                    "f_r_dp",
                    "f_plus_r_dp",
                    "flow_return_dp",
                )
            )

            reverse_dp = self._hs27c_parse_pa_text(
                self._hs27c_row_value(
                    row,
                    "reverse_total_dp",
                    "reverse_route_dp",
                    "reverse_dp",
                    "f_plus_rr_dp",
                    "f_rr_dp",
                    "reverse_return_dp",
                )
            )

            if direct_dp is None and reverse_dp is None:
                continue

            evidence_rows.append(
                {
                    "route_id": str(route_id or ""),
                    "subleg_id": str(subleg_id or ""),
                    "route": str(route_label or route_id or subleg_id or "—"),
                    "route_label": str(route_label or route_id or subleg_id or "—"),
                    "direct_dp_pa": direct_dp,
                    "reverse_dp_pa": reverse_dp,
                }
            )

        return evidence_rows


    def _build_effective_return_arrangement_basis_rows(
            self,
            resolution,
    ) -> list[dict]:
        """
        H-S27-B:
        Convert effective return-arrangement resolver output into compact
        Proportioned-tab display rows.

        Adapter only:
            no mutation
            no balancing
            no pump / valve / pipe resize
        """
        rows: list[dict] = []

        for row in list(getattr(resolution, "rows", ()) or ()):
            rows.append(
                {
                    "scope": self._return_arrangement_scope_display_label(
                        getattr(row, "scope", "")
                    ),
                    "target": str(getattr(row, "label", "") or "—"),
                    "effective_basis": self._return_arrangement_basis_display_label(
                        getattr(row, "effective_basis", "")
                    ),
                    "source": str(getattr(row, "source", "") or "—"),
                    "status": str(getattr(row, "status", "") or "—"),
                }
            )

        if not rows:
            rows.append(
                {
                    "scope": "—",
                    "target": "—",
                    "effective_basis": "—",
                    "source": "—",
                    "status": str(
                        getattr(
                            resolution,
                            "status",
                            "No resolved return arrangement basis",
                        )
                    ),
                }
            )

        return rows

    def _build_chosen_basis_route_pressure_preview_rows(
            self,
            preview_rows,
    ) -> list[dict]:
        """
        H-S27-C:
        Convert chosen-basis route Δp preview rows into Proportioned-tab
        display rows.

        Read-only projection:
            no mutation
            no balancing
            no pump / valve / pipe resize
            no final hydraulic result
        """
        rows: list[dict] = []

        for row in list(preview_rows or ()):
            status = str(getattr(row, "status", "") or "—")

            # H-S27-C is route/subleg evidence only.
            # Skip system/leg rows if backend received them but no pressure
            # evidence exists for them.
            if (
                    getattr(row, "chosen_dp_pa", None) is None
                    and getattr(row, "alternative_dp_pa", None) is None
                    and "missing return comparison evidence" in status.lower()
            ):
                continue

            rows.append(
                {
                    "scope": self._return_arrangement_scope_display_label(
                        getattr(row, "scope", "")
                    ),
                    "route": str(getattr(row, "route", "") or "—"),
                    "basis": str(getattr(row, "basis", "") or "—"),
                    "chosen_dp": self._format_pa(
                        getattr(row, "chosen_dp_pa", None)
                    ),
                    "alternative_dp": self._format_pa(
                        getattr(row, "alternative_dp_pa", None)
                    ),
                    "difference": self._format_signed_pa(
                        getattr(row, "difference_pa", None)
                    ),
                    "source": str(getattr(row, "source", "") or "—"),
                    "status": status,
                }
            )

        if not rows:
            rows.append(
                {
                    "scope": "—",
                    "route": "—",
                    "basis": "—",
                    "chosen_dp": "—",
                    "alternative_dp": "—",
                    "difference": "—",
                    "source": "—",
                    "status": "Preview only — no chosen-basis route pressure evidence",
                }
            )

        return rows
    def _build_chosen_basis_controlling_route_preview_rows(
            self,
            preview_rows,
    ) -> list[dict]:
        """
        H-S27-D:
        Convert chosen-basis controlling route preview rows into
        Proportioned-tab display rows.

        Read-only projection:
            no mutation
            no balancing
            no pump / valve selection
            no pipe resize
            no final hydraulic result
        """
        rows: list[dict] = []

        for row in list(preview_rows or ()):
            rows.append(
                {
                    "scope": self._return_arrangement_scope_display_label(
                        getattr(row, "scope", "")
                    ),
                    "route": str(getattr(row, "route", "") or "—"),
                    "basis": str(getattr(row, "basis", "") or "—"),
                    "chosen_dp": self._format_pa(
                        getattr(row, "chosen_dp_pa", None)
                    ),
                    "controlling": (
                        "Yes"
                        if getattr(row, "is_controlling", False)
                        else "No"
                    ),
                    "dp_below_controlling": self._format_pa(
                        getattr(row, "dp_below_controlling_pa", None)
                    ),
                    "source": str(getattr(row, "source", "") or "—"),
                    "status": str(getattr(row, "status", "") or "—"),
                }
            )

        if not rows:
            rows.append(
                {
                    "scope": "—",
                    "route": "—",
                    "basis": "—",
                    "chosen_dp": "—",
                    "controlling": "No",
                    "dp_below_controlling": "—",
                    "source": "—",
                    "status": (
                        "Preview only — no chosen-basis controlling route evidence"
                    ),
                }
            )

        return rows

    def _build_chosen_basis_proportioned_readiness_rows(
            self,
            readiness_rows,
    ) -> list[dict]:
        """
        H-S27-F:
        Convert chosen-basis proportioned readiness summary rows into
        Proportioned-tab display rows.

        Read-only projection:
            no mutation
            no balancing
            no pump / valve / pipe resize
            no final hydraulic result
        """
        rows: list[dict] = []

        for row in readiness_rows or ():
            rows.append(
                {
                    "item": str(getattr(row, "item", "—")),
                    "status": str(getattr(row, "status", "—")),
                }
            )

        if not rows:
            rows.append(
                {
                    "item": "Chosen-basis proportioned readiness",
                    "status": "Not ready — no readiness evidence",
                }
            )

        return rows

    def _build_proportioned_output_status_rows_v1(
            self,
            *,
            resolution,
            chosen_preview_rows,
            chosen_controlling_rows,
            readiness_rows,
    ) -> list[dict]:
        """
        H-S30-A:
        Build the top Proportioned-tab output status rows.

        Read-only output preview:
            no pump selection
            no valve selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        project = getattr(self, "_project_state", None)
        snapshot = getattr(
            project,
            "hydronic_proportioned_basis_snapshot",
            None,
        )

        resolved_rows = tuple(getattr(resolution, "rows", ()) or ())
        chosen_preview_rows = tuple(chosen_preview_rows or ())
        chosen_controlling_rows = tuple(chosen_controlling_rows or ())
        readiness_rows = tuple(readiness_rows or ())

        if snapshot is not None:
            basis = str(
                getattr(snapshot, "return_arrangement_basis", "—")
                or "—"
            )
            accepted_basis_status = (
                f"Committed basis snapshot: {basis} — basis only; "
                "final hydraulics not committed"
            )
        elif resolved_rows:
            accepted_basis_status = (
                "Read-only preview available — accepted basis resolved; "
                "not a final hydraulic result"
            )
        else:
            accepted_basis_status = (
                "Waiting for accepted return-arrangement basis"
            )

        route_pressure_status = (
            "Chosen-basis route Δp evidence available — preview only"
            if chosen_preview_rows
            else "Waiting for chosen-basis route pressure evidence"
        )

        has_controlling = any(
            bool(getattr(row, "is_controlling", False))
            for row in chosen_controlling_rows
        )

        controlling_status = (
            "Controlling route / shortfall evidence available — preview only"
            if has_controlling
            else "Waiting for controlling route / shortfall evidence"
        )

        readiness_status = (
            "Readiness evidence available — see readiness table"
            if readiness_rows
            else "Waiting for chosen-basis readiness evidence"
        )

        return [
            {
                "item": "Accepted return basis",
                "status": accepted_basis_status,
            },
            {
                "item": "Route pressure evidence",
                "status": route_pressure_status,
            },
            {
                "item": "Controlling / shortfall evidence",
                "status": controlling_status,
            },
            {
                "item": "Chosen-basis readiness",
                "status": readiness_status,
            },
            {
                "item": "Final hydraulic actions",
                "status": (
                    "Pump, valve selection, final balancing, and pipe "
                    "resizing not performed"
                ),
            },
            {
                "item": "Final output",
                "status": (
                    "Not committed — Proportioned tab is read-only output "
                    "preview at this stage"
                ),
            },
        ]

    def _refresh_effective_return_arrangement_basis_rows(
            self,
            return_path_comparison_rows=None,
    ) -> None:
        """
        H-S27-B / H-S27-C / H-S27-D / H-S27-F:
        Feed Proportioned-tab resolved return-arrangement basis,
        chosen-basis route Δp preview, chosen-basis controlling route
        preview, and chosen-basis readiness summary.

        Read-only projection:
            no mutation
            no balancing
            no pump / valve / pipe resize
            no final hydraulic result
        """
        has_resolved_table = hasattr(
            self._panel,
            "set_effective_return_arrangement_basis_rows",
        )
        has_chosen_table = hasattr(
            self._panel,
            "set_chosen_basis_route_pressure_preview_rows",
        )
        has_controlling_table = hasattr(
            self._panel,
            "set_chosen_basis_controlling_route_preview_rows",
        )
        has_readiness_table = hasattr(
            self._panel,
            "set_chosen_basis_proportioned_readiness_rows",
        )
        has_proportioned_status_table = hasattr(
            self._panel,
            "set_proportioned_status",
        )

        if (
                not has_resolved_table
                and not has_chosen_table
                and not has_controlling_table
                and not has_readiness_table
                and not has_proportioned_status_table
        ):
            return

        try:
            resolution = resolve_effective_return_arrangements_v1(
                self._project_state
            )

            if has_resolved_table:
                self._panel.set_effective_return_arrangement_basis_rows(
                    self._build_effective_return_arrangement_basis_rows(
                        resolution
                    )
                )

            chosen_preview_rows = build_chosen_basis_route_pressure_preview_v1(
                resolved_basis_rows=getattr(resolution, "rows", ()) or (),
                return_comparison_rows=return_path_comparison_rows or (),
            )

            if has_chosen_table:
                self._panel.set_chosen_basis_route_pressure_preview_rows(
                    self._build_chosen_basis_route_pressure_preview_rows(
                        chosen_preview_rows
                    )
                )

            chosen_controlling_rows = (
                build_chosen_basis_controlling_route_preview_v1(
                    chosen_preview_rows
                )
            )

            if has_controlling_table:
                self._panel.set_chosen_basis_controlling_route_preview_rows(
                    self._build_chosen_basis_controlling_route_preview_rows(
                        chosen_controlling_rows
                    )
                )

            readiness_rows = (
                build_chosen_basis_proportioned_readiness_summary_v1(
                    has_resolved_return_arrangement_basis=bool(
                        getattr(resolution, "rows", ()) or ()
                    ),
                    has_chosen_route_pressure_evidence=bool(
                        chosen_preview_rows
                    ),
                    has_chosen_basis_controlling_route=any(
                        bool(getattr(row, "is_controlling", False))
                        for row in chosen_controlling_rows or ()
                    ),
                    has_chosen_basis_shortfall_preview=bool(
                        chosen_controlling_rows
                    ),
                )
            )

            if has_readiness_table:
                self._panel.set_chosen_basis_proportioned_readiness_rows(
                    self._build_chosen_basis_proportioned_readiness_rows(
                        readiness_rows
                    )
                )

            if has_proportioned_status_table:
                self._panel.set_proportioned_status(
                    self._build_proportioned_output_status_rows_v1(
                        resolution=resolution,
                        chosen_preview_rows=chosen_preview_rows,
                        chosen_controlling_rows=chosen_controlling_rows,
                        readiness_rows=readiness_rows,
                    )
                )

        except Exception as exc:
            print(
                "[H-S27-B/C/D/F RETURN ARRANGEMENT PREVIEW ERROR]",
                repr(exc),
            )

            if has_resolved_table:
                self._panel.set_effective_return_arrangement_basis_rows([])

            if has_chosen_table:
                self._panel.set_chosen_basis_route_pressure_preview_rows([])

            if has_controlling_table:
                self._panel.set_chosen_basis_controlling_route_preview_rows([])

            if has_readiness_table:
                self._panel.set_chosen_basis_proportioned_readiness_rows([])

            if has_proportioned_status_table:
                self._panel.set_proportioned_status(
                    [
                        {
                            "item": "Proportioned output preview",
                            "status": (
                                "Preview unavailable — return-arrangement "
                                "evidence refresh failed"
                            ),
                        },
                        {
                            "item": "Final output",
                            "status": "Not committed",
                        },
                    ]
                )

    def set_scoped_return_arrangement_acceptance(
            self,
            scope_key: str,
            target_id: str,
            target_label: str,
            basis: str,
    ) -> None:
        """
        Persist leg/subleg return-arrangement overrides.

        Meaning:
            INHERIT removes the override.
            DIRECT_RETURN stores F&R.
            REVERSE_RETURN stores F+RR.

        Design-basis intent only:
            • no room/subleg exclusion
            • no balancing
            • no pump selection
            • no valve selection
            • no pipe resizing
            • no final Proportioned result
        """
        scope_key = str(scope_key or "").strip().upper()
        target_id = str(target_id or "").strip()
        target_label = str(target_label or "").strip()
        basis = str(basis or "").strip().upper()

        if basis not in {
                "INHERIT",
                "DIRECT_RETURN",
                "REVERSE_RETURN",
        }:
            basis = "INHERIT"

        if scope_key not in {
                "LEG",
                "COMMON_SUBLEG",
                "BRANCH_SUBLEG",
        }:
            print(
                "H-S26-I5 warning: unknown return-arrangement scope:",
                repr(scope_key),
            )
            return

        if not target_id:
            print(
                "H-S26-I5 warning: missing target id for scoped "
                f"return-arrangement scope {scope_key!r}"
            )
            return

        intent = self._get_return_arrangement_acceptance_intent()

        if scope_key == "LEG":
            field_name = "leg_arrangements"
        else:
            field_name = "subleg_arrangements"

        if isinstance(intent, dict):
            next_intent = dict(intent)
            override_map = dict(next_intent.get(field_name, {}) or {})

            if basis == "INHERIT":
                override_map.pop(target_id, None)
            else:
                override_map[target_id] = basis

            next_intent[field_name] = override_map
            self._return_arrangement_acceptance_intent = next_intent

        else:
            from dataclasses import replace

            override_map = dict(
                getattr(intent, field_name, {}) or {}
            )

            if basis == "INHERIT":
                override_map.pop(target_id, None)
            else:
                override_map[target_id] = basis

            try:
                self._return_arrangement_acceptance_intent = replace(
                    intent,
                    **{field_name: override_map},
                )
            except TypeError:
                setattr(intent, field_name, override_map)
                self._return_arrangement_acceptance_intent = intent

        project = getattr(self, "_project_state", None)
        if project is not None:
            project.hydronic_return_arrangement_intent = (
                self._return_arrangement_acceptance_intent
            )

        print(
            "H-S26-I5 scoped return arrangement persisted:",
            scope_key,
            target_label or target_id,
            "=>",
            basis,
        )

        self.refresh()

    def _build_common_main_leg_subleg_schematic(
            self,
            topology,
    ) -> CommonMainLegSublegSchematicV1:
        """
        H-S26-G2:
        Build display-only common-main / leg / subleg schematic.

        Branch sublegs are attached to a parent/common subleg take-off marker,
        not drawn as if they originate directly from the leg.

        Branch take-off location remains TBA.
        """
        routes: list[CommonMainLegSublegRouteV1] = []

        for leg in getattr(topology, "legs", []) or []:
            leg_id = str(getattr(leg, "leg_id", "") or "")

            raw_leg_label = str(
                getattr(leg, "label", None)
                or getattr(leg, "name", None)
                or leg_id
                or "Leg"
            )

            leg_label = self._display_leg_label(raw_leg_label)

            leg_sublegs = list(getattr(leg, "sublegs", []) or [])

            primary_subleg = self._primary_subleg_for_display(leg_sublegs)

            primary_subleg_id = ""
            primary_subleg_label = ""

            if primary_subleg is not None:
                primary_subleg_id = str(
                    getattr(primary_subleg, "subleg_id", "") or ""
                )
                primary_subleg_label = self._display_subleg_label(
                    str(
                        getattr(primary_subleg, "label", None)
                        or getattr(primary_subleg, "name", None)
                        or primary_subleg_id
                        or "Primary subleg"
                    )
                )

            def add_subleg_tree(
                    sublegs,
                    *,
                    parent_subleg_id: str = "",
                    parent_subleg_label: str = "",
            ) -> None:
                for subleg in list(sublegs or []):
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

                    role_label = self._subleg_role_label(subleg)
                    role_lower = role_label.lower()

                    is_primary = (
                        "primary-subleg" in subleg_id
                        or (
                            "common" in role_lower
                            and "branch" not in role_lower
                        )
                    )

                    effective_parent_id = str(parent_subleg_id or "")
                    effective_parent_label = str(parent_subleg_label or "")

                    # Some current topology versions hold branch sublegs as
                    # leg-level siblings rather than true nested children.
                    # For display, attach those branches to the leg primary /
                    # common subleg if available.
                    if (
                            not effective_parent_id
                            and not is_primary
                            and primary_subleg_id
                            and subleg_id != primary_subleg_id
                    ):
                        effective_parent_id = primary_subleg_id
                        effective_parent_label = primary_subleg_label

                    is_branch = bool(effective_parent_id)

                    room_labels = tuple(
                        self._subleg_room_ids_for_display(subleg)
                    )

                    routes.append(
                        CommonMainLegSublegRouteV1(
                            leg_id=leg_id,
                            leg_label=leg_label,
                            subleg_id=subleg_id,
                            subleg_label=subleg_label,
                            role=role_label,
                            room_labels=room_labels,
                            parent_subleg_id=effective_parent_id,
                            parent_subleg_label=effective_parent_label,
                            parent_takeoff_label=(
                                "Branch take-off — TBA"
                                if is_branch
                                else ""
                            ),
                            is_branch_subleg=is_branch,
                        )
                    )

                    child_sublegs = list(
                        getattr(subleg, "sublegs", ()) or ()
                    )

                    if child_sublegs:
                        add_subleg_tree(
                            child_sublegs,
                            parent_subleg_id=subleg_id,
                            parent_subleg_label=subleg_label,
                        )

            add_subleg_tree(leg_sublegs)

        return CommonMainLegSublegSchematicV1(
            heat_source_label="Boiler",
            common_main_label="Common main",
            routes=tuple(routes),
            status=(
                "DEV topology schematic preview only — branch take-offs are "
                "display-only TBA markers; no pressure, balancing, pump, "
                "valve, or pipe-resize result"
            ),
        )

    @staticmethod
    def _primary_subleg_for_display(sublegs):
        """
        H-S26-G2:
        Find the common/primary subleg used as the display parent for
        branch sublegs whose explicit parent is not yet modelled.
        """
        sublegs = list(sublegs or [])

        for subleg in sublegs:
            subleg_id = str(getattr(subleg, "subleg_id", "") or "")

            if "primary-subleg" in subleg_id:
                return subleg

        for subleg in sublegs:
            raw_label = str(
                getattr(subleg, "label", None)
                or getattr(subleg, "name", None)
                or ""
            ).lower()

            if "common" in raw_label and "branch" not in raw_label:
                return subleg

        return sublegs[0] if sublegs else None

    def _build_basic_ps_route_specs_for_proportioning(self) -> list[tuple[str, str]]:
        """
        H-S20-F2:
        Build route-aware Basic PS projection specs for Proportioning.

        Preview/input basis only:
        - no balancing
        - no valve selection
        - no pump sizing
        - no pipe resizing
        - branch take-off position remains TBA
        """
        project_state = self._project_state
        topology = getattr(project_state, "hydronic_topology", None)

        specs: list[tuple[str, str]] = []

        def add_subleg_tree(leg_id: str, sublegs: list) -> None:
            for subleg in sublegs or []:
                subleg_id = str(getattr(subleg, "subleg_id", "") or "")
                room_ids = list(getattr(subleg, "route_room_ids", ()) or ())

                if leg_id and subleg_id and room_ids:
                    specs.append((leg_id, subleg_id))

                child_sublegs = list(getattr(subleg, "sublegs", ()) or ())
                if child_sublegs:
                    add_subleg_tree(leg_id, child_sublegs)

        for leg in list(getattr(topology, "legs", ()) or ()):
            leg_id = str(getattr(leg, "leg_id", "") or "")
            add_subleg_tree(
                leg_id,
                list(getattr(leg, "sublegs", ()) or ()),
            )

        # Deterministic order:
        # leg-001 primary, leg-001 branch, leg-002 primary, leg-002 branch...
        def _sort_key(item: tuple[str, str]) -> tuple[str, int, str]:
            leg_id, subleg_id = item
            is_branch = 0 if "primary-subleg" in subleg_id else 1
            return (leg_id, is_branch, subleg_id)

        unique_specs = sorted(set(specs), key=_sort_key)

        if unique_specs:
            return unique_specs

        # Safe fallback for older/incomplete topology.
        return [("leg-001", "leg-001-primary-subleg")]

    @staticmethod
    def _route_pressure_section_contribution_by_id_v1(
        projection,
    ) -> dict[str, object]:
        """
        H-S29-G:
        Map route-pressure section contributions by section_id so the
        Proportioning received-section preview can display the same
        Colebrook-backed pressure metadata as the route accumulator.

        Display/projection only:
        - no ProjectState mutation
        - no recalculation
        - no pipe resizing
        - no final balancing
        """
        by_id: dict[str, object] = {}

        if projection is None:
            return by_id

        for route_row in getattr(projection, "rows", ()) or ():
            for section in getattr(route_row, "sections", ()) or ():
                section_id = str(getattr(section, "section_id", "") or "")

                if section_id:
                    by_id[section_id] = section

        return by_id


    @staticmethod
    def _selected_route_trace_target_from_route_pressure_projection(
        projection,
    ) -> dict:
        """
        H-S25-E:
        Resolve the selected route trace target from route-pressure authority.

        Default rule:
        - use the controlling route candidate
        - return leg/subleg identity for the selected route trace schematic
        - no ProjectState mutation
        - no pressure calculation
        """

        if projection is None:
            return {}

        rows = list(getattr(projection, "rows", ()) or ())

        for row in rows:
            if getattr(row, "is_controlling_candidate", False):
                return {
                    "route_id": str(getattr(row, "route_id", "") or ""),
                    "route_label": str(getattr(row, "route_label", "") or ""),
                    "leg_id": str(getattr(row, "leg_id", "") or ""),
                    "subleg_id": str(getattr(row, "subleg_id", "") or ""),
                }

        return {}

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
                    "route_id": getattr(row, "route_id", ""),
                    "route_label": getattr(row, "route_label", ""),
                    "leg_id": getattr(row, "leg_id", ""),
                    "subleg_id": getattr(row, "subleg_id", ""),
                }
            )

        return rows

    def _build_return_path_comparison_rows(self, projection) -> list[dict]:
        rows: list[dict] = []

        for row in getattr(projection, "rows", ()) or ():
            route_id = str(getattr(row, "route_id", "") or "")
            route_parts = route_id.split(":", 1)

            leg_id = str(
                getattr(row, "leg_id", None)
                or (route_parts[0] if route_parts else "")
                or ""
            )

            subleg_id = str(
                getattr(row, "subleg_id", None)
                or (route_parts[1] if len(route_parts) > 1 else "")
                or ""
            )

            room_id = str(getattr(row, "room_id", "") or "")
            emitter_id = str(getattr(row, "emitter_id", "") or "")
            route_id = str(getattr(row, "route_id", "") or "")
            route_parts = route_id.split(":", 1)

            leg_id = str(
                getattr(row, "leg_id", None)
                or (route_parts[0] if route_parts else "")
                or ""
            )

            subleg_id = str(
                getattr(row, "subleg_id", None)
                or (route_parts[1] if len(route_parts) > 1 else "")
                or ""
            )

            room_id = str(getattr(row, "room_id", "") or "")
            emitter_id = str(getattr(row, "emitter_id", "") or "")
            rows.append(
                {
                    "route_id": route_id,
                    "leg_id": leg_id,
                    "subleg_id": subleg_id,
                    "room_id": room_id,
                    "emitter_id": emitter_id,
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
                    "rr_added_length": self._format_length(
                        getattr(row, "rr_added_length_m", None)
                    ),
                    "rr_added_dp": self._format_pa(
                        getattr(row, "rr_added_pressure_drop_Pa", None)
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

    def _build_proportioning_basic_ps_sections(
        self,
        projection,
        *,
        route_section_by_id: dict[str, object] | None = None,
    ) -> list[dict]:
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
        route_section_by_id = route_section_by_id or {}

        section_by_id = {
            str(getattr(section, "section_id", "") or ""): section
            for section in getattr(
                projection.sections_projection,
                "sections",
                (),
            ) or ()
            if str(getattr(section, "section_id", "") or "")
        }

        for result in projection.pipe_sizing_projection.results:
            section_id = str(getattr(result, "section_id", "") or "")
            preview = preview_by_section_id.get(section_id)
            topology_section = section_by_id.get(section_id)
            route_section = route_section_by_id.get(section_id)
            pressure_source = route_section if route_section is not None else result

            raw_basis_status = str(
                getattr(topology_section, "status", "") or ""
            )
            section_basis_status = (
                ""
                if raw_basis_status in {"", "—", "Projection only"}
                else raw_basis_status
            )

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
                    getattr(pressure_source, "velocity_m_s", 0.0) or 0.0
                ),
                pressure_gradient_Pa_per_m=float(
                    getattr(
                        pressure_source,
                        "pressure_gradient_Pa_per_m",
                        getattr(result, "pressure_gradient_Pa_per_m", 0.0),
                    ) or 0.0
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
                section_basis_status,
                str(getattr(result, "status", "") or ""),
                str(preview_status or ""),
                str(local_k_preview.status or ""),
            ]
            status = " / ".join(
                part for part in status_parts if part and part != "—"
            ) or "—"
            route_label = (
                f"{projection.sections_projection.leg_label} / "
                f"{projection.sections_projection.subleg_label}"
            )

            leg_id = str(getattr(result, "leg_id", "") or "")
            subleg_id = str(getattr(result, "subleg_id", "") or "")

            subleg_role = (
                "common"
                if "primary-subleg" in subleg_id
                else "branch"
                if "subleg" in subleg_id
                else ""
            )

            takeoff_status = "TBA" if subleg_role == "branch" else ""
            rows.append(
                {
                    "leg_id": leg_id,
                    "subleg_id": subleg_id,
                    "route_id": subleg_id,
                    "route": route_label,
                    "subleg_role": subleg_role,
                    "takeoff_status": takeoff_status,
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
                        getattr(pressure_source, "velocity_m_s", None)
                    ),
                    "dp_per_m": self._format_dp_per_m(
                        getattr(
                            pressure_source,
                            "pressure_gradient_Pa_per_m",
                            getattr(result, "pressure_gradient_Pa_per_m", None),
                        )
                    ),
                    "reynolds_number": self._format_reynolds_number(
                        getattr(
                            pressure_source,
                            "reynolds_number",
                            getattr(result, "reynolds_number", None),
                        )
                    ),
                    "friction_factor": self._format_friction_factor(
                        getattr(
                            pressure_source,
                            "friction_factor",
                            getattr(result, "friction_factor", None),
                        )
                    ),
                    "friction_method": str(
                        getattr(
                            pressure_source,
                            "friction_method",
                            getattr(result, "friction_method", "Haaland"),
                        ) or "Haaland"
                    ),
                    "colebrook_iterations": str(
                        getattr(
                            pressure_source,
                            "colebrook_iteration_count",
                            getattr(result, "colebrook_iteration_count", "—"),
                        ) or "—"
                    ),
                    "colebrook_converged": (
                        "Yes"
                        if bool(
                            getattr(
                                pressure_source,
                                "colebrook_converged",
                                getattr(result, "colebrook_converged", False),
                            )
                        )
                        else "—"
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
        """
        H-S26-G2:
        Display rows for common-main / leg / subleg topology, including
        branch parent/take-off meaning.

        Display only:
        • no ProjectState mutation
        • no pressure calculation
        • no pipe sizing
        • no balancing
        """
        rows: list[dict] = []

        for leg in getattr(topology, "legs", []) or []:
            leg_id = str(getattr(leg, "leg_id", "") or "")

            raw_leg_label = str(
                getattr(leg, "label", None)
                or getattr(leg, "name", None)
                or leg_id
                or "Leg"
            )

            leg_label = self._display_leg_label(raw_leg_label)
            leg_sublegs = list(getattr(leg, "sublegs", []) or [])

            primary_subleg = self._primary_subleg_for_display(leg_sublegs)

            primary_subleg_id = ""
            primary_subleg_label = ""

            if primary_subleg is not None:
                primary_subleg_id = str(
                    getattr(primary_subleg, "subleg_id", "") or ""
                )
                primary_subleg_label = self._display_subleg_label(
                    str(
                        getattr(primary_subleg, "label", None)
                        or getattr(primary_subleg, "name", None)
                        or primary_subleg_id
                        or "Primary subleg"
                    )
                )

            def add_rows(
                    sublegs,
                    *,
                    parent_subleg_id: str = "",
                    parent_subleg_label: str = "",
            ) -> None:
                for subleg in list(sublegs or []):
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

                    role_label = self._subleg_role_label(subleg)
                    role_lower = role_label.lower()

                    is_primary = (
                        "primary-subleg" in subleg_id
                        or (
                            "common" in role_lower
                            and "branch" not in role_lower
                        )
                    )

                    effective_parent_id = str(parent_subleg_id or "")
                    effective_parent_label = str(parent_subleg_label or "")

                    if (
                            not effective_parent_id
                            and not is_primary
                            and primary_subleg_id
                            and subleg_id != primary_subleg_id
                    ):
                        effective_parent_id = primary_subleg_id
                        effective_parent_label = primary_subleg_label

                    is_branch = bool(effective_parent_id)

                    room_ids = self._subleg_room_ids_for_display(subleg)
                    rooms_label = " → ".join(room_ids) if room_ids else "—"

                    rows.append(
                        {
                            "common_main": "Common main",
                            "leg_id": leg_id,
                            "leg": leg_label,
                            "subleg_id": subleg_id,
                            "subleg": subleg_label,
                            "parent_subleg_id": effective_parent_id,
                            "parent_subleg": (
                                effective_parent_label if is_branch else "—"
                            ),
                            "role": role_label,
                            "rooms": rooms_label,
                            "status": (
                                "Branch take-off — TBA from parent/common "
                                "subleg"
                                if is_branch
                                else (
                                    "DEV topology preview — common main feeds "
                                    "leg; leg feeds common/primary subleg"
                                )
                            ),
                        }
                    )

                    child_sublegs = list(
                        getattr(subleg, "sublegs", ()) or ()
                    )

                    if child_sublegs:
                        add_rows(
                            child_sublegs,
                            parent_subleg_id=subleg_id,
                            parent_subleg_label=subleg_label,
                        )

            add_rows(leg_sublegs)

        return rows

    @staticmethod
    def _format_reynolds_number(value) -> str:
        if value is None:
            return "—"

        try:
            return f"{float(value):.0f}"
        except (TypeError, ValueError):
            return "—"

    @staticmethod
    def _format_friction_factor(value) -> str:
        if value is None:
            return "—"

        try:
            return f"{float(value):.4f}"
        except (TypeError, ValueError):
            return "—"

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

    @staticmethod
    def _format_signed_pa(value) -> str:
        if value is None:
            return "—"

        try:
            value = float(value)
        except (TypeError, ValueError):
            return "—"

        return f"{value:+.1f} Pa"

    @staticmethod
    def _format_signed_pa(value) -> str:
        if value is None:
            return "—"

        try:
            value = float(value)
        except (TypeError, ValueError):
            return "—"

        return f"{value:+.1f} Pa"

    # --------------------------------------------------
    # H-S26-D — ProjectState-backed return arrangement acceptance intent
    # --------------------------------------------------
    def _get_return_arrangement_acceptance_intent(self):
        """
        H-S26-D:
        Return the persisted ProjectState-backed return arrangement intent.

        Persistence only:
        • no balancing
        • no valve selection
        • no pump sizing
        • no pipe resizing
        • no final Proportioned commit
        • no automatic choice from F+R / F+RR evidence
        """
        from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
            ReturnArrangementIntentV1,
        )

        project = getattr(self, "_project_state", None)

        intent = getattr(
            project,
            "hydronic_return_arrangement_intent",
            None,
        )

        if intent is None:
            intent = ReturnArrangementIntentV1()

            if project is not None:
                project.hydronic_return_arrangement_intent = intent

        self._return_arrangement_acceptance_intent = intent

        return intent

    # --------------------------------------------------
    # H-S26-C — User accepted system return arrangement basis
    # --------------------------------------------------
    def commit_proportioning_basis_snapshot(self) -> None:
        """
        H-S26-G:
        Commit a frozen accepted proportioning-basis snapshot.

        This writes a basis-only snapshot to ProjectState.

        It does not:
        • select a pump
        • select valves
        • resize pipes
        • mutate balancing
        • create a final hydraulic Proportioned result
        """

        project = getattr(self, "_project_state", None)

        if project is None:
            print(
                "H-S26-G Commit Proportioning blocked: "
                "no ProjectState is available"
            )
            return

        result = build_proportioned_basis_snapshot_v1(project)

        if not result.ready or result.snapshot is None:
            if hasattr(self._panel, "set_commit_proportioning_ready"):
                self._panel.set_commit_proportioning_ready(
                    ready=False,
                    reason=result.status,
                )

            print(
                "H-S26-G Commit Proportioning blocked:",
                result.status,
            )
            return

        project.hydronic_proportioned_basis_snapshot = result.snapshot

        print(
            "H-S26-G committed proportioning basis snapshot:",
            result.snapshot.return_arrangement_basis,
        )

        self.refresh()

    def set_system_return_arrangement_acceptance(self, basis: str) -> None:
        """
        User-facing acceptance only.

        This does not persist to ProjectState.
        This does not commit final Proportioned state.
        This does not use F+R/F+RR comparison to auto-select a basis.
        """

        from dataclasses import replace

        from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
            DIRECT_RETURN,
            REVERSE_RETURN,
            UNDECIDED,
        )

        basis = str(basis or "").strip().upper()

        if basis not in {UNDECIDED, DIRECT_RETURN, REVERSE_RETURN}:
            basis = UNDECIDED

        intent = self._get_return_arrangement_acceptance_intent()

        try:
            self._return_arrangement_acceptance_intent = replace(
                intent,
                system_arrangement=basis,
            )
        except TypeError:
            intent.system_arrangement = basis
            self._return_arrangement_acceptance_intent = intent

        project = getattr(self, "_project_state", None)
        if project is not None:
            project.hydronic_return_arrangement_intent = (
                self._return_arrangement_acceptance_intent
            )

        else:
            print(
                "H-S26-D warning: no ProjectState available for return arrangement intent"
            )

        self.refresh()

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
        Convert branch-aware route authority audit rows into the existing
        Branch / proportioning summary table slot.

        H-S25-B:
        This table now surfaces the branch-aware topology authority audit.
        The older H-R1 index-route summary remains as backend evidence but
        is no longer the primary branch authority table in Proportioning.
        """

        source_rows = getattr(rows, "rows", rows) or []

        out: list[dict] = []

        for row in source_rows:
            if hasattr(row, "takeoff_classification"):
                q_label = self._format_watts(
                    getattr(row, "entry_carried_heat_W", None)
                )
                flow_label = self._format_kg_s(
                    getattr(row, "entry_carried_flow_kg_s", None)
                )

                role = str(getattr(row, "role", "") or "")
                origin_room_id = str(getattr(row, "origin_room_id", "") or "")
                parent_subleg_id = str(
                    getattr(row, "parent_subleg_id", "") or ""
                )

                if role == "primary/common subleg":
                    from_label = "Common main / leg entry"
                elif origin_room_id:
                    from_label = f"Take-off at {origin_room_id}"
                elif parent_subleg_id:
                    from_label = f"Parent {parent_subleg_id}"
                else:
                    from_label = "—"

                entry_rooms = getattr(row, "entry_carried_room_ids", ()) or ()
                route_rooms = getattr(row, "route_room_ids", ()) or ()

                basis = (
                    f"{getattr(row, 'takeoff_classification', '')} | "
                    f"entry Q {q_label} | "
                    f"entry rooms {len(entry_rooms)} | "
                    f"route rooms {len(route_rooms)}"
                )

                out.append(
                    {
                        "group": str(getattr(row, "leg_label", "") or ""),
                        "role": role,
                        "from": from_label,
                        "to": str(getattr(row, "subleg_label", "") or ""),
                        "flow": flow_label,
                        "basis": basis,
                        "status": str(getattr(row, "status", "") or ""),
                    }
                )
                continue

            # Legacy fallback for any remaining old H-R1 DTO rows.
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

    def _clear_common_main_leg_subleg_table_focus(self) -> None:
        if not hasattr(self, "_common_main_leg_subleg_table"):
            return

        table = self._common_main_leg_subleg_table

        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    item.setBackground(QBrush())

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

    @staticmethod
    def _display_leg_label(label: str) -> str:
        text = str(label or "")

        replacements = {
            "Heating Leg 1": "Leg 1",
            "Heating Leg 2": "Leg 2",
            "Heating Leg 3": "Leg 3",
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


def _hydronic_mass_flow_basis_text(project_state, projection) -> str:
    """
    H-S21-C — Display-only hydronic mass-flow basis text.

    Source temperatures live on Environment.
    Derived ΔT is calculated at use sites and not stored.
    """
    env = getattr(project_state, "environment", None)

    flow_temp_c = getattr(env, "design_flow_temp_c", None) if env is not None else None
    return_temp_c = (
        getattr(env, "design_return_temp_c", None) if env is not None else None
    )

    delta_t_k = getattr(
        getattr(projection, "sections_projection", None),
        "design_delta_t_K",
        None,
    )

    if flow_temp_c is not None and return_temp_c is not None and delta_t_k is not None:
        return (
            "Mass-flow basis: Environment "
            f"{float(flow_temp_c):.1f}/{float(return_temp_c):.1f} °C "
            f"ΔT {float(delta_t_k):.1f} K"
        )

    if delta_t_k is not None:
        return f"Mass-flow basis: ΔT {float(delta_t_k):.1f} K"

    return "Mass-flow basis: —"
