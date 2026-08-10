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
from HVAC.hydronics.topology.topology_creation_candidate_v1 import (
    TopologyCreationCandidateV1,
    topology_creation_room_ids_v1,
    build_add_branch_subleg_candidate_v1,
    build_add_leg_with_principal_candidate_v1,
    build_add_principal_subleg_candidate_v1,
)
from HVAC.hydronics.topology.transactional_topology_editor_v1 import (
    commit_validated_topology_candidate_v1,
)
from HVAC.hydronics.topology.topology_room_placement_candidate_v1 import (
    RETURN_TO_STAGING_ACTION,
    TopologyRoomPlacementCandidateV1,
    build_place_topology_room_candidate_v1,
    build_return_topology_room_to_staging_candidate_v1,
)
from HVAC.hydronics.topology.topology_unassigned_room_inventory_v1 import (
    build_topology_unassigned_room_inventory_v1,
)
from HVAC.hydronics.topology.recursive_subleg_contract_v1 import (
    build_recursive_subleg_positions_v1,
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
        self._principal_subleg_id = ""
        self._branch_parent_subleg_id = ""
        self._branch_origin_room_id = ""
        self._branch_first_room_id = ""
        self._legacy_edit_subleg_id = ""
        self._last_transaction_status = ""
        self._last_creation_confirmation = ""
        self._topology_focus_room_id = ""

        self._subscribe_if_present("room_state_changed", self.refresh)
        self._subscribe_if_present("current_room_changed", self.refresh)
        self._subscribe_if_present("project_changed", self.refresh)
        self._panel.move_up_requested.connect(self._on_move_up_requested)
        self._panel.move_down_requested.connect(self._on_move_down_requested)
        self._panel.make_terminal_requested.connect(self._on_make_terminal_requested)
        self._panel.set_index_requested.connect(self._on_set_index_requested)
        self._panel.leg_selection_requested.connect(
            self._on_leg_selection_requested
        )
        self._panel.principal_selection_requested.connect(
            self._on_principal_selection_requested
        )
        self._panel.add_leg_requested.connect(self._on_add_leg_requested)
        self._panel.add_principal_requested.connect(
            self._on_add_principal_requested
        )
        self._panel.branch_parent_selection_requested.connect(
            self._on_branch_parent_selection_requested
        )
        self._panel.branch_origin_selection_requested.connect(
            self._on_branch_origin_selection_requested
        )
        self._panel.branch_first_room_selection_requested.connect(
            self._on_branch_first_room_selection_requested
        )
        self._panel.add_branch_requested.connect(
            self._on_add_branch_requested
        )
        self._panel.room_placement_requested.connect(
            self._on_room_placement_requested
        )
        self._panel.return_room_to_staging_requested.connect(
            self._on_return_room_to_staging_requested
        )
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
            self._panel.set_leg_options([], "")
            self._panel.set_principal_options([], "")
            self._panel.set_available_rooms([])
            self._panel.set_branch_parent_options([], "")
            self._panel.set_branch_origin_options([])
            self._panel.set_branch_first_room_options([])
            self._panel.set_creation_result("")
            self._panel.set_staging_rooms([])
            self._panel.set_topology_schematic(
                [], heat_source_label="Boiler / Heat Source"
            )
            self._panel.set_rows([])
            return

        self._ensure_dev_topology(project)
        self._push_topology_choices(project)

        try:
            projection = build_topology_arranger_projection_v1(
                project,
                leg_id=self._leg_id,
                principal_subleg_id=self._principal_subleg_id,
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
        self._principal_subleg_id = ""
        self._branch_parent_subleg_id = ""
        self._branch_origin_room_id = ""
        self._branch_first_room_id = ""
        self._topology_focus_room_id = ""
        self.refresh()

    def _push_topology_choices(self, project: Any) -> None:
        topology = project.hydronic_topology
        if not topology.legs:
            self._panel.set_leg_options([], "")
            self._panel.set_principal_options([], "")
            self._panel.set_available_rooms([])
            self._panel.set_branch_parent_options([], "")
            self._panel.set_branch_origin_options([])
            self._panel.set_branch_first_room_options([])
            self._panel.set_staging_rooms([])
            self._panel.set_topology_schematic(
                [], heat_source_label="Boiler / Heat Source"
            )
            return

        leg = next(
            (item for item in topology.legs if item.leg_id == self._leg_id),
            topology.legs[0],
        )
        self._leg_id = leg.leg_id
        positions = [
            item
            for item in build_recursive_subleg_positions_v1(topology)
            if item.leg_id == leg.leg_id
        ]
        selected_position = next(
            (
                item
                for item in positions
                if item.subleg_id == self._principal_subleg_id
            ),
            positions[0] if positions else None,
        )
        self._principal_subleg_id = (
            selected_position.subleg_id if selected_position is not None else ""
        )
        parent_position = next(
            (
                item
                for item in positions
                if item.subleg_id == self._branch_parent_subleg_id
            ),
            selected_position,
        )
        self._branch_parent_subleg_id = (
            parent_position.subleg_id if parent_position is not None else ""
        )
        self._legacy_edit_subleg_id = (
            leg.sublegs[0].subleg_id if leg.sublegs else ""
        )

        self._panel.set_leg_options(
            [
                {"id": item.leg_id, "label": item.label}
                for item in topology.legs
            ],
            self._leg_id,
        )
        self._panel.set_principal_options(
            [
                {
                    "id": item.subleg_id,
                    "label": (
                        f"{'  ' * item.depth}{item.subleg_label} "
                        f"[{item.kind.title()}]"
                    ),
                }
                for item in positions
            ],
            self._principal_subleg_id,
        )
        parent_options = [
            {
                "id": item.subleg_id,
                "label": (
                    f"{'  ' * item.depth}{item.subleg_label} "
                    f"[{item.kind.title()}]"
                ),
            }
            for item in positions
        ]
        self._panel.set_branch_parent_options(
            parent_options,
            self._branch_parent_subleg_id,
        )
        origin_room_ids = [
            str(room_id)
            for room_id in (
                parent_position.subleg.route_room_ids
                if parent_position is not None
                else ()
            )
        ]
        if self._branch_origin_room_id not in origin_room_ids:
            self._branch_origin_room_id = (
                origin_room_ids[0] if origin_room_ids else ""
            )
        self._panel.set_branch_origin_options(
            [
                {
                    "id": room_id,
                    "label": str(
                        getattr(project.rooms.get(room_id), "name", None)
                        or room_id
                    ),
                }
                for room_id in origin_room_ids
            ],
            self._branch_origin_room_id,
        )

        creation_room_ids = topology_creation_room_ids_v1(project)
        allocated_room_ids = set(topology.all_route_room_ids())

        def room_option(room_id: str) -> dict[str, str]:
            return {
                "id": room_id,
                "label": (
                    str(
                        getattr(project.rooms.get(room_id), "name", None)
                        or room_id
                    )
                    + (
                        " — currently allocated; will move"
                        if room_id in allocated_room_ids
                        else " — unallocated"
                    )
                ),
            }

        self._panel.set_available_rooms(
            [room_option(room_id) for room_id in creation_room_ids]
        )
        branch_first_room_ids = [
            room_id
            for room_id in creation_room_ids
            if room_id != self._branch_origin_room_id
        ]
        if self._branch_first_room_id not in branch_first_room_ids:
            self._branch_first_room_id = (
                branch_first_room_ids[0] if branch_first_room_ids else ""
            )
        self._panel.set_branch_first_room_options(
            [room_option(room_id) for room_id in branch_first_room_ids],
            self._branch_first_room_id,
        )
        self._push_staging_rooms(project)
        self._push_topology_schematic(project)

    def _push_staging_rooms(self, project: Any) -> None:
        inventory = build_topology_unassigned_room_inventory_v1(project)
        if not inventory.ready:
            self._panel.set_staging_rooms([])
            return
        self._panel.set_staging_rooms(
            [
                {"id": row.room_id, "label": row.room_label}
                for row in inventory.staging_rooms
            ]
        )

    def _push_topology_schematic(self, project: Any) -> None:
        topology = project.hydronic_topology
        rows: list[dict[str, Any]] = []
        for position in build_recursive_subleg_positions_v1(topology):
            rows.append(
                {
                    "leg_id": position.leg_id,
                    "leg_label": position.leg_label,
                    "subleg_id": position.subleg_id,
                    "subleg_label": position.subleg_label,
                    "kind": position.kind,
                    "parent_subleg_id": position.parent_subleg_id or "",
                    "depth": position.depth,
                    "rooms": [
                        {
                            "id": str(room_id),
                            "label": str(
                                getattr(
                                    project.rooms.get(str(room_id)),
                                    "name",
                                    None,
                                )
                                or room_id
                            ),
                        }
                        for room_id in position.subleg.route_room_ids
                    ],
                }
            )
        heat_source_id = str(topology.heat_source_room_id or "")
        heat_source_label = str(
            getattr(project.rooms.get(heat_source_id), "name", None)
            or "Boiler / Heat Source"
        )
        self._panel.set_topology_schematic(
            rows,
            heat_source_label=heat_source_label,
            focus={
                "leg_id": self._leg_id,
                "subleg_id": self._principal_subleg_id,
                "room_id": self._topology_focus_room_id,
            },
        )

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
            "Topology Arranger — "
            f"{projection.leg_label} / {projection.principal_subleg_label}"
        )

        base_status = (
            f"Heat source: {projection.heat_source_room_id} | "
            f"Type: {projection.selected_subleg_kind.title()} | "
            f"Index: {projection.selected_index_room_id or '—'}"
        )
        route_editing_enabled = (
            projection.principal_subleg_id == self._legacy_edit_subleg_id
        )
        self._panel.set_route_editing_enabled(route_editing_enabled)
        if not route_editing_enabled:
            base_status += (
                " | Room order/index editing for this selected subleg "
                "is deferred"
            )
        self._panel.set_status(
            f"{self._last_transaction_status}\n{base_status}"
            if self._last_transaction_status
            else base_status
        )
        self._panel.set_creation_result(self._last_creation_confirmation)

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

    def _on_leg_selection_requested(self, leg_id: str) -> None:
        self._leg_id = str(leg_id or "")
        self._principal_subleg_id = ""
        self._branch_parent_subleg_id = ""
        self._branch_origin_room_id = ""
        self._branch_first_room_id = ""
        self._last_transaction_status = ""
        self._topology_focus_room_id = ""
        self.refresh()

    def _on_principal_selection_requested(self, subleg_id: str) -> None:
        self._principal_subleg_id = str(subleg_id or "")
        self._branch_parent_subleg_id = self._principal_subleg_id
        self._branch_origin_room_id = ""
        self._branch_first_room_id = ""
        self._last_transaction_status = ""
        self._topology_focus_room_id = ""
        self.refresh()

    def _on_branch_parent_selection_requested(self, subleg_id: str) -> None:
        self._branch_parent_subleg_id = str(subleg_id or "")
        self._branch_origin_room_id = ""
        self._branch_first_room_id = ""
        self._last_transaction_status = ""
        self._topology_focus_room_id = ""
        self.refresh()

    def _on_branch_origin_selection_requested(self, room_id: str) -> None:
        self._branch_origin_room_id = str(room_id or "")
        if self._branch_first_room_id == self._branch_origin_room_id:
            self._branch_first_room_id = ""
        self._last_transaction_status = ""
        self.refresh()

    def _on_branch_first_room_selection_requested(self, room_id: str) -> None:
        self._branch_first_room_id = str(room_id or "")
        self._last_transaction_status = ""
        self.refresh()

    def _on_add_leg_requested(
        self,
        leg_label: str,
        principal_label: str,
        initial_room_id: str,
    ) -> None:
        project = self._context.project_state
        if project is None:
            return
        creation = build_add_leg_with_principal_candidate_v1(
            project,
            initial_room_id=initial_room_id,
            leg_label=leg_label,
            principal_label=principal_label,
        )
        self._commit_creation(
            creation,
            action_label="Create leg with first principal subleg",
        )

    def _on_add_principal_requested(
        self,
        principal_label: str,
        initial_room_id: str,
    ) -> None:
        project = self._context.project_state
        if project is None:
            return
        creation = build_add_principal_subleg_candidate_v1(
            project,
            leg_id=self._leg_id,
            initial_room_id=initial_room_id,
            principal_label=principal_label,
        )
        self._commit_creation(
            creation,
            action_label="Create principal subleg",
        )

    def _on_add_branch_requested(
        self,
        branch_label: str,
        parent_subleg_id: str,
        branch_origin_room_id: str,
        initial_room_id: str,
    ) -> None:
        project = self._context.project_state
        if project is None:
            return
        creation = build_add_branch_subleg_candidate_v1(
            project,
            parent_subleg_id=parent_subleg_id,
            branch_origin_room_id=branch_origin_room_id,
            initial_room_id=initial_room_id,
            branch_label=branch_label,
        )
        self._commit_creation(
            creation,
            action_label="Create recursive branch subleg",
        )

    def _on_room_placement_requested(
        self,
        room_id: str,
        target_subleg_id: str,
        target_order: int,
    ) -> None:
        project = self._context.project_state
        if project is None:
            return
        candidate = build_place_topology_room_candidate_v1(
            project,
            room_id=room_id,
            target_subleg_id=target_subleg_id,
            target_order=target_order,
        )
        self._commit_room_placement(candidate)

    def _on_return_room_to_staging_requested(self, room_id: str) -> None:
        project = self._context.project_state
        if project is None:
            return
        candidate = build_return_topology_room_to_staging_candidate_v1(
            project,
            room_id=room_id,
        )
        self._commit_room_placement(candidate)

    def _commit_room_placement(
        self,
        candidate: TopologyRoomPlacementCandidateV1,
    ) -> None:
        if not candidate.ready or candidate.topology is None:
            self._last_transaction_status = "Blocked — " + "; ".join(
                candidate.blockers
            )
            self._last_creation_confirmation = ""
            self.refresh()
            return
        project = self._context.project_state
        result = commit_validated_topology_candidate_v1(
            project,
            candidate.topology,
            action_label=self._room_placement_action_label(candidate),
            focus_kind=candidate.focus_kind,
            focus_target_id=candidate.focus_target_id,
        )
        if not result.ready:
            self._last_transaction_status = "Blocked — " + "; ".join(
                result.blockers
            )
            self._last_creation_confirmation = ""
            self.refresh()
            return

        if candidate.action == RETURN_TO_STAGING_ACTION:
            self._topology_focus_room_id = ""
        else:
            position = next(
                (
                    item
                    for item in build_recursive_subleg_positions_v1(
                        project.hydronic_topology
                    )
                    if item.subleg_id == candidate.target_subleg_id
                ),
                None,
            )
            if position is not None:
                self._leg_id = position.leg_id
                self._principal_subleg_id = position.subleg_id
                self._topology_focus_room_id = candidate.room_id

        room = project.rooms.get(candidate.room_id)
        room_label = str(getattr(room, "name", None) or candidate.room_id)
        self._last_transaction_status = result.status
        self._last_creation_confirmation = (
            f"Moved: {room_label} → neutral room staging\n"
            if candidate.action == RETURN_TO_STAGING_ACTION
            else (
                f"Moved: {room_label} → {candidate.target_subleg_id} "
                f"at order {candidate.target_order}\n"
            )
        ) + (
            "Full ProjectState step-back saved. Downstream Hydronics "
            "Schematic awaits transactional rebuild."
            if result.changed
            else "Topology was already in that exact position."
        )
        self._notify_changed(candidate.room_id)
        self.refresh()
        if candidate.action != RETURN_TO_STAGING_ACTION:
            self._panel.select_room_id(candidate.room_id)

    @staticmethod
    def _room_placement_action_label(
        candidate: TopologyRoomPlacementCandidateV1,
    ) -> str:
        labels = {
            "place_from_staging": "Place staged room in topology",
            "reorder_within_subleg": "Reorder room within topology subleg",
            "transfer_between_sublegs": "Transfer room between topology sublegs",
            "return_to_staging": "Return room to neutral topology staging",
        }
        return labels.get(candidate.action, "Move room in topology")

    def _commit_creation(
        self,
        creation: TopologyCreationCandidateV1,
        *,
        action_label: str,
    ) -> None:
        if not creation.ready or creation.topology is None:
            self._last_transaction_status = "Blocked — " + "; ".join(
                creation.blockers
            )
            self.refresh()
            return

        project = self._context.project_state
        previous_room_owner = self._room_owner_description(
            project,
            creation.initial_room_id,
        )
        result = commit_validated_topology_candidate_v1(
            project,
            creation.topology,
            action_label=(
                ("Migrate accepted legacy topology and " if creation.migration_applied else "")
                + ("reallocate initial room and " if creation.room_reallocated else "")
                + action_label.lower()
            ).capitalize(),
            focus_kind=creation.focus_kind,
            focus_target_id=creation.focus_target_id,
        )
        if not result.ready:
            self._last_transaction_status = "Blocked — " + "; ".join(
                result.blockers
            )
            self.refresh()
            return

        self._leg_id = creation.leg_id
        self._principal_subleg_id = creation.focus_target_id
        self._branch_parent_subleg_id = (
            creation.parent_subleg_id or creation.focus_target_id
        )
        self._branch_origin_room_id = creation.branch_origin_room_id
        self._branch_first_room_id = creation.initial_room_id
        self._topology_focus_room_id = creation.initial_room_id
        self._last_transaction_status = (
            result.status
            + (
                "; accepted legacy topology migrated"
                if creation.migration_applied
                else ""
            )
            + (
                "; selected initial room moved from its previous route"
                if creation.room_reallocated
                else ""
            )
        )
        self._last_creation_confirmation = self._creation_confirmation(
            project,
            creation,
            previous_room_owner=previous_room_owner,
        )
        self._panel.clear_creation_labels()
        self._notify_changed(creation.initial_room_id)
        self.refresh()
        self._panel.select_room_id(creation.initial_room_id)

    @staticmethod
    def _room_owner_description(project: Any, room_id: str) -> str:
        topology = getattr(project, "hydronic_topology", None)
        if topology is None:
            return ""
        stable_room_id = str(room_id or "")
        for position in build_recursive_subleg_positions_v1(topology):
            if stable_room_id in {
                str(value) for value in position.subleg.route_room_ids
            }:
                return f"{position.leg_label} / {position.subleg_label}"
        return ""

    @staticmethod
    def _creation_confirmation(
        project: Any,
        creation: TopologyCreationCandidateV1,
        *,
        previous_room_owner: str,
    ) -> str:
        topology = project.hydronic_topology
        position = next(
            (
                item
                for item in build_recursive_subleg_positions_v1(topology)
                if item.subleg_id == creation.focus_target_id
            ),
            None,
        )
        leg_label = (
            position.leg_label if position is not None else creation.leg_id
        )
        subleg_label = (
            position.subleg_label
            if position is not None
            else creation.focus_target_id
        )
        room = project.rooms.get(str(creation.initial_room_id))
        room_label = str(
            getattr(room, "name", None) or creation.initial_room_id
        )
        moved = (
            f" — moved from {previous_room_owner}"
            if creation.room_reallocated and previous_room_owner
            else ""
        )
        return (
            f"Created: {leg_label} → {subleg_label}\n"
            f"First room: {room_label}{moved}\n"
            "Full ProjectState step-back saved. Downstream Hydronics "
            "Schematic awaits transactional rebuild."
        )

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
