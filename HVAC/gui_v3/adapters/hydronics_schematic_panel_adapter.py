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

from HVAC.hydronics.proportioning.valve_authority_preview_v1 import (
    build_valve_authority_preview_v1,
)
from HVAC.hydronics.proportioning.valve_authority_input_mapping_v1 import (
    build_valve_authority_input_mapping_v1,
)
from HVAC.hydronics.proportioning.balancing_method_candidate_mapping_v1 import (
    build_balancing_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.basis_only_proportioned_export_payload_v1 import (
    build_basis_only_proportioned_export_payload_preview_v1,
)
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
    CommonMainLegSublegBalancingPointEvidenceV1,
    CommonMainLegSublegRoomEvidenceV1,
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegSchematicV1,
)
from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    _room_flow_kg_s,
)
from HVAC.hydronics.proportioning.section_route_identity_v1 import (
    infer_section_route_identity_v1,
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
    return_arrangement_intent_from_dict_v1,
)
from HVAC.hydronics.proportioning.effective_return_arrangement_resolver_v1 import (
    resolve_effective_return_arrangements_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    build_proportioned_basis_snapshot_v1,
)
from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    build_committed_proportioning_hydraulic_input_authority_v1,
)
from HVAC.hydronics.proportioning.chosen_basis_route_pressure_preview_v1 import (
    build_chosen_basis_route_pressure_preview_v1,
)
from HVAC.hydronics.proportioning.chosen_basis_controlling_route_preview_v1 import (
    build_chosen_basis_controlling_route_preview_v1,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    PreliminaryBalancingResistanceRowV1,
    build_chosen_basis_balancing_resistance_basis_v1,
)
from HVAC.hydronics.proportioning.balancing_point_topology_authority_v1 import (
    build_balancing_point_topology_authority_v1,
)
from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    build_balancing_point_resistance_allocation_v1,
)
from HVAC.hydronics.proportioning.balancing_point_method_candidate_mapping_v1 import (
    build_balancing_point_method_candidate_mapping_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    build_balancing_point_valve_authority_input_mapping_v1,
)
from HVAC.hydronics.proportioning.balancing_point_controlled_circuit_dp_authority_v1 import (
    build_balancing_point_controlled_circuit_dp_authority_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_authority_preview_v1 import (
    build_balancing_point_valve_authority_preview_v1,
)
from HVAC.hydronics.proportioning.balancing_point_low_authority_design_disposition_v1 import (
    build_balancing_point_low_authority_design_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_duty_design_basis_v1 import (
    build_balancing_point_valve_duty_design_basis_v1,
)
from HVAC.hydronics.proportioning.balancing_point_required_kv_preview_v1 import (
    build_balancing_point_required_kv_preview_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_evidence_v1 import (
    build_balancing_point_kvs_candidate_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_utilisation_evidence_v1 import (
    build_balancing_point_kvs_candidate_utilisation_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_kvs_candidate_acceptance_intent_v1 import (
    BalancingPointKvsCandidateAcceptanceIntentV1,
    resolve_balancing_point_kvs_candidate_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_hydraulic_consequence_v1 import (
    build_balancing_point_accepted_kvs_hydraulic_consequence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
    KVS_REVISION_REQUIRED,
    BalancingPointAcceptedKvsConsequenceDispositionIntentV1,
    resolve_balancing_point_accepted_kvs_consequence_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_duty_envelope_v1 import (
    build_balancing_point_valve_product_search_duty_envelope_v1,
)
from HVAC.hydronics.proportioning.balancing_point_proportioning_commit_readiness_v1 import (
    build_point_proportioning_commit_readiness_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_product_search_criteria_intent_v1 import (
    BalancingPointValveProductSearchCriteriaIntentV1,
    resolve_balancing_point_valve_product_search_criteria_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_catalogue_candidate_match_evidence_v1 import (
    build_balancing_point_valve_catalogue_candidate_match_evidence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_valve_candidate_acceptance_intent_v1 import (
    BalancingPointValveCandidateAcceptanceIntentV1,
    resolve_balancing_point_valve_candidate_acceptance_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_hydraulic_consequence_v1 import (
    build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1,
)
from HVAC.hydronics.proportioning.balancing_point_accepted_valve_candidate_consequence_disposition_intent_v1 import (
    APPROVED_FOR_LATER_VALVE_DESIGN,
    VALVE_CANDIDATE_REVISION_REQUIRED,
    BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1,
    resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1,
)
from HVAC.hydronics.proportioning.balancing_point_approved_valve_candidate_design_duty_envelope_v1 import (
    build_balancing_point_approved_valve_candidate_design_duty_envelope_v1,
)
from HVAC.hydronics_v3.dto.valve_catalog_dto import ValveCatalogDTO
from HVAC.hydronics_v3.catalogues.local_valve_catalogue_loader_v1 import (
    load_bundled_local_valve_catalogue_v1,
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
        # H-S50-C — bundled local catalogue evidence. This is adapter-memory
        # input only: no ProjectState persistence, ranking or valve selection.
        try:
            self._supplied_valve_catalog_dto_v1 = (
                load_bundled_local_valve_catalogue_v1()
            )
        except ValueError as exc:
            print("[H-S50-C LOCAL VALVE CATALOGUE ERROR]", str(exc))
            self._supplied_valve_catalog_dto_v1 = None

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
        # H-S38-A2 — Scoped RR length authority callback
        # --------------------------------------------------
        if hasattr(self._panel, "set_scoped_rr_length_basis_callback"):
            self._panel.set_scoped_rr_length_basis_callback(
                self.set_scoped_rr_length_basis
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

        # --------------------------------------------------
        # H-S37-B4 — Local Basic PS section velocity callback
        # --------------------------------------------------
        if hasattr(
                self._panel,
                "set_basic_ps_section_velocity_override_callback",
        ):
            self._panel.set_basic_ps_section_velocity_override_callback(
                self.set_basic_ps_section_velocity_override
            )

        # H-S48-B — explicit manual generic-Kvs acceptance callback.
        if hasattr(
                self._panel,
                "set_balancing_point_kvs_acceptance_callback",
        ):
            self._panel.set_balancing_point_kvs_acceptance_callback(
                self.set_balancing_point_kvs_candidate_acceptance
            )

        if hasattr(
                self._panel,
                "set_accepted_kvs_consequence_disposition_callback",
        ):
            self._panel.set_accepted_kvs_consequence_disposition_callback(
                self.set_accepted_kvs_consequence_disposition
            )

        if hasattr(
                self._panel,
                "set_product_search_criteria_callback",
        ):
            self._panel.set_product_search_criteria_callback(
                self.set_product_search_criteria
            )

        # H-S52-B — explicit manual catalogue-candidate intent callback.
        if hasattr(
                self._panel,
                "set_point_valve_candidate_acceptance_callback",
        ):
            self._panel.set_point_valve_candidate_acceptance_callback(
                self.set_point_valve_candidate_acceptance
            )

        if hasattr(
                self._panel,
                "set_point_valve_candidate_consequence_disposition_callback",
        ):
            self._panel.set_point_valve_candidate_consequence_disposition_callback(
                self.set_point_valve_candidate_consequence_disposition
            )

        self.refresh()



    def supply_valve_catalog_dto_v1(
            self,
            catalog: ValveCatalogDTO | None,
    ) -> None:
        """Supply or clear transient H-S50-B catalogue evidence.

        The DTO is copied into adapter-owned memory. No ProjectState field is
        written and no candidate is ranked, recommended or selected.
        """
        if catalog is not None and not isinstance(catalog, ValveCatalogDTO):
            raise ValueError("catalog must be ValveCatalogDTO or None")
        self._supplied_valve_catalog_dto_v1 = (
            None
            if catalog is None
            else ValveCatalogDTO(
                catalog_id=str(catalog.catalog_id or "").strip(),
                kv_options=list(catalog.kv_options or []),
            )
        )
        self.refresh()

    def set_product_search_criteria(self, payload: dict) -> None:
        """Persist or clear H-S49-C manual criteria; never query a catalogue."""
        if not isinstance(payload, dict):
            raise ValueError("Product-search criteria payload must be a dictionary")
        project = self._project_state
        if project is None:
            return
        point_id = str(payload.get("balancing_point_id") or "").strip()
        if not point_id:
            raise ValueError("balancing_point_id is required")
        action = str(payload.get("action") or "").strip().lower()
        intent = getattr(
            project,
            "hydronic_point_valve_product_search_criteria_intent",
            None,
        )

        if action == "set":
            envelopes = getattr(
                self,
                "_balancing_point_valve_product_search_duty_envelope_preview",
                None,
            )
            envelope = next(
                (
                    row for row in tuple(getattr(envelopes, "rows", ()) or ())
                    if str(getattr(row, "balancing_point_id", "") or "").strip()
                    == point_id
                ),
                None,
            )
            if (
                envelope is None
                or not bool(getattr(envelope, "envelope_available", False))
                or not bool(
                    getattr(envelope, "approved_for_product_search", False)
                )
            ):
                raise ValueError("Current approved H-S49-A envelope required")
            if intent is None:
                intent = BalancingPointValveProductSearchCriteriaIntentV1()
            intent.set_criteria(
                balancing_point_id=point_id,
                accepted_kvs_basis=getattr(envelope, "accepted_kvs", None),
                catalog_id=payload.get("catalog_id"),
                kv_tolerance_percent=payload.get(
                    "kv_tolerance_percent", 0.0
                ),
                valve_ref_contains=payload.get("valve_ref_contains", ""),
                note_contains=payload.get("note_contains", ""),
            )
        elif action == "clear":
            if intent is None:
                self.refresh()
                return
            intent.clear_criteria(point_id)
        else:
            raise ValueError("action must be 'set' or 'clear'")

        project.hydronic_point_valve_product_search_criteria_intent = intent
        project.hydronics_valid = False
        if hasattr(project, "mark_dirty"):
            project.mark_dirty()
        self.refresh()
        for signal_name in ("project_state_changed", "project_changed"):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

    def set_point_valve_candidate_acceptance(
            self,
            payload: dict,
    ) -> None:
        """Persist or clear one explicit H-S52-B candidate identity.

        The requested catalogue/reference pair must still be a current
        H-S50-A match for the selected stable balancing-point ID.  This stores
        manual intent only: no product hydraulics, valve setting or final
        balancing result is committed.
        """
        if not isinstance(payload, dict):
            raise ValueError(
                "Point valve-candidate payload must be a dictionary"
            )
        project = self._project_state
        if project is None:
            return
        point_id = str(payload.get("balancing_point_id") or "").strip()
        if not point_id:
            raise ValueError("balancing_point_id is required")
        action = str(payload.get("action") or "").strip().lower()
        intent = getattr(
            project,
            "hydronic_point_valve_candidate_acceptance_intent",
            None,
        )

        if action == "accept":
            evidence = getattr(
                self,
                "_balancing_point_valve_catalogue_candidate_match_evidence",
                None,
            )
            point_row = next(
                (
                    row
                    for row in tuple(getattr(evidence, "rows", ()) or ())
                    if str(
                        getattr(row, "balancing_point_id", "") or ""
                    ).strip() == point_id
                ),
                None,
            )
            if point_row is None:
                raise ValueError(
                    "Balancing point has no current H-S50-A evidence"
                )
            catalog_id = str(payload.get("catalog_id") or "").strip()
            valve_ref = str(payload.get("valve_ref") or "").strip()
            matching = next(
                (
                    candidate
                    for candidate in tuple(
                        getattr(point_row, "candidates", ()) or ()
                    )
                    if (
                        str(
                            getattr(candidate, "catalog_id", "") or ""
                        ).strip() == catalog_id
                        and str(
                            getattr(candidate, "valve_ref", "") or ""
                        ).strip() == valve_ref
                    )
                ),
                None,
            )
            if matching is None:
                raise ValueError(
                    "catalog_id and valve_ref must identify a current "
                    "H-S50-A candidate for this point"
                )
            if intent is None:
                intent = BalancingPointValveCandidateAcceptanceIntentV1()
            intent.accept_candidate(
                balancing_point_id=point_id,
                catalog_id=catalog_id,
                valve_ref=valve_ref,
            )
        elif action == "clear":
            if intent is None:
                self.refresh()
                return
            intent.clear_candidate(point_id)
        else:
            raise ValueError("action must be 'accept' or 'clear'")

        project.hydronic_point_valve_candidate_acceptance_intent = intent
        project.hydronics_valid = False
        if hasattr(project, "mark_dirty"):
            project.mark_dirty()

        self.refresh()
        for signal_name in ("project_state_changed", "project_changed"):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

    def set_point_valve_candidate_consequence_disposition(
            self,
            payload: dict,
    ) -> None:
        """Persist or clear one explicit H-S52-E manual disposition."""
        if not isinstance(payload, dict):
            raise ValueError(
                "Valve-candidate consequence disposition payload "
                "must be a dictionary"
            )
        project = self._project_state
        if project is None:
            return
        point_id = str(
            payload.get("balancing_point_id") or ""
        ).strip()
        if not point_id:
            raise ValueError("balancing_point_id is required")

        action = str(payload.get("action") or "").strip().lower()
        intent = getattr(
            project,
            "hydronic_point_accepted_valve_candidate_"
            "consequence_disposition_intent",
            None,
        )

        if action == "set":
            consequence = getattr(
                self,
                "_balancing_point_accepted_valve_candidate_"
                "hydraulic_consequence_preview",
                None,
            )
            consequence_row = next(
                (
                    row
                    for row in tuple(
                        getattr(consequence, "rows", ()) or ()
                    )
                    if str(
                        getattr(row, "balancing_point_id", "") or ""
                    ).strip() == point_id
                ),
                None,
            )
            if (
                consequence_row is None
                or not bool(
                    getattr(
                        consequence_row,
                        "consequence_available",
                        False,
                    )
                )
            ):
                raise ValueError(
                    "Current H-S52-C accepted catalogue valve-candidate "
                    "consequence is required"
                )

            disposition = str(
                payload.get("disposition") or ""
            ).strip()
            if disposition not in {
                APPROVED_FOR_LATER_VALVE_DESIGN,
                VALVE_CANDIDATE_REVISION_REQUIRED,
            }:
                raise ValueError(
                    "Unknown accepted valve-candidate "
                    "consequence disposition"
                )
            if intent is None:
                intent = (
                    BalancingPointAcceptedValveCandidateConsequenceDispositionIntentV1()
                )
            intent.set_disposition(
                balancing_point_id=point_id,
                disposition=disposition,
                catalog_id_basis=getattr(
                    consequence_row,
                    "catalog_id",
                    "",
                ),
                valve_ref_basis=getattr(
                    consequence_row,
                    "valve_ref",
                    "",
                ),
                current_kv_m3_h_basis=getattr(
                    consequence_row,
                    "current_kv_m3_h",
                    None,
                ),
            )
        elif action == "clear":
            if intent is None:
                self.refresh()
                return
            intent.clear_disposition(point_id)
        else:
            raise ValueError("action must be 'set' or 'clear'")

        project.hydronic_point_accepted_valve_candidate_consequence_disposition_intent = (
            intent
        )
        project.hydronics_valid = False
        if hasattr(project, "mark_dirty"):
            project.mark_dirty()

        self.refresh()
        for signal_name in (
            "project_state_changed",
            "project_changed",
        ):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

    def set_accepted_kvs_consequence_disposition(
            self,
            payload: dict,
    ) -> None:
        """Persist or clear one explicit H-S48-D consequence disposition."""
        if not isinstance(payload, dict):
            raise ValueError("Kvs consequence disposition payload must be a dictionary")

        project = self._project_state
        if project is None:
            return

        point_id = str(payload.get("balancing_point_id") or "").strip()
        if not point_id:
            raise ValueError("balancing_point_id is required")

        action = str(payload.get("action") or "").strip().lower()
        intent = getattr(
            project,
            "hydronic_point_accepted_kvs_consequence_disposition_intent",
            None,
        )

        if action == "set":
            consequence = getattr(
                self,
                "_balancing_point_accepted_kvs_hydraulic_consequence_preview",
                None,
            )
            consequence_row = next(
                (
                    row for row in tuple(getattr(consequence, "rows", ()) or ())
                    if str(getattr(row, "balancing_point_id", "") or "").strip()
                    == point_id
                ),
                None,
            )
            if (
                consequence_row is None
                or not bool(getattr(consequence_row, "consequence_available", False))
            ):
                raise ValueError(
                    "Current H-S48-C accepted-Kvs consequence is required"
                )

            disposition = str(payload.get("disposition") or "").strip()
            if disposition not in {
                APPROVED_FOR_PRODUCT_SEARCH,
                KVS_REVISION_REQUIRED,
            }:
                raise ValueError("Unknown accepted-Kvs consequence disposition")

            accepted_kvs = getattr(consequence_row, "accepted_kvs", None)
            if intent is None:
                intent = BalancingPointAcceptedKvsConsequenceDispositionIntentV1()
            intent.set_disposition(
                balancing_point_id=point_id,
                disposition=disposition,
                accepted_kvs_basis=accepted_kvs,
            )
        elif action == "clear":
            if intent is None:
                self.refresh()
                return
            intent.clear_disposition(point_id)
        else:
            raise ValueError("action must be 'set' or 'clear'")

        project.hydronic_point_accepted_kvs_consequence_disposition_intent = intent
        project.hydronics_valid = False
        if hasattr(project, "mark_dirty"):
            project.mark_dirty()

        self.refresh()
        for signal_name in ("project_state_changed", "project_changed"):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

    def set_balancing_point_kvs_candidate_acceptance(
            self,
            payload: dict,
    ) -> None:
        """Persist or clear one explicit H-S48-B generic-Kvs acceptance.

        This is the manual intent boundary only. It does not choose a valve
        product, size or setting and it does not alter hydraulic calculations.
        """
        if not isinstance(payload, dict):
            raise ValueError("Point Kvs acceptance payload must be a dictionary")

        project = self._project_state
        if project is None:
            return

        point_id = str(payload.get("balancing_point_id") or "").strip()
        if not point_id:
            raise ValueError("balancing_point_id is required")

        action = str(payload.get("action") or "").strip().lower()
        intent = getattr(
            project,
            "hydronic_point_kvs_candidate_acceptance_intent",
            None,
        )

        if action == "accept":
            evidence = getattr(
                self,
                "_balancing_point_kvs_utilisation_evidence_preview",
                None,
            )
            if evidence is None:
                raise ValueError("Current H-S47-C Kvs evidence is required")

            evidence_row = next(
                (
                    row for row in tuple(getattr(evidence, "rows", ()) or ())
                    if str(getattr(row, "balancing_point_id", "") or "").strip()
                    == point_id
                ),
                None,
            )
            if evidence_row is None:
                raise ValueError("Balancing point has no current H-S47-C evidence")

            try:
                requested_kvs = float(payload.get("accepted_kvs"))
            except (TypeError, ValueError):
                raise ValueError("accepted_kvs must be a current candidate")

            matching_kvs = next(
                (
                    float(candidate)
                    for candidate in tuple(
                        getattr(evidence_row, "kvs_candidates", ()) or ()
                    )
                    if abs(float(candidate) - requested_kvs) <= 1e-9
                ),
                None,
            )
            if matching_kvs is None:
                raise ValueError("accepted_kvs must be a current H-S47-C candidate")

            series_id = str(
                getattr(evidence_row, "kvs_series_id", "") or ""
            ).strip()
            if not series_id:
                raise ValueError("Current Kvs series identity is unavailable")

            if intent is None:
                intent = BalancingPointKvsCandidateAcceptanceIntentV1()
            intent.accept_candidate(
                balancing_point_id=point_id,
                accepted_kvs=matching_kvs,
                kvs_series_id=series_id,
            )
        elif action == "clear":
            if intent is None:
                self.refresh()
                return
            intent.clear_candidate(point_id)
        else:
            raise ValueError("action must be 'accept' or 'clear'")

        project.hydronic_point_kvs_candidate_acceptance_intent = intent
        project.hydronics_valid = False
        if hasattr(project, "mark_dirty"):
            project.mark_dirty()

        self.refresh()
        for signal_name in ("project_state_changed", "project_changed"):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

    def set_basic_ps_section_velocity_override(self, payload: dict) -> None:
        """Persist one explicit H-S37-B4 section override or clear it.

        This callback is the authority boundary. It mutates only the selected
        stable Basic PS section_id, invalidates hydronics, and refreshes the
        read-only projections. It does not alter Environment or other sections.
        """
        if not isinstance(payload, dict):
            raise ValueError("Basic PS section velocity payload must be a dictionary")

        project = self._project_state
        if project is None:
            return

        section_id = str(payload.get("section_id") or "").strip()
        if not section_id:
            raise ValueError("section_id is required")

        action = str(payload.get("action") or "").strip().lower()
        intent = getattr(project, "basic_hydronic_sizing_intent", None)

        if action == "set":
            if intent is None:
                from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
                    BasicHydronicSizingIntentV1,
                )

                intent = BasicHydronicSizingIntentV1()
                project.basic_hydronic_sizing_intent = intent
            intent.set_section_max_velocity_override(
                section_id,
                payload.get("max_velocity_m_s"),
            )
        elif action == "clear":
            if intent is None:
                self.refresh()
                return
            intent.clear_section_max_velocity_override(section_id)
        else:
            raise ValueError("action must be 'set' or 'clear'")

        project.hydronics_valid = False
        self.refresh()

        for signal_name in ("project_state_changed", "project_changed"):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

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

    def set_scoped_rr_length_basis(self, payload: dict) -> None:
        """Persist one H-S38-A2 Leg/Common/Branch RR length override."""
        if not isinstance(payload, dict):
            raise ValueError("Scoped RR length payload must be a dictionary")

        project = getattr(self, "_project_state", None)
        if project is None:
            return

        scope = str(payload.get("scope") or "").strip().upper()
        target_id = str(payload.get("target_id") or "").strip()
        mode = str(payload.get("basis_mode") or "INHERIT").strip()
        try:
            added_length_m = max(
                float(payload.get("added_length_m") or 0.0),
                0.0,
            )
        except (TypeError, ValueError):
            added_length_m = 0.0

        if not target_id:
            raise ValueError("Scoped RR length target_id is required")

        intent = self._get_return_arrangement_acceptance_intent()
        if isinstance(intent, dict):
            intent = return_arrangement_intent_from_dict_v1(intent)

        if scope == "LEG":
            if mode.upper() == INHERIT:
                intent.clear_leg_rr_added_length_override(target_id)
            else:
                intent.set_leg_rr_added_length_override(
                    target_id,
                    mode,
                    added_length_m,
                )
        elif scope in {"COMMON_SUBLEG", "BRANCH_SUBLEG"}:
            if mode.upper() == INHERIT:
                intent.clear_subleg_rr_added_length_override(target_id)
            else:
                intent.set_subleg_rr_added_length_override(
                    target_id,
                    mode,
                    added_length_m,
                )
        else:
            raise ValueError(f"Unknown scoped RR length scope: {scope}")

        self._return_arrangement_acceptance_intent = intent
        project.hydronic_return_arrangement_intent = intent

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
        self._committed_hydraulic_route_pressure_projection_v1 = None

        if getattr(self._project_state, "hydronic_topology", None) is not None:
            try:
                route_pressure_projection = (
                    build_route_pressure_accumulator_v1(
                        self._project_state,
                    )
                )
                self._committed_hydraulic_route_pressure_projection_v1 = (
                    route_pressure_projection
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

        # H-S43-B1: adapter-owned flow evidence avoids refresh-order
        # dependence on the panel's preliminary resistance cache.
        self._received_basic_ps_route_flow_basis_v1 = (
            self._build_received_basic_ps_route_flow_basis_v1(
                received_basic_ps_rows
            )
        )

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

            if hasattr(self._panel, "set_scoped_rr_length_basis_overrides"):
                if isinstance(intent, dict):
                    leg_rr_modes = dict(
                        intent.get("leg_rr_added_length_basis_modes", {}) or {}
                    )
                    leg_rr_lengths = dict(
                        intent.get("leg_rr_added_lengths_m", {}) or {}
                    )
                    subleg_rr_modes = dict(
                        intent.get("subleg_rr_added_length_basis_modes", {}) or {}
                    )
                    subleg_rr_lengths = dict(
                        intent.get("subleg_rr_added_lengths_m", {}) or {}
                    )
                else:
                    leg_rr_modes = dict(
                        getattr(
                            intent,
                            "leg_rr_added_length_basis_modes",
                            {},
                        ) or {}
                    )
                    leg_rr_lengths = dict(
                        getattr(intent, "leg_rr_added_lengths_m", {}) or {}
                    )
                    subleg_rr_modes = dict(
                        getattr(
                            intent,
                            "subleg_rr_added_length_basis_modes",
                            {},
                        ) or {}
                    )
                    subleg_rr_lengths = dict(
                        getattr(intent, "subleg_rr_added_lengths_m", {}) or {}
                    )

                self._panel.set_scoped_rr_length_basis_overrides(
                    leg_basis_modes=leg_rr_modes,
                    leg_lengths_m=leg_rr_lengths,
                    subleg_basis_modes=subleg_rr_modes,
                    subleg_lengths_m=subleg_rr_lengths,
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
        # H-S36-A1 — explicit section-evidence delivery
        # --------------------------------------------------
        # Run after the adapter pass has assembled its read-only evidence.
        # This is display wiring only; no calculation or ProjectState change.
        self._push_clean_proportioned_focused_section_source_rows_v1()

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
                    "common_main_dp": self._format_pa(
                        getattr(row, "common_main_dp_pa", None)
                    ),
                    "leg_entry_dp": self._format_pa(
                        getattr(row, "leg_entry_dp_pa", None)
                    ),
                    "physical_main_entry_dp": self._format_pa(
                        getattr(row, "physical_main_entry_dp_pa", None)
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
                    "common_main_dp": "—",
                    "leg_entry_dp": "—",
                    "physical_main_entry_dp": "—",
                    "source": "—",
                    "status": (
                        "Preview only — no chosen-basis controlling route evidence"
                    ),
                }
            )

        return rows

    def _build_provisional_proportioning_burden_rows_v1(
            self,
            chosen_controlling_rows,
            resistance_basis=None,
    ) -> list[dict]:
        """
        H-S30-C:
        Convert chosen-basis controlling / shortfall evidence into a
        Proportioned-tab provisional burden table.

        Read-only evidence:
            no valve selection
            no final balancing
            no pump selection
            no pipe resizing
            no final hydraulic result
        """
        input_rows = list(chosen_controlling_rows or ())

        def _normalise_key(value: object) -> str:
            return str(value or "").strip().lower()

        resistance_by_route: dict[str, object] = {}

        for resistance_row in list(
                getattr(resistance_basis, "rows", ()) or ()
        ):
            route_id = _normalise_key(
                getattr(resistance_row, "route_id", "")
            )
            route_label = _normalise_key(
                getattr(resistance_row, "route_label", "")
            )

            if route_id:
                resistance_by_route[route_id] = resistance_row

            if route_label:
                resistance_by_route[route_label] = resistance_row

        def _resistance_row_for(route_row):
            route_id = _normalise_key(getattr(route_row, "route_id", ""))
            route_label = _normalise_key(getattr(route_row, "route", ""))

            if route_id and route_id in resistance_by_route:
                return resistance_by_route[route_id]

            if route_label and route_label in resistance_by_route:
                return resistance_by_route[route_label]

            for key, candidate in resistance_by_route.items():
                if route_label and (
                        route_label in key
                        or key in route_label
                ):
                    return candidate

            return None

        def _chosen_dp(row) -> float:
            try:
                return float(getattr(row, "chosen_dp_pa", 0.0) or 0.0)
            except (TypeError, ValueError):
                return 0.0

        ranked_rows = sorted(
            input_rows,
            key=_chosen_dp,
            reverse=True,
        )

        rows: list[dict] = []

        for rank, row in enumerate(ranked_rows, start=1):
            is_controlling = bool(getattr(row, "is_controlling", False))
            required_added_dp = getattr(row, "dp_below_controlling_pa", None)
            resistance_row = _resistance_row_for(row)

            flow_kg_s = "—"
            resistance_pa_per_kg_s2 = "—"

            if resistance_row is not None:
                flow_kg_s = str(
                    getattr(resistance_row, "flow_kg_s", "") or "—"
                )
                resistance_pa_per_kg_s2 = str(
                    getattr(
                        resistance_row,
                        "resistance_pa_per_kg_s2",
                        "",
                    )
                    or "—"
                )

            if is_controlling:
                action = "Controlling route — no provisional added Δp"
                status = (
                    "Preview only — chosen-basis controlling route; "
                    "no valve selected"
                )
            else:
                action = "Provisional added Δp evidence only"
                status = (
                    "Preview only — below controlling route; "
                    "no balancing valve selected"
                )

            rows.append(
                {
                    "rank": str(rank),
                    "route": str(getattr(row, "route", "") or "—"),
                    "basis": str(getattr(row, "basis", "") or "—"),
                    "flow_kg_s": flow_kg_s,
                    "chosen_dp": self._format_pa(
                        getattr(row, "chosen_dp_pa", None)
                    ),
                    "controlling": "Yes" if is_controlling else "No",
                    "required_added_dp": self._format_pa(required_added_dp),
                    "common_main_dp": self._format_pa(
                        getattr(row, "common_main_dp_pa", None)
                    ),
                    "leg_entry_dp": self._format_pa(
                        getattr(row, "leg_entry_dp_pa", None)
                    ),
                    "physical_main_entry_dp": self._format_pa(
                        getattr(row, "physical_main_entry_dp_pa", None)
                    ),
                    "resistance_pa_per_kg_s2": resistance_pa_per_kg_s2,
                    "action": action,
                    "status": status,
                }
            )

        if not rows:
            rows.append(
                {
                    "rank": "—",
                    "route": "—",
                    "basis": "—",
                    "flow_kg_s": "—",
                    "chosen_dp": "—",
                    "controlling": "No",
                    "required_added_dp": "—",
                    "common_main_dp": "—",
                    "leg_entry_dp": "—",
                    "physical_main_entry_dp": "—",
                    "resistance_pa_per_kg_s2": "—",
                    "action": "Waiting for chosen-basis burden evidence",
                    "status": "Preview only — no valve selected",
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

    @staticmethod
    def _received_basic_ps_route_identity_v1(
            result: object,
            projection: object,
    ) -> tuple[str, str]:
        """
        H-S43-B2 stable received-route identity.

        Pipe-sizing result identity is retained when present. The composed
        Basic PS sections projection is the authoritative fallback because it
        owns the leg/subleg scope used to build the received rows.
        """
        sections_projection = getattr(
            projection,
            "sections_projection",
            None,
        )
        leg_id = str(
            getattr(result, "leg_id", "")
            or getattr(sections_projection, "leg_id", "")
            or ""
        )
        subleg_id = str(
            getattr(result, "subleg_id", "")
            or getattr(sections_projection, "subleg_id", "")
            or ""
        )
        return leg_id, subleg_id

    @staticmethod
    def _build_received_basic_ps_route_flow_basis_v1(
            rows: list[dict] | tuple[dict, ...],
    ) -> PreliminaryBalancingResistanceBasisV1:
        """
        H-S43-B1 stable route-flow delivery from received Basic PS evidence.

        This consumes existing carried-flow evidence only. For each stable
        route/subleg identity it retains the largest section flow, matching
        the established route-level balancing-point flow rule.
        """
        grouped: dict[str, dict[str, object]] = {}
        blockers: list[str] = []

        for raw_row in tuple(rows or ()):
            row = dict(raw_row or {})
            route_id = str(
                row.get("route_id") or row.get("subleg_id") or ""
            ).strip()
            route_label = str(row.get("route") or route_id or "").strip()
            if not route_id:
                continue

            raw_flow = row.get("flow_kg_s")
            try:
                flow_kg_s = float(str(raw_flow or "").split()[0])
            except (TypeError, ValueError, IndexError):
                continue
            if flow_kg_s <= 0.0:
                continue

            current = grouped.get(route_id)
            if current is None:
                grouped[route_id] = {
                    "route_label": route_label,
                    "flow_kg_s": flow_kg_s,
                    "section_count": 1,
                }
            else:
                current["flow_kg_s"] = max(
                    float(current["flow_kg_s"]),
                    flow_kg_s,
                )
                current["section_count"] = int(current["section_count"]) + 1

        basis_rows: list[PreliminaryBalancingResistanceRowV1] = []
        for route_id, values in grouped.items():
            flow_kg_s = float(values["flow_kg_s"])
            basis_rows.append(
                PreliminaryBalancingResistanceRowV1(
                    route_id=route_id,
                    route_label=str(values["route_label"] or route_id),
                    sections=str(values["section_count"]),
                    flow_kg_s=f"{flow_kg_s:.5f} kg/s",
                    required_added_dp="—",
                    resistance_pa_per_kg_s2="—",
                    controlling="No",
                    status="Received Basic PS stable route-flow basis",
                )
            )

        if not basis_rows:
            blockers.append("No positive received Basic PS route flows available")

        return PreliminaryBalancingResistanceBasisV1(
            ready=bool(basis_rows),
            status=(
                "Received Basic PS stable route-flow basis ready"
                if basis_rows
                else "Received Basic PS stable route-flow basis unavailable"
            ),
            rows=basis_rows,
            blockers=blockers,
        )

    @staticmethod
    def _balancing_point_target_id_v1(
            balancing_point_id: object,
            point_scope: object,
    ) -> str:
        point_id = str(balancing_point_id or "")
        scope = str(point_scope or "").strip().lower()
        if scope == "main":
            return "common_main"
        prefix = f"balancing-point:{scope}:"
        if not point_id.startswith(prefix):
            return ""
        target_id = point_id[len(prefix):]
        # H-S44-A2 route-exclusive common-route points retain their own
        # stable identity while mapping to the owning schematic subleg.
        if scope == "subleg" and target_id.endswith(
                ":downstream-exclusive"
        ):
            return target_id.rsplit(":", 1)[0]
        return target_id

    def _build_blocked_balancing_point_allocation_gui_rows_v1(
            self,
            allocation,
    ) -> list[dict]:
        """
        H-S44-E1 display-only fallback for a valid but unconserved allocation.

        H-S44-C/D correctly publish no method or valve rows when H-S44-B
        cannot conserve every route burden.  Preserve the available H-S44-B
        point rows and route residual evidence instead of displaying the
        generic waiting row.
        """

        def number(value, suffix: str, digits: int) -> str:
            if value is None:
                return "—"
            try:
                return f"{float(value):.{digits}f}{suffix}"
            except (TypeError, ValueError):
                return "—"

        conservation_rows = tuple(
            getattr(allocation, "route_conservation", ()) or ()
        )
        allocation_blockers = tuple(
            str(value)
            for value in tuple(getattr(allocation, "blockers", ()) or ())
            if str(value or "").strip()
        )
        display_rows: list[dict] = []

        for row in tuple(getattr(allocation, "rows", ()) or ()):
            governed_routes = tuple(
                str(value or "")
                for value in tuple(
                    getattr(row, "downstream_route_ids", ()) or ()
                )
                if str(value or "").strip()
            )
            relevant_residuals: list[str] = []
            for conservation in conservation_rows:
                route_id = str(
                    getattr(conservation, "route_id", "") or ""
                )
                if route_id not in governed_routes:
                    continue
                if bool(getattr(conservation, "conserved", False)):
                    continue
                difference = number(
                    getattr(conservation, "difference_pa", None),
                    " Pa",
                    1,
                )
                relevant_residuals.append(
                    f"{route_id}: unallocated residual {difference}"
                )

            shared = bool(getattr(row, "is_shared", False))
            exclusive = bool(getattr(row, "is_route_exclusive", False))
            topology = (
                "Shared"
                if shared
                else "Route-exclusive"
                if exclusive
                else "Unresolved"
            )
            blockers = tuple(relevant_residuals) or allocation_blockers
            point_status = str(getattr(row, "status", "") or "")
            display_rows.append(
                {
                    "balancing_point_id": str(
                        getattr(row, "balancing_point_id", "") or ""
                    ),
                    "point_scope": str(
                        getattr(row, "point_scope", "") or "—"
                    ),
                    "point_role": str(
                        getattr(row, "point_role", "") or "—"
                    ),
                    "label": str(getattr(row, "label", "") or "—"),
                    "target_id": self._balancing_point_target_id_v1(
                        getattr(row, "balancing_point_id", ""),
                        getattr(row, "point_scope", ""),
                    ),
                    "topology": topology,
                    "governed_routes": ", ".join(governed_routes) or "—",
                    "point_flow": number(
                        getattr(row, "point_flow_kg_s", None),
                        " kg/s",
                        5,
                    ),
                    "allocated_dp": number(
                        getattr(row, "allocated_added_dp_pa", None),
                        " Pa",
                        1,
                    ),
                    "resistance": number(
                        getattr(
                            row,
                            "allocated_resistance_pa_per_kg_s2",
                            None,
                        ),
                        " Pa/(kg/s)²",
                        1,
                    ),
                    "method": "Unavailable — allocation not conserved",
                    "valve_duty": "Unavailable — allocation not conserved",
                    "controlled_dp": "—",
                    "authority": "—",
                    "ready": "No",
                    "status": (
                        f"{point_status} / H-S44-B evidence retained; "
                        "H-S44-C/D blocked"
                    ).strip(" /"),
                    "blockers": "; ".join(blockers) if blockers else "—",
                }
            )

        return display_rows

    @staticmethod
    def _build_catalogue_candidate_match_gui_rows_v1(evidence) -> list[dict]:
        """Flatten H-S50-A evidence without sorting or selecting candidates."""
        rows = []
        for point_row in tuple(getattr(evidence, "rows", ()) or ()):
            if getattr(point_row, "match_state_id", "") == (
                "catalogue_match_not_applicable"
            ):
                continue
            candidates = tuple(getattr(point_row, "candidates", ()) or ())
            blockers = "; ".join(
                tuple(getattr(point_row, "blockers", ()) or ())
            ) or "—"
            if not candidates:
                rows.append({
                    "balancing_point_id": getattr(
                        point_row, "balancing_point_id", "—"
                    ),
                    "catalog_id": getattr(point_row, "catalog_id", "") or (
                        getattr(evidence, "catalog_id", "") or "—"
                    ),
                    "valve_ref": "—",
                    "kv": "—",
                    "deviation": "—",
                    "note": "—",
                    "ready": "Yes" if getattr(point_row, "ready", False) else "No",
                    "status": getattr(point_row, "status", "—"),
                    "blockers": blockers,
                })
                continue
            for candidate in candidates:
                rows.append({
                    "balancing_point_id": getattr(
                        point_row, "balancing_point_id", "—"
                    ),
                    "catalog_id": getattr(candidate, "catalog_id", "—"),
                    "valve_ref": getattr(candidate, "valve_ref", "—"),
                    "kv": f"{float(getattr(candidate, 'kv_m3_h', 0.0)):g}",
                    "deviation": (
                        f"{float(getattr(candidate, 'kv_deviation_percent', 0.0)):.2f}%"
                    ),
                    "note": getattr(candidate, "note", "") or "—",
                    "ready": "Yes" if getattr(point_row, "ready", False) else "No",
                    "status": getattr(point_row, "status", "—"),
                    "blockers": blockers,
                })
        if rows:
            return rows
        return [{
            "balancing_point_id": "—",
            "catalog_id": getattr(evidence, "catalog_id", "") or "—",
            "valve_ref": "—",
            "kv": "—",
            "deviation": "—",
            "note": "—",
            "ready": "Yes" if getattr(evidence, "ready", False) else "No",
            "status": getattr(evidence, "status", "No candidate-match evidence"),
            "blockers": "; ".join(
                tuple(getattr(evidence, "blockers", ()) or ())
            ) or "—",
        }]

    @staticmethod
    def _build_point_valve_candidate_acceptance_editor_rows_v1(
            candidate_evidence,
            acceptance_resolution,
            consequence_evidence=None,
            disposition_resolution=None,
    ) -> list[dict]:
        """Join candidates, resolved identity and H-S52-C consequence."""
        consequence_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(
                getattr(consequence_evidence, "rows", ()) or ()
            )
        }
        disposition_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(
                getattr(disposition_resolution, "rows", ()) or ()
            )
        }
        resolved_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(
                getattr(acceptance_resolution, "rows", ()) or ()
            )
        }
        rows: list[dict] = []
        for point_row in tuple(
                getattr(candidate_evidence, "rows", ()) or ()
        ):
            point_id = str(
                getattr(point_row, "balancing_point_id", "") or ""
            ).strip()
            if not point_id:
                continue
            candidates = tuple(
                {
                    "catalog_id": str(
                        getattr(candidate, "catalog_id", "") or ""
                    ).strip(),
                    "valve_ref": str(
                        getattr(candidate, "valve_ref", "") or ""
                    ).strip(),
                    "kv_m3_h": float(
                        getattr(candidate, "kv_m3_h", 0.0)
                    ),
                    "note": str(
                        getattr(candidate, "note", "") or ""
                    ).strip(),
                }
                for candidate in tuple(
                    getattr(point_row, "candidates", ()) or ()
                )
            )
            resolved = resolved_by_id.get(point_id)
            accepted_catalog_id = str(
                getattr(resolved, "catalog_id", "") or ""
            ).strip()
            accepted_valve_ref = str(
                getattr(resolved, "valve_ref", "") or ""
            ).strip()
            has_acceptance = bool(
                accepted_catalog_id and accepted_valve_ref
            )
            # Dormant/no-match rows without saved intent need no editor entry.
            if not candidates and not has_acceptance:
                continue
            consequence = consequence_by_id.get(point_id)
            disposition = disposition_by_id.get(point_id)

            def number(value, suffix: str, digits: int) -> str:
                if value is None:
                    return "—"
                try:
                    return f"{float(value):.{digits}f}{suffix}"
                except (TypeError, ValueError):
                    return "—"

            rows.append({
                "balancing_point_id": point_id,
                "catalog_id": str(
                    getattr(point_row, "catalog_id", "")
                    or getattr(candidate_evidence, "catalog_id", "")
                    or ""
                ).strip(),
                "candidates": candidates,
                "accepted_catalog_id": accepted_catalog_id,
                "accepted_valve_ref": accepted_valve_ref,
                "accepted": bool(getattr(resolved, "accepted", False)),
                "has_acceptance": has_acceptance,
                "status": str(
                    getattr(resolved, "status", "")
                    or "Manual valve-candidate acceptance pending"
                ),
                "blockers": tuple(
                    getattr(resolved, "blockers", ()) or ()
                ),
                "consequence_available": bool(
                    getattr(consequence, "consequence_available", False)
                ),
                "current_catalogue_kv": number(
                    getattr(consequence, "current_kv_m3_h", None),
                    "",
                    3,
                ),
                "catalogue_implied_valve_dp": number(
                    getattr(consequence, "implied_valve_dp_pa", None),
                    " Pa",
                    1,
                ),
                "catalogue_implied_authority": number(
                    getattr(consequence, "implied_authority", None),
                    "",
                    3,
                ),
                "consequence_status": str(
                    getattr(consequence, "status", "")
                    or "Catalogue-candidate consequence unavailable"
                ),
                "consequence_blockers": tuple(
                    getattr(consequence, "blockers", ()) or ()
                ),
                "consequence_disposition": str(
                    getattr(disposition, "disposition", "") or ""
                ),
                "approved_for_later_valve_design": bool(
                    getattr(
                        disposition,
                        "approved_for_later_valve_design",
                        False,
                    )
                ),
                "valve_candidate_revision_required": bool(
                    getattr(
                        disposition,
                        "valve_candidate_revision_required",
                        False,
                    )
                ),
                "consequence_disposition_status": str(
                    getattr(disposition, "status", "")
                    or (
                        "Manual catalogue-candidate consequence "
                        "disposition pending"
                    )
                ),
                "consequence_disposition_blockers": tuple(
                    getattr(disposition, "blockers", ()) or ()
                ),
            })
        return rows

    @staticmethod
    def _build_product_search_criteria_editor_rows_v1(
            envelopes,
            criteria_resolution,
            *,
            available_catalog_ids=(),
    ) -> list[dict]:
        """Expose approved envelopes, persisted criteria and catalogues.

        Available catalogue IDs are transient GUI choices. A default shown by
        the panel is not persisted until the user presses Apply.
        """
        clean_catalog_ids = tuple(dict.fromkeys(
            str(value or "").strip()
            for value in tuple(available_catalog_ids or ())
            if str(value or "").strip()
        ))
        resolved_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(getattr(criteria_resolution, "rows", ()) or ())
        }
        rows = []
        for envelope in tuple(getattr(envelopes, "rows", ()) or ()):
            if (
                not bool(getattr(envelope, "envelope_available", False))
                or not bool(
                    getattr(envelope, "approved_for_product_search", False)
                )
            ):
                continue
            point_id = str(
                getattr(envelope, "balancing_point_id", "") or ""
            ).strip()
            resolved = resolved_by_id.get(point_id)
            rows.append({
                "balancing_point_id": point_id,
                "point_scope": getattr(envelope, "point_scope", "—"),
                "point_role": getattr(envelope, "point_role", "—"),
                "accepted_kvs": getattr(envelope, "accepted_kvs", None),
                "catalog_id": getattr(resolved, "catalog_id", ""),
                "available_catalog_ids": clean_catalog_ids,
                "kv_tolerance_percent": getattr(
                    resolved, "kv_tolerance_percent", None
                ),
                "valve_ref_contains": getattr(
                    resolved, "valve_ref_contains", ""
                ),
                "note_contains": getattr(resolved, "note_contains", ""),
                "criteria_available": bool(
                    getattr(resolved, "criteria_available", False)
                ),
                "status": str(
                    getattr(resolved, "status", "")
                    or "Manual product-search criteria pending"
                ),
                "blockers": tuple(
                    getattr(resolved, "blockers", ()) or ()
                ),
            })
        return rows

    @staticmethod
    def _build_approved_valve_candidate_design_duty_gui_rows_v1(
            envelopes,
    ) -> list[dict]:
        """Format H-S53-A evidence without granting product authority."""

        def number(value, suffix: str, digits: int) -> str:
            if value is None:
                return "—"
            try:
                return f"{float(value):.{digits}f}{suffix}"
            except (TypeError, ValueError):
                return "—"

        rows: list[dict] = []
        for source in tuple(getattr(envelopes, "rows", ()) or ()):
            if not bool(
                    getattr(source, "detailed_valve_design_required", False)
            ):
                continue
            rows.append({
                "balancing_point_id": getattr(
                    source, "balancing_point_id", "—"
                ),
                "point_scope": getattr(source, "point_scope", "—"),
                "point_role": getattr(source, "point_role", "—"),
                "topology": getattr(source, "topology", "—"),
                "governed_routes": ", ".join(
                    tuple(getattr(source, "governed_route_ids", ()) or ())
                ) or "—",
                "catalog_id": getattr(source, "catalog_id", "") or "—",
                "valve_ref": getattr(source, "valve_ref", "") or "—",
                "current_kv": number(
                    getattr(source, "current_kv_m3_h", None), "", 3
                ),
                "point_flow": number(
                    getattr(source, "point_flow_kg_s", None), " kg/s", 5
                ),
                "required_kv": number(
                    getattr(source, "required_kv", None), "", 3
                ),
                "implied_dp": number(
                    getattr(source, "implied_valve_dp_pa", None), " Pa", 1
                ),
                "controlled_dp": number(
                    getattr(source, "controlled_circuit_dp_pa", None),
                    " Pa",
                    1,
                ),
                "implied_authority": number(
                    getattr(source, "implied_authority", None), "", 3
                ),
                "design_authority": number(
                    getattr(source, "design_authority", None), "", 3
                ),
                "ready": "Yes" if getattr(source, "ready", False) else "No",
                "status": getattr(source, "status", "—"),
                "blockers": "; ".join(
                    tuple(getattr(source, "blockers", ()) or ())
                ) or "—",
            })
        return rows

    @staticmethod
    def _build_product_search_duty_envelope_gui_rows_v1(envelopes) -> list[dict]:
        """Format H-S49-A envelopes without granting product authority."""
        def number(value, suffix: str, digits: int) -> str:
            if value is None:
                return "—"
            try:
                return f"{float(value):.{digits}f}{suffix}"
            except (TypeError, ValueError):
                return "—"

        rows = []
        for source in tuple(getattr(envelopes, "rows", ()) or ()):
            if not bool(getattr(source, "product_search_required", False)):
                continue
            rows.append({
                "balancing_point_id": getattr(source, "balancing_point_id", "—"),
                "point_scope": getattr(source, "point_scope", "—"),
                "point_role": getattr(source, "point_role", "—"),
                "topology": getattr(source, "topology", "—"),
                "governed_routes": ", ".join(
                    tuple(getattr(source, "governed_route_ids", ()) or ())
                ) or "—",
                "point_flow": number(getattr(source, "point_flow_kg_s", None), " kg/s", 5),
                "required_kv": number(getattr(source, "required_kv", None), "", 3),
                "accepted_kvs": number(getattr(source, "accepted_kvs", None), "", 3),
                "kvs_series": getattr(source, "kvs_series_id", "") or "—",
                "implied_dp": number(getattr(source, "implied_valve_dp_pa", None), " Pa", 1),
                "controlled_dp": number(getattr(source, "controlled_circuit_dp_pa", None), " Pa", 1),
                "implied_authority": number(getattr(source, "implied_authority", None), "", 3),
                "design_authority": number(getattr(source, "design_authority", None), "", 3),
                "ready": "Yes" if getattr(source, "ready", False) else "No",
                "status": getattr(source, "status", "—"),
                "blockers": "; ".join(tuple(getattr(source, "blockers", ()) or ())) or "—",
            })
        return rows

    @staticmethod
    def _build_balancing_point_kvs_acceptance_editor_rows_v1(
            *,
            point_display_rows,
            utilisation_evidence,
            acceptance_resolution,
            consequence_evidence,
            disposition_resolution,
    ) -> list[dict]:
        """Join prepared H-S47-C evidence to resolved H-S48-A intent."""
        display_by_id = {
            str(row.get("balancing_point_id") or "").strip(): dict(row)
            for row in list(point_display_rows or [])
            if str(row.get("balancing_point_id") or "").strip()
        }
        resolved_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(
                getattr(acceptance_resolution, "rows", ()) or ()
            )
        }
        consequence_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(getattr(consequence_evidence, "rows", ()) or ())
        }
        disposition_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(getattr(disposition_resolution, "rows", ()) or ())
        }
        rows: list[dict] = []
        for evidence_row in tuple(
                getattr(utilisation_evidence, "rows", ()) or ()
        ):
            point_id = str(
                getattr(evidence_row, "balancing_point_id", "") or ""
            ).strip()
            candidates = tuple(
                float(value)
                for value in tuple(
                    getattr(evidence_row, "kvs_candidates", ()) or ()
                )
            )
            # H-S48-B edits only points for which a valve/Kvs is required.
            if not point_id or not candidates:
                continue
            display = display_by_id.get(point_id, {})
            resolved = resolved_by_id.get(point_id)
            consequence = consequence_by_id.get(point_id)
            disposition = disposition_by_id.get(point_id)
            rows.append(
                {
                    "balancing_point_id": point_id,
                    "point_scope": display.get("point_scope", "—"),
                    "point_role": display.get("point_role", "—"),
                    "required_kv": display.get("required_kv", "—"),
                    "kvs_candidates": candidates,
                    "kvs_candidates_text": display.get(
                        "kvs_candidates",
                        ", ".join(f"{value:g}" for value in candidates),
                    ),
                    "kvs_utilisation": display.get("kvs_utilisation", "—"),
                    "accepted_kvs": getattr(resolved, "accepted_kvs", None),
                    "accepted": bool(getattr(resolved, "accepted", False)),
                    "status": str(
                        getattr(resolved, "status", "")
                        or "Manual Kvs candidate acceptance pending"
                    ),
                    "blockers": tuple(
                        getattr(resolved, "blockers", ()) or ()
                    ),
                    "consequence_available": bool(
                        getattr(consequence, "consequence_available", False)
                    ),
                    "implied_valve_dp": display.get("implied_valve_dp", "—"),
                    "implied_authority": display.get("implied_authority", "—"),
                    "consequence_disposition": str(
                        getattr(disposition, "disposition", "") or ""
                    ),
                    "consequence_disposition_status": str(
                        getattr(disposition, "status", "")
                        or "Manual consequence disposition pending"
                    ),
                    "consequence_disposition_blockers": tuple(
                        getattr(disposition, "blockers", ()) or ()
                    ),
                }
            )
        return rows

    @staticmethod
    def _enrich_balancing_point_gui_rows_with_kvs_disposition_v1(
            display_rows,
            disposition_resolution,
    ) -> list[dict]:
        disposition_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(
                getattr(disposition_resolution, "rows", ()) or ()
            )
        }
        enriched: list[dict] = []
        for source in list(display_rows or []):
            row = dict(source)
            disposition = disposition_by_id.get(
                str(row.get("balancing_point_id") or "").strip()
            )
            row["consequence_disposition"] = str(
                getattr(disposition, "status", "") or "—"
            )
            enriched.append(row)
        return enriched

    @staticmethod
    def _enrich_balancing_point_gui_rows_with_kvs_consequence_v1(
            display_rows,
            consequence_evidence,
    ) -> list[dict]:
        """Add formatted H-S48-C fields without replacing design evidence."""
        consequence_by_id = {
            str(getattr(row, "balancing_point_id", "") or "").strip(): row
            for row in tuple(
                getattr(consequence_evidence, "rows", ()) or ()
            )
        }

        def number(value, suffix: str, digits: int) -> str:
            if value is None:
                return "—"
            try:
                return f"{float(value):.{digits}f}{suffix}"
            except (TypeError, ValueError):
                return "—"

        enriched: list[dict] = []
        for source in list(display_rows or []):
            row = dict(source)
            consequence = consequence_by_id.get(
                str(row.get("balancing_point_id") or "").strip()
            )
            row.update(
                accepted_kvs=number(
                    getattr(consequence, "accepted_kvs", None),
                    "",
                    3,
                ),
                implied_valve_dp=number(
                    getattr(consequence, "implied_valve_dp_pa", None),
                    " Pa",
                    1,
                ),
                implied_authority=number(
                    getattr(consequence, "implied_authority", None),
                    "",
                    3,
                ),
            )
            enriched.append(row)
        return enriched

    def _build_balancing_point_gui_rows_v1(self, mapping) -> list[dict]:
        """H-S44-E combined allocation, method and valve-duty evidence."""

        def number(value, suffix: str, digits: int) -> str:
            if value is None:
                return "—"
            try:
                return f"{float(value):.{digits}f}{suffix}"
            except (TypeError, ValueError):
                return "—"

        display_rows: list[dict] = []
        for row in tuple(getattr(mapping, "rows", ()) or ()):
            blockers = tuple(getattr(row, "blockers", ()) or ())
            shared = bool(getattr(row, "is_shared", False))
            exclusive = bool(getattr(row, "is_route_exclusive", False))
            topology = (
                "Shared"
                if shared
                else "Route-exclusive"
                if exclusive
                else "Unresolved"
            )
            display_rows.append(
                {
                    "balancing_point_id": str(
                        getattr(row, "balancing_point_id", "") or ""
                    ),
                    "point_scope": str(
                        getattr(row, "point_scope", "") or "—"
                    ),
                    "point_role": str(
                        getattr(row, "point_role", "") or "—"
                    ),
                    "label": str(getattr(row, "label", "") or "—"),
                    "target_id": self._balancing_point_target_id_v1(
                        getattr(row, "balancing_point_id", ""),
                        getattr(row, "point_scope", ""),
                    ),
                    "topology": topology,
                    "is_shared": shared,
                    "is_route_exclusive": exclusive,
                    "governed_routes": ", ".join(
                        str(value)
                        for value in tuple(
                            getattr(row, "downstream_route_ids", ()) or ()
                        )
                    ) or "—",
                    "point_flow": number(
                        getattr(row, "point_flow_kg_s", None),
                        " kg/s",
                        5,
                    ),
                    "allocated_dp": number(
                        getattr(row, "design_valve_dp_pa", None),
                        " Pa",
                        1,
                    ),
                    "resistance": number(
                        getattr(
                            row,
                            "candidate_resistance_pa_per_kg_s2",
                            None,
                        ),
                        " Pa/(kg/s)²",
                        1,
                    ),
                    "method": str(
                        getattr(row, "balancing_method_label", "") or "—"
                    ),
                    "valve_duty": str(
                        getattr(row, "authority_label", "") or "—"
                    ),
                    "required_kv": number(
                        getattr(row, "required_kv", None),
                        "",
                        3,
                    ),
                    "kvs_candidates": str(
                        getattr(row, "kvs_candidate_summary", "") or "—"
                    ),
                    "kvs_utilisation": str(
                        getattr(row, "kvs_utilisation_summary", "") or "—"
                    ),
                    "controlled_dp": number(
                        getattr(row, "controlled_circuit_dp_pa", None),
                        " Pa",
                        1,
                    ),
                    "authority": number(
                        getattr(row, "authority", None),
                        "",
                        3,
                    ),
                    "ready": "Yes" if bool(getattr(row, "ready", False)) else "No",
                    "status": str(getattr(row, "status", "") or "—"),
                    "blockers": "; ".join(str(value) for value in blockers)
                    if blockers
                    else "—",
                }
            )
        return display_rows

    def _build_schematic_balancing_point_evidence_v1(
            self,
            mapping,
    ) -> tuple[CommonMainLegSublegBalancingPointEvidenceV1, ...]:
        return tuple(
            CommonMainLegSublegBalancingPointEvidenceV1(
                balancing_point_id=str(row.get("balancing_point_id", "") or ""),
                point_scope=str(row.get("point_scope", "") or ""),
                point_role=str(row.get("point_role", "") or ""),
                target_id=str(row.get("target_id", "") or ""),
                label=str(row.get("label", "") or ""),
                topology=str(row.get("topology", "") or ""),
                governed_routes=str(row.get("governed_routes", "") or ""),
                point_flow=str(row.get("point_flow", "") or ""),
                allocated_dp=str(row.get("allocated_dp", "") or ""),
                resistance=str(row.get("resistance", "") or ""),
                method=str(row.get("method", "") or ""),
                valve_duty=str(row.get("valve_duty", "") or ""),
                required_kv=str(row.get("required_kv", "") or ""),
                kvs_candidates=str(row.get("kvs_candidates", "") or ""),
                kvs_utilisation=str(row.get("kvs_utilisation", "") or ""),
                controlled_dp=str(row.get("controlled_dp", "") or ""),
                authority=str(row.get("authority", "") or ""),
                ready=str(row.get("ready", "") or ""),
                status=str(row.get("status", "") or ""),
            )
            for row in self._build_balancing_point_gui_rows_v1(mapping)
        )

    def _build_balancing_method_candidate_rows_v1(
            self,
            mapping,
    ) -> list[dict]:
        """
        H-S31-D:
        Convert balancing method candidate mapping into Proportioned-tab rows.

        Read-only display:
            no ProjectState mutation
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no pump selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        candidates = tuple(
            getattr(mapping, "candidates", ()) or ()
        )

        rows: list[dict] = []

        for candidate in candidates:
            required_added_dp_pa = getattr(
                candidate,
                "required_added_dp_pa",
                None,
            )
            flow_kg_s = getattr(candidate, "flow_kg_s", None)
            resistance = getattr(
                candidate,
                "resistance_pa_per_kg_s2",
                None,
            )
            blockers = tuple(getattr(candidate, "blockers", ()) or ())

            rows.append(
                {
                    "route": str(getattr(candidate, "route", "—") or "—"),
                    "method": str(
                        getattr(candidate, "method_label", "—") or "—"
                    ),
                    "ready": (
                        "Yes"
                        if bool(getattr(candidate, "ready", False))
                        else "No"
                    ),
                    "controlling": (
                        "Yes"
                        if bool(getattr(candidate, "controlling", False))
                        else "No"
                    ),
                    "required_added_dp": self._format_pa(
                        required_added_dp_pa
                    ),
                    "flow_kg_s": (
                        f"{float(flow_kg_s):.4f}"
                        if flow_kg_s is not None
                        else "—"
                    ),
                    "resistance_pa_per_kg_s2": (
                        f"{float(resistance):.1f}"
                        if resistance is not None
                        else "—"
                    ),
                    "status": str(
                        getattr(candidate, "status", "—") or "—"
                    ),
                    "blockers": (
                        "; ".join(str(blocker) for blocker in blockers)
                        if blockers
                        else "—"
                    ),
                }
            )

        if not rows:
            rows.append(
                {
                    "route": "—",
                    "method": "—",
                    "ready": "No",
                    "controlling": "No",
                    "required_added_dp": "—",
                    "flow_kg_s": "—",
                    "resistance_pa_per_kg_s2": "—",
                    "status": (
                        "Waiting for balancing method candidate evidence"
                    ),
                    "blockers": "—",
                }
            )

        return rows

    def _build_valve_authority_preview_v1(
            self,
            *,
            valve_authority_input_mapping,
            route_pressure_rows,
    ):
        """
        H-S32-G:
        Adapter wrapper for H-S32-F valve authority preview calculation.

        Preview only:
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no manufacturer valve data
            no pump selection
            no final balancing
            no pipe resizing
            no ProjectState mutation
        """
        return build_valve_authority_preview_v1(
            valve_authority_input_mapping=valve_authority_input_mapping,
            route_pressure_rows=route_pressure_rows,
        )

    def _build_clean_proportioned_route_status_v1(
            self,
            *,
            burden_row: dict,
            authority_label: str = "",
            authority_status: str = "",
    ) -> str:
        """
        H-S33-F:
        Build compact report-style status text for the clean Proportioned
        route-output table.

        Wording polish only:
            no ProjectState mutation
            no new pressure calculation
            no valve product selection
            no Kv / Kvs selection
            no pump selection
            no final balancing
            no pipe resizing
        """
        burden_status = str(burden_row.get("status", "") or "").lower()
        added_dp = str(
            burden_row.get("required_added_dp")
            or burden_row.get("added_dp")
            or ""
        ).strip()
        label = str(authority_label or "").lower()
        auth_status = str(authority_status or "").lower()

        is_controlling = (
            "controlling route" in burden_status
            or added_dp in {"0.0 Pa", "0 Pa", "0.0", "0", "—", "-"}
        )

        if "no valve authority required" in label:
            if is_controlling:
                return "Controlling route — no added Δp; no authority required"
            return "No added Δp preview — no authority required"

        if "too low" in label or "below preview minimum" in auth_status:
            return "Added Δp preview — low authority warning"

        if "high throttling" in label or "high throttling" in auth_status:
            return "Added Δp preview — high throttling warning"

        if "acceptable" in label:
            return "Added Δp preview — authority acceptable"

        if "manual review" in label or "blocked" in auth_status:
            return "Added Δp preview — manual review required"

        if is_controlling:
            return "Controlling route — no added Δp"

        if added_dp and added_dp not in {"—", "-"}:
            return "Added Δp preview"

        return "Preview route output evidence only"

    def _clean_proportioned_adapter_first_value_v1(
            self,
            row: dict,
            *keys: str,
    ) -> str:
        """
        H-S33-M:
        Read the first available display value from an adapter evidence row.

        Display mapping only:
            no new hydraulic calculation
            no ProjectState mutation
            no pipe resizing
        """
        if not isinstance(row, dict):
            return "—"

        for key in keys:
            if key in row and row.get(key) not in (None, ""):
                return str(row.get(key)).strip()

        wanted = {
            str(key or "").strip().lower()
            for key in keys
        }

        for row_key, value in row.items():
            if str(row_key or "").strip().lower() in wanted:
                if value not in (None, ""):
                    return str(value).strip()

        return "—"

    def _clean_proportioned_adapter_iter_display_value_v1(
            self,
            *,
            row: dict,
            raw_iter: object,
            status: object = "",
    ) -> str:
        """
        H-S33-M5:
        Display Iter only when adapter evidence explicitly represents a
        Colebrook friction solve.

        Iter means Colebrook iteration count only.
        """
        iter_text = str(raw_iter or "").strip()

        if not iter_text or iter_text in {"—", "-"}:
            return "—"

        evidence_parts: list[str] = []

        for key in (
            "friction_method",
            "Friction method",
            "method",
            "Method",
            "solver",
            "Solver",
            "status",
            "Status",
            "friction_status",
            "Friction status",
            "calculation_method",
            "Calculation method",
            "source",
            "Source",
            "note",
            "Note",
            "notes",
            "Notes",
        ):
            if key in row and row.get(key) not in (None, ""):
                evidence_parts.append(str(row.get(key)))

        if status:
            evidence_parts.append(str(status))

        evidence_text = " ".join(evidence_parts).lower()

        if "colebrook" not in evidence_text:
            return "—"

        return iter_text



    def _normalise_clean_proportioned_adapter_section_row_v1(
            self,
            row: dict,
    ) -> dict:
        """
        H-S33-M:
        Normalise adapter-held pipe/section evidence into the focused
        clean Proportioned section-table schema.

        Adapter wiring only:
            no new hydraulic calculation
            no valve product / Kv / Kvs
            no pump selection
            no pipe resizing
            no ProjectState mutation
        """
        # H-S36-A1 — explicit section-evidence delivery.
        # Preserve stable identity alongside display text. Identity inference
        # is deterministic and does not model branch take-off geometry.
        identity = infer_section_route_identity_v1(row)

        def stable_value(value: object, inferred: object = "") -> str:
            text = str(value or "").strip()

            if text and text not in {"—", "-"}:
                return text

            inferred_text = str(inferred or "").strip()
            return inferred_text or "—"

        route = self._clean_proportioned_adapter_first_value_v1(
            row,
            "route",
            "Route",
            "route_label",
            "Route label",
            "subleg",
            "Subleg",
            "subleg_label",
            "Subleg label",
            "target",
            "Target",
            "scope",
            "Scope",
        )
        route = stable_value(
            route,
            identity.route_code or identity.subleg_id,
        )

        section_id = self._clean_proportioned_adapter_first_value_v1(
            row,
            "section_id",
        )

        return {
            "route": route,
            "section_id": stable_value(section_id),
            "route_code": stable_value(
                row.get("route_code"),
                identity.route_code,
            ),
            "leg_id": stable_value(
                row.get("leg_id"),
                identity.leg_id,
            ),
            "subleg_id": stable_value(
                row.get("subleg_id"),
                identity.subleg_id,
            ),
            "route_id": stable_value(
                row.get("route_id"),
                identity.route_id,
            ),
            "subleg_role": stable_value(
                row.get("subleg_role"),
                identity.subleg_role,
            ),
            "takeoff_status": stable_value(
                row.get("takeoff_status"),
                identity.takeoff_status,
            ),
            "section": self._clean_proportioned_adapter_first_value_v1(
                row,
                "section",
                "Section",
                "order",
                "Order",
                "section_label",
                "section_id",
            ),
            "from": self._clean_proportioned_adapter_first_value_v1(
                row,
                "from",
                "From",
                "from_label",
                "from_node",
            ),
            "to": self._clean_proportioned_adapter_first_value_v1(
                row,
                "to",
                "To",
                "to_label",
                "to_node",
            ),
            "flow_kg_s": self._clean_proportioned_adapter_first_value_v1(
                row,
                "flow_kg_s",
                "Flow kg/s",
                "flow",
                "mass_flow_kg_s",
            ),
            "pipe_dn": self._clean_proportioned_adapter_first_value_v1(
                row,
                "pipe_dn",
                "Pipe DN",
                "pipe",
                "Pipe",
                "dn",
            ),
            "dp_per_m": self._clean_proportioned_adapter_first_value_v1(
                row,
                "dp_per_m",
                "Δp/m",
                "dp_m",
                "pressure_gradient",
            ),
            "length": self._clean_proportioned_adapter_first_value_v1(
                row,
                "length",
                "Length",
                "length_m",
            ),
            "k": self._clean_proportioned_adapter_first_value_v1(
                row,
                "k",
                "K",
                "local_k",
                "k_total",
            ),
            "section_dp": self._clean_proportioned_adapter_first_value_v1(
                row,
                "section_dp",
                "Section Δp",
                "section_dp_pa",
                "total_dp",
            ),
            "iter": self._clean_proportioned_adapter_iter_display_value_v1(
                row=row,
                raw_iter=self._clean_proportioned_adapter_first_value_v1(
                    row,
                    "iter",
                    "Iter",
                    "colebrook_iter",
                    "colebrook_iterations",
                    "iteration_count",
                    "iterations",
                    "friction_iterations",
                ),
                status=self._clean_proportioned_adapter_first_value_v1(
                    row,
                    "status",
                    "Status",
                ),
            ),
            "status": self._clean_proportioned_adapter_first_value_v1(
                row,
                "status",
                "Status",
            ),
        }

    def _clean_proportioned_adapter_mapping_from_object_v1(
            self,
            value: object,
    ) -> dict:
        """
        H-S33-M:
        Convert dict-like/dataclass-like evidence objects to a mapping.
        """
        if isinstance(value, dict):
            return value

        if hasattr(value, "__dict__"):
            try:
                return dict(vars(value))
            except Exception:
                return {}

        return {}

    def _clean_proportioned_adapter_row_looks_like_section_v1(
            self,
            row: dict,
    ) -> bool:
        """
        H-S33-M:
        Identify pipe/section evidence rows without relying on one brittle
        adapter attribute name.
        """
        if not isinstance(row, dict):
            return False

        keys = {
            str(key or "").strip().lower()
            for key in row.keys()
        }

        has_from = bool(
            keys.intersection(
                {
                    "from",
                    "from_label",
                    "from_node",
                }
            )
        )
        has_to = bool(
            keys.intersection(
                {
                    "to",
                    "to_label",
                    "to_node",
                }
            )
        )
        has_section_evidence = bool(
            keys.intersection(
                {
                    "section",
                    "section_id",
                    "section_label",
                    "order",
                    "flow_kg_s",
                    "flow kg/s",
                    "mass_flow_kg_s",
                    "pipe_dn",
                    "pipe dn",
                    "dp_per_m",
                    "Δp/m",
                    "length",
                    "length_m",
                    "k",
                    "section_dp",
                    "section Δp",
                    "section_dp_pa",
                    "iter",
                    "colebrook_iter",
                    "colebrook_iterations",
                    "iteration_count",
                    "iterations",
                    "friction_iterations",
                }
            )
        )

        return has_from and has_to and has_section_evidence

    def _iter_clean_proportioned_adapter_section_rows_v1(
            self,
            value: object,
            *,
            depth: int = 0,
            seen: set[int] | None = None,
    ):
        """
        H-S33-M:
        Walk adapter evidence structures and yield section-like rows.

        Defensive traversal only. Qt/panel objects are not walked.
        """
        if seen is None:
            seen = set()

        if depth > 6:
            return

        value_id = id(value)

        if value_id in seen:
            return

        seen.add(value_id)

        if isinstance(value, dict):
            if self._clean_proportioned_adapter_row_looks_like_section_v1(
                    value
            ):
                yield self._normalise_clean_proportioned_adapter_section_row_v1(
                    value
                )

            for child in value.values():
                yield from self._iter_clean_proportioned_adapter_section_rows_v1(
                    child,
                    depth=depth + 1,
                    seen=seen,
                )
            return

        if isinstance(value, (list, tuple, set)):
            for child in value:
                yield from self._iter_clean_proportioned_adapter_section_rows_v1(
                    child,
                    depth=depth + 1,
                    seen=seen,
                )
            return

        mapping = self._clean_proportioned_adapter_mapping_from_object_v1(
            value
        )

        if mapping:
            yield from self._iter_clean_proportioned_adapter_section_rows_v1(
                mapping,
                depth=depth + 1,
                seen=seen,
            )

    def _clean_proportioned_adapter_section_source_objects_v1(self) -> list:
        """
        H-S33-M:
        Gather likely adapter-held section evidence sources.

        This deliberately avoids walking the panel/widget tree.
        """
        sources = []

        for attr_name, value in vars(self).items():
            attr_key = str(attr_name or "").lower()

            if attr_key in {
                "_panel",
                "panel",
                "_view",
                "view",
                "_window",
                "window",
            }:
                continue

            if any(
                    token in attr_key
                    for token in (
                        "section",
                        "snapshot",
                        "proportion",
                        "route",
                        "basis",
                        "preview",
                        "burden",
                        "pressure",
                        "input",
                    )
            ):
                sources.append(value)

        return sources

    def _build_clean_proportioned_focused_section_source_rows_v1(
            self,
            *,
            source_objects: list | None = None,
    ) -> list[dict]:
        """
        H-S33-M:
        Build focused pipe/section source rows for the clean Proportioned tab.

        This is adapter display wiring only:
            no ProjectState mutation
            no new hydraulic calculation
            no valve product / Kv / Kvs
            no pump selection
            no pipe resizing
        """
        if source_objects is None:
            source_objects = (
                self._clean_proportioned_adapter_section_source_objects_v1()
            )

        rows: list[dict] = []

        for source in source_objects:
            rows.extend(
                list(
                    self._iter_clean_proportioned_adapter_section_rows_v1(
                        source
                    )
                )
            )

        unique_rows: list[dict] = []
        seen_keys: set[tuple] = set()

        columns = (
            "route_id",
            "subleg_id",
            "section_id",
            "route",
            "section",
            "from",
            "to",
            "flow_kg_s",
            "pipe_dn",
            "dp_per_m",
            "length",
            "k",
            "section_dp",
            "iter",
            "status",
        )

        for row in rows:
            key = tuple(
                str(row.get(column, "") or "")
                for column in columns
            )

            if key in seen_keys:
                continue

            seen_keys.add(key)
            unique_rows.append(row)

        return unique_rows

    def _push_clean_proportioned_focused_section_source_rows_v1(self) -> None:
        """
        H-S33-M:
        Push adapter-held focused pipe/section source rows into the clean
        Proportioned panel section view.

        If no rows are available, the panel keeps its H-S33-L fallback /
        placeholder behaviour.
        """
        panel = getattr(self, "_panel", None)

        if panel is None:
            return

        if not hasattr(
                panel,
                "set_clean_proportioned_focused_section_source_rows_v1",
        ):
            return

        rows = self._build_clean_proportioned_focused_section_source_rows_v1()

        # H-S36-A3 — runtime section-evidence fallback.
        # The panel already owns the enriched Basic PS display snapshot. Use
        # it only when the adapter's defensive evidence scan finds no rows.
        # This remains read-only delivery; no calculation or ProjectState.
        if not rows:
            rows = [
                dict(row or {})
                for row in (
                    getattr(
                        panel,
                        "_proportioning_snapshot_section_rows",
                        [],
                    )
                    or []
                )
            ]

        # Preserve the existing panel fallback/placeholder when neither
        # explicit source contains section evidence.
        if not rows:
            return

        panel.set_clean_proportioned_focused_section_source_rows_v1(rows)



    def _build_clean_proportioned_route_output_rows_v1(
            self,
            *,
            provisional_burden_rows,
            valve_authority_preview,
    ) -> list[dict]:
        """
        Build the clean route table from committed H-S55-A results when
        available, otherwise retain the pre-commit H-S33 preview projection.

        Display projection only: no ProjectState mutation, pump selection,
        valve setting, pipe resizing or commissioning/final balancing.
        """

        def norm(value) -> str:
            return str(value or "").strip().lower()

        def text_or_dash(value) -> str:
            value = str(value or "").strip()
            return value if value else "—"

        def fmt_pa(value) -> str:
            try:
                number = float(value)
            except (TypeError, ValueError):
                return "—"
            # H-S55-B1: suppress negative zero at one-decimal display
            # precision without changing the committed numeric result.
            if abs(number) < 0.05:
                number = 0.0
            return f"{number:.1f} Pa"

        committed_result = getattr(
            self,
            "_committed_basis_route_proportioning_result_v1",
            None,
        )
        if committed_result is not None:
            committed_rows = list(
                getattr(committed_result, "rows", ()) or ()
            )
            if not committed_rows:
                return [
                    {
                        "route": "—",
                        "basis": "—",
                        "route_dp": "—",
                        "added_dp": "—",
                        "proportioned_dp": "—",
                        "target_dp": "—",
                        "residual_dp": "—",
                        "at_target": "No",
                        "status": text_or_dash(
                            getattr(committed_result, "status", "")
                        ),
                    }
                ]

            return [
                {
                    "route": text_or_dash(
                        getattr(row, "route_label", "")
                        or getattr(row, "route_id", "")
                    ),
                    "basis": text_or_dash(getattr(row, "basis", "")),
                    "route_dp": fmt_pa(
                        getattr(row, "chosen_pressure_drop_Pa", None)
                    ),
                    "added_dp": fmt_pa(
                        getattr(
                            row,
                            "required_added_pressure_drop_Pa",
                            None,
                        )
                    ),
                    "proportioned_dp": fmt_pa(
                        getattr(
                            row,
                            "proportioned_pressure_drop_Pa",
                            None,
                        )
                    ),
                    "target_dp": fmt_pa(
                        getattr(
                            row,
                            "controlling_target_pressure_drop_Pa",
                            None,
                        )
                    ),
                    "residual_dp": fmt_pa(
                        getattr(row, "residual_to_target_Pa", None)
                    ),
                    "at_target": (
                        "Yes"
                        if bool(getattr(row, "within_tolerance", False))
                        else "No"
                    ),
                    "status": text_or_dash(getattr(row, "status", "")),
                }
                for row in committed_rows
            ]

        def fmt_authority(value) -> str:
            if value is None:
                return "—"
            try:
                return f"{float(value):.3f}"
            except (TypeError, ValueError):
                return "—"

        authority_by_route: dict[str, object] = {}
        for row in list(getattr(valve_authority_preview, "rows", ()) or ()):
            route = norm(getattr(row, "route", ""))
            if route:
                authority_by_route[route] = row

        clean_rows: list[dict] = []
        for burden_row in list(provisional_burden_rows or ()):
            route = text_or_dash(
                burden_row.get("route")
                or burden_row.get("route_label")
                or burden_row.get("route_id")
            )
            if route in {"", "—", "-"}:
                continue

            authority_row = authority_by_route.get(norm(route))
            authority_label = ""
            authority_status = ""
            if authority_row is not None:
                fmt_authority(getattr(authority_row, "authority", None))
                authority_label = str(
                    getattr(authority_row, "authority_label", "") or ""
                )
                authority_status = str(
                    getattr(authority_row, "status", "") or ""
                )

            clean_status = self._build_clean_proportioned_route_status_v1(
                burden_row=burden_row,
                authority_label=authority_label,
                authority_status=authority_status,
            )
            clean_rows.append(
                {
                    "route": route,
                    "basis": text_or_dash(burden_row.get("basis")),
                    "route_dp": text_or_dash(
                        burden_row.get("chosen_dp")
                        or burden_row.get("route_dp")
                        or burden_row.get("route_chosen_dp")
                    ),
                    "added_dp": text_or_dash(
                        burden_row.get("required_added_dp")
                        or burden_row.get("added_dp")
                    ),
                    "proportioned_dp": "—",
                    "target_dp": "—",
                    "residual_dp": "—",
                    "at_target": "Preview only",
                    "status": clean_status,
                    # Compatibility keys retained for focused H-S33 tests.
                    "sections": text_or_dash(
                        burden_row.get("sections")
                        or burden_row.get("section_count")
                    ),
                    "flow_kg_s": text_or_dash(
                        burden_row.get("flow_kg_s")
                        or burden_row.get("flow")
                    ),
                    "pipe_dn": text_or_dash(
                        burden_row.get("pipe_dn")
                        or burden_row.get("pipe")
                        or burden_row.get("pipe_size")
                    ),
                    "dp_per_m": text_or_dash(
                        burden_row.get("dp_per_m")
                        or burden_row.get("dp_m")
                        or burden_row.get("dp_per_m_label")
                    ),
                    "authority": (
                        fmt_authority(
                            getattr(authority_row, "authority", None)
                        )
                        if authority_row is not None
                        else "—"
                    ),
                }
            )

        return clean_rows

    def _build_valve_authority_preview_summary_status_v1(
            self,
            preview,
    ) -> str:
        """
        H-S32-I:
        Build top-level Proportioned-tab status text for valve authority
        preview evidence.

        Summary only:
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no manufacturer valve data
            no pump selection
            no final balancing
            no pipe resizing
            no ProjectState mutation
        """
        rows = list(getattr(preview, "rows", ()) or ())

        if not rows:
            return "Waiting for valve authority preview evidence"

        total = len(rows)
        not_required = 0
        calculated = 0
        low_warning = 0
        high_warning = 0
        acceptable = 0
        blocked = 0

        for row in rows:
            label = str(getattr(row, "authority_label", "") or "").lower()
            status = str(getattr(row, "status", "") or "").lower()
            authority = getattr(row, "authority", None)
            blockers = tuple(getattr(row, "blockers", ()) or ())

            if "no valve authority required" in label:
                not_required += 1
                continue

            if blockers or not bool(getattr(row, "ready", False)):
                blocked += 1
                continue

            if authority is not None:
                calculated += 1

            if "too low" in label or "below preview minimum" in status:
                low_warning += 1
            elif "high throttling" in label or "high throttling" in status:
                high_warning += 1
            elif "acceptable" in label:
                acceptable += 1

        parts: list[str] = []

        if calculated:
            parts.append(f"{calculated} calculated")

        if acceptable:
            parts.append(f"{acceptable} acceptable")

        if not_required:
            parts.append(f"{not_required} not required")

        if low_warning:
            parts.append(f"{low_warning} low-authority warning")

        if high_warning:
            parts.append(f"{high_warning} high-throttling warning")

        if blocked:
            parts.append(f"{blocked} blocked")

        if not parts:
            return "Waiting for valve authority preview evidence"

        prefix = "Ready"
        if blocked:
            prefix = "Blocked"
        elif low_warning or high_warning:
            prefix = "Ready with warnings"

        return f"{prefix} — " + ", ".join(parts)

    def _build_valve_authority_preview_rows_v1(
            self,
            preview,
    ) -> list[dict]:
        """
        H-S32-H:
        Build display rows for the calculated valve authority preview.

        Display only:
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no manufacturer valve data
            no pump selection
            no final balancing
            no pipe resizing
            no ProjectState mutation
        """

        def fmt_pa(value) -> str:
            if value is None:
                return "—"

            try:
                return f"{float(value):.1f} Pa"
            except (TypeError, ValueError):
                return "—"

        def fmt_flow(value) -> str:
            if value is None:
                return "—"

            try:
                return f"{float(value):.4f}"
            except (TypeError, ValueError):
                return "—"

        def fmt_resistance(value) -> str:
            if value is None:
                return "—"

            try:
                return f"{float(value):.1f}"
            except (TypeError, ValueError):
                return "—"

        def fmt_authority(value) -> str:
            if value is None:
                return "—"

            try:
                return f"{float(value):.3f}"
            except (TypeError, ValueError):
                return "—"

        rows = list(getattr(preview, "rows", ()) or ())

        if not rows:
            return [
                {
                    "route": "—",
                    "balancing_method": "—",
                    "authority_state": "Waiting for authority preview",
                    "ready": "No",
                    "design_valve_dp": "—",
                    "flow_kg_s": "—",
                    "candidate_resistance": "—",
                    "controlled_circuit_dp": "—",
                    "authority": "—",
                    "status": "Waiting for valve authority preview evidence",
                    "blockers": "—",
                }
            ]

        display_rows: list[dict] = []

        for row in rows:
            blockers = tuple(getattr(row, "blockers", ()) or ())

            display_rows.append(
                {
                    "route": str(getattr(row, "route", "—") or "—"),
                    "balancing_method": str(
                        getattr(row, "balancing_method_label", "—") or "—"
                    ),
                    "authority_state": str(
                        getattr(row, "authority_label", "—") or "—"
                    ),
                    "ready": (
                        "Yes"
                        if bool(getattr(row, "ready", False))
                        else "No"
                    ),
                    "design_valve_dp": fmt_pa(
                        getattr(row, "design_valve_dp_pa", None)
                    ),
                    "flow_kg_s": fmt_flow(
                        getattr(row, "route_flow_kg_s", None)
                    ),
                    "candidate_resistance": fmt_resistance(
                        getattr(
                            row,
                            "candidate_resistance_pa_per_kg_s2",
                            None,
                        )
                    ),
                    "controlled_circuit_dp": fmt_pa(
                        getattr(row, "controlled_circuit_dp_pa", None)
                    ),
                    "authority": fmt_authority(
                        getattr(row, "authority", None)
                    ),
                    "status": str(getattr(row, "status", "") or "—"),
                    "blockers": (
                        "; ".join(str(item) for item in blockers)
                        if blockers
                        else "—"
                    ),
                }
            )

        return display_rows

    def _build_valve_authority_input_rows_v1(
            self,
            mapping,
    ) -> list[dict]:
        """
        H-S32-D:
        Convert valve authority input mapping into Proportioned-tab rows.

        Read-only display:
            no ProjectState mutation
            no authority ratio calculation here
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no manufacturer valve data
            no pump selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        input_rows = tuple(getattr(mapping, "rows", ()) or ())

        rows: list[dict] = []

        for input_row in input_rows:
            design_valve_dp_pa = getattr(
                input_row,
                "design_valve_dp_pa",
                None,
            )
            route_flow_kg_s = getattr(input_row, "route_flow_kg_s", None)
            candidate_resistance = getattr(
                input_row,
                "candidate_resistance_pa_per_kg_s2",
                None,
            )
            controlled_circuit_dp_pa = getattr(
                input_row,
                "controlled_circuit_dp_pa",
                None,
            )
            authority = getattr(input_row, "authority", None)
            blockers = tuple(getattr(input_row, "blockers", ()) or ())

            rows.append(
                {
                    "route": str(getattr(input_row, "route", "—") or "—"),
                    "balancing_method": str(
                        getattr(
                            input_row,
                            "balancing_method_label",
                            "—",
                        )
                        or "—"
                    ),
                    "authority_state": str(
                        getattr(input_row, "authority_label", "—") or "—"
                    ),
                    "ready": (
                        "Yes"
                        if bool(getattr(input_row, "ready", False))
                        else "No"
                    ),
                    "design_valve_dp": self._format_pa(
                        design_valve_dp_pa
                    ),
                    "flow_kg_s": (
                        f"{float(route_flow_kg_s):.4f}"
                        if route_flow_kg_s is not None
                        else "—"
                    ),
                    "candidate_resistance": (
                        f"{float(candidate_resistance):.1f}"
                        if candidate_resistance is not None
                        else "—"
                    ),
                    "controlled_circuit_dp": self._format_pa(
                        controlled_circuit_dp_pa
                    ),
                    "authority": (
                        f"{float(authority):.3f}"
                        if authority is not None
                        else "—"
                    ),
                    "status": str(
                        getattr(input_row, "status", "—") or "—"
                    ),
                    "blockers": (
                        "; ".join(str(blocker) for blocker in blockers)
                        if blockers
                        else "—"
                    ),
                }
            )

        if not rows:
            rows.append(
                {
                    "route": "—",
                    "balancing_method": "—",
                    "authority_state": "—",
                    "ready": "No",
                    "design_valve_dp": "—",
                    "flow_kg_s": "—",
                    "candidate_resistance": "—",
                    "controlled_circuit_dp": "—",
                    "authority": "—",
                    "status": "Waiting for valve authority input evidence",
                    "blockers": "—",
                }
            )

        return rows

    def _build_valve_authority_input_mapping_preview_v1(
            self,
            *,
            balancing_candidate_mapping=None,
    ):
        """
        H-S32-C:
        Build valve-authority input mapping from the adapter's
        balancing method candidate mapping.

        Adapter-memory only:
            no ProjectState mutation
            no panel output
            no file export
            no authority ratio calculation yet
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no manufacturer valve data
            no pump selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        return build_valve_authority_input_mapping_v1(
            balancing_candidate_mapping
        )

    def _build_balancing_method_candidate_mapping_preview_v1(
            self,
            *,
            provisional_burden_rows=None,
    ):
        """
        H-S31-C:
        Build route-level balancing method candidates from the
        Proportioned-tab provisional burden rows.

        Adapter-memory only:
            no ProjectState mutation
            no panel output
            no file export
            no valve product selection
            no Kv / Kvs selection
            no lockshield turn count
            no pump selection
            no final balancing
            no pipe resizing
            no final hydraulic result
        """
        return build_balancing_method_candidate_mapping_v1(
            provisional_burden_rows or ()
        )

    def _build_basis_only_proportioned_export_payload_preview_v1(
            self,
            *,
            resolution=None,
            chosen_preview_rows=None,
            chosen_controlling_rows=None,
            provisional_burden_rows=None,
    ):
        """
        H-S30-I:
        Build basis-only Proportioned export payload preview from the
        adapter evidence already feeding the Proportioned tab.

        Adapter-memory only:
            no ProjectState mutation
            no file export
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

        resolved_rows = tuple(
            getattr(resolution, "rows", ()) or ()
        )

        return build_basis_only_proportioned_export_payload_preview_v1(
            snapshot=snapshot,
            resolved_return_arrangement_basis_rows=resolved_rows,
            chosen_basis_route_pressure_rows=chosen_preview_rows or (),
            chosen_basis_controlling_shortfall_rows=(
                chosen_controlling_rows or ()
            ),
            provisional_proportioning_burden_rows=(
                provisional_burden_rows or ()
            ),
        )

    @staticmethod
    def _build_committed_point_valve_basis_detail_rows_v1(
            snapshot,
    ) -> list[dict]:
        """Flatten only frozen H-S51-B point-valve basis evidence."""
        if snapshot is None:
            return []

        rows = []
        for source in tuple(
                getattr(snapshot, "committed_point_valve_bases", ()) or ()
        ):
            point_id = str(
                getattr(source, "balancing_point_id", "") or ""
            ).strip()
            accepted_kvs = getattr(source, "accepted_kvs_basis", None)
            try:
                accepted_kvs_text = f"{float(accepted_kvs):.3f}"
            except (TypeError, ValueError):
                accepted_kvs_text = "—"

            disposition_id = str(
                getattr(source, "disposition", "") or ""
            ).strip()
            disposition = (
                "Approved for later product search"
                if disposition_id == "approved_for_product_search"
                else (
                    disposition_id.replace("_", " ").capitalize()
                    if disposition_id
                    else "—"
                )
            )
            rows.append(
                {
                    "balancing_point_id": point_id or "—",
                    "accepted_kvs": accepted_kvs_text,
                    "disposition": disposition,
                    "status": (
                        "Committed basis only — no valve product selected"
                    ),
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
        """Add H-S55-A committed-route status to the existing summary."""
        rows = self._build_preview_proportioned_output_status_rows_v1(
            resolution=resolution,
            chosen_preview_rows=chosen_preview_rows,
            chosen_controlling_rows=chosen_controlling_rows,
            readiness_rows=readiness_rows,
        )
        result = getattr(
            self,
            "_committed_basis_route_proportioning_result_v1",
            None,
        )
        if result is None:
            return rows

        output = [dict(row or {}) for row in rows]
        for row in output:
            if str(row.get("item") or "") != "Accepted return basis":
                continue
            status = str(row.get("status") or "")
            status = status.replace(
                " — basis only; final hydraulics not committed",
                " — committed hydraulic route basis",
            )
            row["status"] = status

        status = str(getattr(result, "status", "") or "—")
        status += (
            " — no pump, valve setting, pipe resizing or final "
            "commissioning"
        )
        output.append(
            {
                "item": "Committed route result",
                "status": status,
            }
        )
        return output

    def _build_preview_proportioned_output_status_rows_v1(
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

        if snapshot is not None:
            basis_only_output_ready = bool(
                getattr(snapshot, "basis_only_output_ready", False)
            )
            basis_only_output_status = str(
                getattr(snapshot, "basis_only_output_status", "") or ""
            ).strip()

            if basis_only_output_ready:
                export_status = (
                    basis_only_output_status
                    or (
                        "Ready for basis-only Proportioned output export — "
                        "final hydraulics not included"
                    )
                )
            else:
                export_status = (
                    basis_only_output_status
                    or "Not ready for basis-only Proportioned output export"
                )
        else:
            export_status = (
                "Not ready — commit accepted basis snapshot before "
                "basis-only Proportioned output export"
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
                "item": "Committed point-valve basis",
                "status": (
                    str(
                        getattr(
                            snapshot,
                            "point_valve_basis_status",
                            "No committed point-valve basis evidence",
                        )
                    )
                    if snapshot is not None
                    else "Not committed — point-valve basis remains preview"
                ),
            },
            {
                "item": "Basis-only export",
                "status": (
                    f"{export_status}; pump, valve selection, final "
                    "balancing, and pipe resizing not performed"
                ),
            },
            {
                "item": "Valve authority preview",
                "status": self._build_valve_authority_preview_summary_status_v1(
                    getattr(self, "_valve_authority_preview", None)
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
        has_provisional_burden_table = hasattr(
            self._panel,
            "set_provisional_proportioning_burden_rows",
        )
        has_balancing_method_candidate_table = hasattr(
            self._panel,
            "set_balancing_method_candidate_rows",
        )
        has_valve_authority_input_table = hasattr(
            self._panel,
            "set_valve_authority_input_rows",
        )
        has_balancing_point_evidence_table = hasattr(
            self._panel,
            "set_balancing_point_evidence_rows",
        )
        has_proportioned_status_table = hasattr(
            self._panel,
            "set_proportioned_status",
        )
        has_committed_point_valve_basis_detail_table = hasattr(
            self._panel,
            "set_committed_point_valve_basis_detail_rows",
        )

        if (
                not has_resolved_table
                and not has_chosen_table
                and not has_controlling_table
                and not has_readiness_table
                and not has_provisional_burden_table
                and not has_balancing_method_candidate_table
                and not has_valve_authority_input_table
                and not has_balancing_point_evidence_table
                and not has_proportioned_status_table
                and not has_committed_point_valve_basis_detail_table
        ):
            return

        if has_committed_point_valve_basis_detail_table:
            committed_snapshot = getattr(
                self._project_state,
                "hydronic_proportioned_basis_snapshot",
                None,
            )
            committed_authority = getattr(
                committed_snapshot,
                "hydraulic_input_authority",
                None,
            )
            self._committed_basis_route_proportioning_result_v1 = (
                build_committed_basis_route_proportioning_result_v1(
                    committed_authority
                )
                if committed_authority is not None
                else None
            )
            if hasattr(
                self._panel,
                "set_commit_proportioning_committed",
            ):
                self._panel.set_commit_proportioning_committed(
                    committed=bool(
                        getattr(
                            committed_snapshot,
                            "hydraulic_input_authority",
                            None,
                        )
                    )
                )
            self._panel.set_committed_point_valve_basis_detail_rows(
                self._build_committed_point_valve_basis_detail_rows_v1(
                    committed_snapshot
                )
            )

        self._committed_hydraulic_chosen_controlling_rows_v1 = ()
        self._committed_hydraulic_resistance_basis_v1 = None

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

            chosen_resistance_basis = (
                build_chosen_basis_balancing_resistance_basis_v1(
                    chosen_controlling_rows=chosen_controlling_rows,
                    flow_basis=(
                        getattr(
                            self,
                            "_received_basic_ps_route_flow_basis_v1",
                            None,
                        )
                    ),
                )
            )
            self._committed_hydraulic_chosen_controlling_rows_v1 = tuple(
                chosen_controlling_rows or ()
            )
            self._committed_hydraulic_resistance_basis_v1 = (
                chosen_resistance_basis
            )

            provisional_burden_rows = (
                self._build_provisional_proportioning_burden_rows_v1(
                    chosen_controlling_rows,
                    resistance_basis=chosen_resistance_basis,
                )
            )

            # H-S44-E — point-scoped evidence chain for display only.
            point_topology = build_balancing_point_topology_authority_v1(
                self._project_state
            )
            point_allocation = build_balancing_point_resistance_allocation_v1(
                topology=point_topology,
                resistance_basis=chosen_resistance_basis,
            )
            point_candidates = build_balancing_point_method_candidate_mapping_v1(
                point_allocation
            )
            point_valve_inputs = (
                build_balancing_point_valve_authority_input_mapping_v1(
                    point_candidates
                )
            )
            self._balancing_point_valve_authority_input_mapping_preview = (
                point_valve_inputs
            )
            point_controlled_circuit_dp = (
                build_balancing_point_controlled_circuit_dp_authority_v1(
                    point_valve_inputs,
                    chosen_preview_rows,
                )
            )
            self._balancing_point_controlled_circuit_dp_authority_preview = (
                point_controlled_circuit_dp
            )
            point_valve_authority = (
                build_balancing_point_valve_authority_preview_v1(
                    point_controlled_circuit_dp
                )
            )
            self._balancing_point_valve_authority_preview = (
                point_valve_authority
            )
            point_design_disposition = (
                build_balancing_point_low_authority_design_disposition_v1(
                    point_valve_authority
                )
            )
            self._balancing_point_low_authority_design_disposition_preview = (
                point_design_disposition
            )
            point_valve_duty_basis = (
                build_balancing_point_valve_duty_design_basis_v1(
                    point_design_disposition
                )
            )
            self._balancing_point_valve_duty_design_basis_preview = (
                point_valve_duty_basis
            )
            point_required_kv = build_balancing_point_required_kv_preview_v1(
                point_valve_duty_basis
            )
            self._balancing_point_required_kv_preview = point_required_kv
            point_kvs_candidates = (
                build_balancing_point_kvs_candidate_evidence_v1(
                    point_required_kv
                )
            )
            self._balancing_point_kvs_candidate_evidence_preview = (
                point_kvs_candidates
            )
            point_kvs_utilisation = (
                build_balancing_point_kvs_candidate_utilisation_evidence_v1(
                    point_kvs_candidates
                )
            )
            self._balancing_point_kvs_utilisation_evidence_preview = (
                point_kvs_utilisation
            )
            point_kvs_acceptance = (
                resolve_balancing_point_kvs_candidate_acceptance_v1(
                    getattr(
                        self._project_state,
                        "hydronic_point_kvs_candidate_acceptance_intent",
                        None,
                    ),
                    point_kvs_utilisation,
                )
            )
            self._balancing_point_kvs_candidate_acceptance_resolution = (
                point_kvs_acceptance
            )
            point_kvs_consequence = (
                build_balancing_point_accepted_kvs_hydraulic_consequence_v1(
                    point_kvs_utilisation,
                    point_kvs_acceptance,
                )
            )
            self._balancing_point_accepted_kvs_hydraulic_consequence_preview = (
                point_kvs_consequence
            )
            point_kvs_consequence_disposition = (
                resolve_balancing_point_accepted_kvs_consequence_disposition_v1(
                    getattr(
                        self._project_state,
                        "hydronic_point_accepted_kvs_consequence_disposition_intent",
                        None,
                    ),
                    point_kvs_consequence,
                )
            )
            self._balancing_point_accepted_kvs_consequence_disposition_resolution = (
                point_kvs_consequence_disposition
            )
            point_commit_readiness = (
                build_point_proportioning_commit_readiness_v1(
                    point_kvs_consequence_disposition
                )
            )
            self._point_proportioning_commit_readiness_v1 = (
                point_commit_readiness
            )
            basic_commit_readiness = build_proportioning_readiness_v1(
                self._project_state
            )
            basic_commit_ready = bool(
                basic_commit_readiness.return_arrangement_basis_ready
            )
            if hasattr(self._panel, "set_commit_proportioning_ready"):
                self._panel.set_commit_proportioning_ready(
                    ready=(
                        basic_commit_ready and point_commit_readiness.ready
                    ),
                    reason=(
                        point_commit_readiness.status
                        if basic_commit_ready
                        else basic_commit_readiness.proportioning_status
                    ),
                )
            point_product_search_envelopes = (
                build_balancing_point_valve_product_search_duty_envelope_v1(
                    point_kvs_utilisation,
                    point_kvs_consequence,
                    point_kvs_consequence_disposition,
                )
            )
            self._balancing_point_valve_product_search_duty_envelope_preview = (
                point_product_search_envelopes
            )
            point_product_search_criteria = (
                resolve_balancing_point_valve_product_search_criteria_v1(
                    getattr(
                        self._project_state,
                        "hydronic_point_valve_product_search_criteria_intent",
                        None,
                    ),
                    point_product_search_envelopes,
                )
            )
            self._balancing_point_valve_product_search_criteria_resolution = (
                point_product_search_criteria
            )
            point_catalogue_candidate_matches = (
                build_balancing_point_valve_catalogue_candidate_match_evidence_v1(
                    point_product_search_envelopes,
                    point_product_search_criteria,
                    getattr(self, "_supplied_valve_catalog_dto_v1", None),
                )
            )
            self._balancing_point_valve_catalogue_candidate_match_evidence = (
                point_catalogue_candidate_matches
            )
            point_valve_candidate_acceptance = (
                resolve_balancing_point_valve_candidate_acceptance_v1(
                    getattr(
                        self._project_state,
                        "hydronic_point_valve_candidate_acceptance_intent",
                        None,
                    ),
                    point_catalogue_candidate_matches,
                )
            )
            self._balancing_point_valve_candidate_acceptance_resolution = (
                point_valve_candidate_acceptance
            )
            point_valve_candidate_consequence = (
                build_balancing_point_accepted_valve_candidate_hydraulic_consequence_v1(
                    point_product_search_envelopes,
                    point_valve_candidate_acceptance,
                )
            )
            self._balancing_point_accepted_valve_candidate_hydraulic_consequence_preview = (
                point_valve_candidate_consequence
            )
            point_valve_candidate_consequence_disposition = (
                resolve_balancing_point_accepted_valve_candidate_consequence_disposition_v1(
                    getattr(
                        self._project_state,
                        "hydronic_point_accepted_valve_candidate_"
                        "consequence_disposition_intent",
                        None,
                    ),
                    point_valve_candidate_consequence,
                )
            )
            self._balancing_point_accepted_valve_candidate_consequence_disposition_resolution = (
                point_valve_candidate_consequence_disposition
            )
            approved_valve_candidate_design_duties = (
                build_balancing_point_approved_valve_candidate_design_duty_envelope_v1(
                    point_product_search_envelopes,
                    point_valve_candidate_consequence,
                    point_valve_candidate_consequence_disposition,
                )
            )
            self._balancing_point_approved_valve_candidate_design_duty_envelope_preview = (
                approved_valve_candidate_design_duties
            )
            point_display_rows = self._build_balancing_point_gui_rows_v1(
                point_kvs_utilisation
            )
            point_display_rows = (
                self._enrich_balancing_point_gui_rows_with_kvs_consequence_v1(
                    point_display_rows,
                    point_kvs_consequence,
                )
            )
            point_display_rows = (
                self._enrich_balancing_point_gui_rows_with_kvs_disposition_v1(
                    point_display_rows,
                    point_kvs_consequence_disposition,
                )
            )
            if not point_display_rows and tuple(
                    getattr(point_allocation, "rows", ()) or ()
            ):
                point_display_rows = (
                    self._build_blocked_balancing_point_allocation_gui_rows_v1(
                        point_allocation
                    )
                )
            self._schematic_balancing_point_evidence_v1 = (
                self._build_schematic_balancing_point_evidence_v1(
                    point_kvs_utilisation
                )
            )
            if has_balancing_point_evidence_table:
                self._panel.set_balancing_point_evidence_rows(
                    point_display_rows
                )
            if hasattr(
                    self._panel,
                    "set_balancing_point_kvs_acceptance_editor_rows",
            ):
                self._panel.set_balancing_point_kvs_acceptance_editor_rows(
                    self._build_balancing_point_kvs_acceptance_editor_rows_v1(
                        point_display_rows=point_display_rows,
                        utilisation_evidence=point_kvs_utilisation,
                        acceptance_resolution=point_kvs_acceptance,
                        consequence_evidence=point_kvs_consequence,
                        disposition_resolution=point_kvs_consequence_disposition,
                    )
                )

            if hasattr(
                    self._panel,
                    "set_product_search_duty_envelope_rows",
            ):
                self._panel.set_product_search_duty_envelope_rows(
                    self._build_product_search_duty_envelope_gui_rows_v1(
                        point_product_search_envelopes
                    )
                )

            if hasattr(
                    self._panel,
                    "set_product_search_criteria_editor_rows",
            ):
                self._panel.set_product_search_criteria_editor_rows(
                    self._build_product_search_criteria_editor_rows_v1(
                        point_product_search_envelopes,
                        point_product_search_criteria,
                        available_catalog_ids=(
                            getattr(
                                getattr(
                                    self,
                                    "_supplied_valve_catalog_dto_v1",
                                    None,
                                ),
                                "catalog_id",
                                "",
                            ),
                        ),
                    )
                )

            if hasattr(
                    self._panel,
                    "set_catalogue_candidate_match_rows",
            ):
                self._panel.set_catalogue_candidate_match_rows(
                    self._build_catalogue_candidate_match_gui_rows_v1(
                        point_catalogue_candidate_matches
                    )
                )

            if hasattr(
                    self._panel,
                    "set_point_valve_candidate_acceptance_editor_rows",
            ):
                self._panel.set_point_valve_candidate_acceptance_editor_rows(
                    self._build_point_valve_candidate_acceptance_editor_rows_v1(
                        point_catalogue_candidate_matches,
                        point_valve_candidate_acceptance,
                        point_valve_candidate_consequence,
                        point_valve_candidate_consequence_disposition,
                    )
                )

            if hasattr(
                    self._panel,
                    "set_approved_valve_candidate_design_duty_envelope_rows",
            ):
                self._panel.set_approved_valve_candidate_design_duty_envelope_rows(
                    self._build_approved_valve_candidate_design_duty_gui_rows_v1(
                        approved_valve_candidate_design_duties
                    )
                )

            self._balancing_method_candidate_mapping_preview = (
                self._build_balancing_method_candidate_mapping_preview_v1(
                    provisional_burden_rows=provisional_burden_rows,
                )
            )

            self._valve_authority_input_mapping_preview = (
                self._build_valve_authority_input_mapping_preview_v1(
                    balancing_candidate_mapping=(
                        self._balancing_method_candidate_mapping_preview
                    ),
                )
            )

            self._valve_authority_preview = (
                self._build_valve_authority_preview_v1(
                    valve_authority_input_mapping=(
                        self._valve_authority_input_mapping_preview
                    ),
                    route_pressure_rows=(
                        locals().get("mappable_provisional_burden_rows")
                        or locals().get("provisional_burden_rows")
                        or ()
                    ),
                )
            )

            if has_balancing_method_candidate_table:
                self._panel.set_balancing_method_candidate_rows(
                    self._build_balancing_method_candidate_rows_v1(
                        self._balancing_method_candidate_mapping_preview
                    )
                )

            if has_valve_authority_input_table:
                self._panel.set_valve_authority_input_rows(
                    self._build_valve_authority_preview_rows_v1(
                        self._valve_authority_preview
                    )
                )

                if hasattr(
                        self._panel,
                        "set_clean_proportioned_route_output_rows",
                ):
                    self._panel.set_clean_proportioned_route_output_rows(
                        self._build_clean_proportioned_route_output_rows_v1(
                            provisional_burden_rows=(
                                locals().get("mappable_provisional_burden_rows")
                                or locals().get("provisional_burden_rows")
                                or ()
                            ),
                            valve_authority_preview=getattr(
                                self,
                                "_valve_authority_preview",
                                None,
                            ),
                        )
                    )

            self._basis_only_proportioned_export_payload_preview = (
                self._build_basis_only_proportioned_export_payload_preview_v1(
                    resolution=resolution,
                    chosen_preview_rows=chosen_preview_rows,
                    chosen_controlling_rows=chosen_controlling_rows,
                    provisional_burden_rows=provisional_burden_rows,
                )
            )

            if has_provisional_burden_table:
                self._panel.set_provisional_proportioning_burden_rows(
                    provisional_burden_rows
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

            if has_provisional_burden_table:
                self._panel.set_provisional_proportioning_burden_rows([])

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
                    room_evidence = tuple(
                        self._build_schematic_room_evidence_v1(room_id)
                        for room_id in room_labels
                    )

                    routes.append(
                        CommonMainLegSublegRouteV1(
                            leg_id=leg_id,
                            leg_label=leg_label,
                            subleg_id=subleg_id,
                            subleg_label=subleg_label,
                            role=role_label,
                            room_labels=room_labels,
                            room_evidence=room_evidence,
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
            balancing_point_evidence=tuple(
                getattr(
                    self,
                    "_schematic_balancing_point_evidence_v1",
                    (),
                )
                or ()
            ),
            status=(
                "DEV topology schematic preview only — branch take-offs are "
                "display-only TBA markers; no pressure, balancing, pump, "
                "valve, or pipe-resize result"
            ),
        )

    def _build_schematic_room_evidence_v1(
            self,
            room_id: str,
    ) -> CommonMainLegSublegRoomEvidenceV1:
        """
        H-S39-A — compose existing room authority evidence for display.

        The existing branch-aware carried-flow resolver remains the only
        emitter-flow authority used here. No rule-of-thumb pipe size is
        introduced and the schematic does not resize any section.
        """
        project = self._project_state
        stable_room_id = str(room_id or "")
        room = (getattr(project, "rooms", {}) or {}).get(stable_room_id)
        room_label = str(
            getattr(room, "name", None)
            or getattr(room, "label", None)
            or stable_room_id
            or "Room"
        )

        status_parts: list[str] = []
        heat_loss_W = None
        if bool(getattr(project, "heatloss_valid", False)):
            totals_reader = getattr(project, "get_room_heatloss_totals", None)
            if callable(totals_reader):
                totals = totals_reader(stable_room_id)
                if totals is not None:
                    heat_loss_W = float(totals[2])
        if heat_loss_W is None:
            status_parts.append("Heat-loss evidence unavailable or stale")

        room_emitters = [
            emitter
            for emitter in (getattr(project, "emitters", {}) or {}).values()
            if str(getattr(emitter, "room_id", "") or "") == stable_room_id
        ]
        emitter_labels = [
            str(
                getattr(emitter, "name", None)
                or getattr(emitter, "emitter_id", None)
                or "Emitter"
            )
            for emitter in room_emitters
        ]

        emitter_output_W = 0.0
        has_output = False
        for emitter in room_emitters:
            try:
                output = float(getattr(emitter, "design_output_W", None))
            except (TypeError, ValueError):
                continue
            if output > 0.0:
                emitter_output_W += output
                has_output = True

        if not room_emitters:
            status_parts.append("No assigned emitter")
        elif not has_output:
            status_parts.append("Emitter design output unavailable")

        try:
            emitter_flow_kg_s = _room_flow_kg_s(project, stable_room_id)
        except Exception:
            emitter_flow_kg_s = None
        if emitter_flow_kg_s is None:
            status_parts.append("Emitter design flow unavailable")

        return CommonMainLegSublegRoomEvidenceV1(
            room_id=stable_room_id,
            room_label=room_label,
            design_heat_loss_W=(
                "" if heat_loss_W is None else f"{heat_loss_W:.1f} W"
            ),
            emitter_summary=", ".join(emitter_labels),
            emitter_output_W=(
                "" if not has_output else f"{emitter_output_W:.1f} W"
            ),
            emitter_flow_kg_s=(
                ""
                if emitter_flow_kg_s is None
                else f"{float(emitter_flow_kg_s):.4f} kg/s"
            ),
            flow_basis=(
                ""
                if emitter_flow_kg_s is None
                else "Existing branch-aware carried-flow basis"
            ),
            status=(
                "; ".join(status_parts)
                if status_parts
                else "Read-only room design evidence"
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
                    "rr_added_length_m": getattr(
                        row, "rr_added_length_m", None
                    ),
                    "rr_added_length_basis_mode": getattr(
                        row,
                        "rr_added_length_basis_mode",
                        "physical_loop_zero_extra",
                    ),
                    "rr_added_length_source": getattr(
                        row, "rr_added_length_source", "system"
                    ),
                    "rr_added_length_inherited_from": getattr(
                        row, "rr_added_length_inherited_from", ""
                    ),
                    "rr_added_dp": self._format_pa(
                        getattr(row, "rr_added_pressure_drop_Pa", None)
                    ),
                    "rr_suitability": getattr(
                        row,
                        "rr_suitability_status",
                        "—",
                    ),
                    "missing_upstream_length_section_ids": tuple(
                        getattr(
                            row,
                            "missing_upstream_length_section_ids",
                            (),
                        ) or ()
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

            leg_id, subleg_id = (
                self._received_basic_ps_route_identity_v1(
                    result,
                    projection,
                )
            )

            subleg_role = (
                "common"
                if "primary-subleg" in subleg_id
                else "branch"
                if "subleg" in subleg_id
                else ""
            )

            takeoff_status = "TBA" if subleg_role == "branch" else ""

            environment = getattr(self._project_state, "environment", None)
            environment_max_velocity_m_s = getattr(
                environment,
                "basic_ps_max_velocity_m_s",
                1.0,
            )
            if environment_max_velocity_m_s is None:
                environment_max_velocity_m_s = 1.0

            sizing_intent = getattr(
                self._project_state,
                "basic_hydronic_sizing_intent",
                None,
            )
            velocity_overrides = getattr(
                sizing_intent,
                "section_max_velocity_overrides_m_s",
                {},
            ) or {}
            local_max_velocity_override_m_s = (
                velocity_overrides.get(section_id)
                if isinstance(velocity_overrides, dict)
                else None
            )

            rows.append(
                {
                    "leg_id": leg_id,
                    "subleg_id": subleg_id,
                    "route_id": subleg_id,
                    "route": route_label,
                    "subleg_role": subleg_role,
                    "takeoff_status": takeoff_status,
                    "section_id": section_id,
                    "environment_max_velocity_m_s": float(
                        environment_max_velocity_m_s
                    ),
                    "local_max_velocity_override_m_s": (
                        None
                        if local_max_velocity_override_m_s is None
                        else float(local_max_velocity_override_m_s)
                    ),
                    "applied_max_velocity_m_s": float(
                        getattr(result, "applied_max_velocity_m_s", 1.0)
                    ),
                    "max_velocity_source": str(
                        getattr(result, "max_velocity_source", "") or "—"
                    ),
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

                    # H-S37-B5 — keep Basic selection evidence explicit.
                    # Pipe selection is the velocity criterion. Haaland is
                    # the Basic first-pass friction / Δp estimate basis.
                    "basic_velocity_m_s": self._format_velocity(
                        getattr(result, "velocity_m_s", None)
                    ),
                    "basic_max_velocity_m_s": self._format_velocity(
                        getattr(result, "applied_max_velocity_m_s", None)
                    ),
                    "basic_velocity_source": str(
                        getattr(result, "max_velocity_source", "") or "—"
                    ),
                    "basic_friction_basis": (
                        "Velocity selection / Haaland Δp"
                    ),
                    "basic_dp_per_m": self._format_dp_per_m(
                        getattr(result, "pressure_gradient_Pa_per_m", None)
                    ),
                    "basic_friction_method": "Haaland",

                    # Proportioning evidence is populated only when the
                    # downstream route-section calculation exists. Do not
                    # disguise the Basic Haaland fallback as Proportioning.
                    "proportioning_velocity_m_s": (
                        self._format_velocity(
                            getattr(route_section, "velocity_m_s", None)
                        )
                        if route_section is not None
                        else "—"
                    ),
                    "proportioning_dp_per_m": (
                        self._format_dp_per_m(
                            getattr(
                                route_section,
                                "pressure_gradient_Pa_per_m",
                                None,
                            )
                        )
                        if route_section is not None
                        else "—"
                    ),
                    "proportioning_reynolds_number": (
                        self._format_reynolds_number(
                            getattr(route_section, "reynolds_number", None)
                        )
                        if route_section is not None
                        else "—"
                    ),
                    "proportioning_friction_factor": (
                        self._format_friction_factor(
                            getattr(route_section, "friction_factor", None)
                        )
                        if route_section is not None
                        else "—"
                    ),
                    "proportioning_friction_method": (
                        str(
                            getattr(route_section, "friction_method", "")
                            or "—"
                        )
                        if route_section is not None
                        else "—"
                    ),
                    "proportioning_colebrook_iterations": (
                        str(
                            getattr(
                                route_section,
                                "colebrook_iteration_count",
                                "—",
                            ) or "—"
                        )
                        if route_section is not None
                        else "—"
                    ),

                    # Legacy downstream keys remain for the clean
                    # Proportioned viewer and existing snapshot consumers.
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

        basic_commit_readiness = build_proportioning_readiness_v1(project)
        point_commit_readiness = build_point_proportioning_commit_readiness_v1(
            getattr(
                self,
                "_balancing_point_accepted_kvs_consequence_disposition_resolution",
                None,
            )
        )
        basic_commit_ready = bool(
            basic_commit_readiness.return_arrangement_basis_ready
        )
        if not basic_commit_ready or not point_commit_readiness.ready:
            reason = (
                point_commit_readiness.status
                if basic_commit_ready
                else basic_commit_readiness.proportioning_status
            )
            if hasattr(self._panel, "set_commit_proportioning_ready"):
                self._panel.set_commit_proportioning_ready(
                    ready=False,
                    reason=reason,
                )
            print("H-S51-A Commit Proportioning blocked:", reason)
            return

        hydraulic_input_authority = (
            build_committed_proportioning_hydraulic_input_authority_v1(
                route_pressure_projection=getattr(
                    self,
                    "_committed_hydraulic_route_pressure_projection_v1",
                    None,
                ),
                chosen_controlling_rows=getattr(
                    self,
                    "_committed_hydraulic_chosen_controlling_rows_v1",
                    (),
                ),
                resistance_basis=getattr(
                    self,
                    "_committed_hydraulic_resistance_basis_v1",
                    None,
                ),
            )
        )
        if not hydraulic_input_authority.ready:
            reason = hydraulic_input_authority.status
            if hasattr(self._panel, "set_commit_proportioning_ready"):
                self._panel.set_commit_proportioning_ready(
                    ready=False,
                    reason=reason,
                )
            print("H-S54-B Commit Proportioning blocked:", reason)
            return

        result = build_proportioned_basis_snapshot_v1(
            project,
            point_commit_readiness=point_commit_readiness,
            hydraulic_input_authority=hydraulic_input_authority,
        )

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
        project.hydronics_valid = False
        if hasattr(project, "mark_dirty"):
            project.mark_dirty()

        for signal_name in (
            "project_state_changed",
            "project_changed",
        ):
            signal = getattr(self._context, signal_name, None)
            emit = getattr(signal, "emit", None)
            if not callable(emit):
                continue
            try:
                emit()
            except TypeError:
                try:
                    emit(project)
                except TypeError:
                    pass

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
