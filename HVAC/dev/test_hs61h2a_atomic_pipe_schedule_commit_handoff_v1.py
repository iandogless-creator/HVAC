# ======================================================================
# H-S61-H2A — Atomic adapter pipe-schedule commit persistence handoff
# ======================================================================

from __future__ import annotations

from dataclasses import replace
import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.dev.test_hs61h1b_transactional_pipe_schedule_rebuild_v1 import (
    _fixtures,
)
from HVAC.gui_v3.adapters import hydronics_schematic_panel_adapter as module
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    proportioned_basis_snapshot_to_dict_v1,
)
from HVAC.project.project_state import ProjectState


class _Signal:
    def __init__(self) -> None:
        self.calls = 0

    def emit(self, *_args) -> None:
        self.calls += 1


class _Project:
    def __init__(
            self,
            *,
            snapshot,
            material,
            acceptance_intent,
            valve_intent,
    ) -> None:
        self.hydronic_proportioned_basis_snapshot = snapshot
        self.hydronic_proportioned_pipe_material_family_intent = material
        self.hydronic_proportioned_pipe_resizing_schedule_acceptance_intent = (
            acceptance_intent
        )
        self.hydronic_point_kvs_candidate_acceptance_intent = valve_intent
        self.hydronics_valid = True
        self.dirty_calls = 0

    def mark_dirty(self) -> None:
        self.dirty_calls += 1


def _adapter(project, projection, reconciliation):
    state_changed = _Signal()
    changed = _Signal()
    refreshes: list[bool] = []
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project
    adapter._context = SimpleNamespace(
        project_state_changed=state_changed,
        project_changed=changed,
    )
    adapter._proportioned_pipe_resizing_hydraulic_projection_v1 = projection
    adapter._resized_balancing_point_reconciliation_v1 = reconciliation
    adapter.refresh = lambda: refreshes.append(True)
    return adapter, state_changed, changed, refreshes


def main() -> None:
    snapshot, material, resolved, projection, reconciliation = _fixtures()
    stored_acceptance = object()
    valve_intent = object()
    project = _Project(
        snapshot=snapshot,
        material=material,
        acceptance_intent=stored_acceptance,
        valve_intent=valve_intent,
    )
    adapter, state_changed, changed, refreshes = _adapter(
        project,
        projection,
        reconciliation,
    )
    original_snapshot_payload = proportioned_basis_snapshot_to_dict_v1(
        snapshot
    )
    original_material_payload = material.to_dict()

    with patch.object(
            module,
            "resolve_proportioned_pipe_resizing_schedule_acceptance_v1",
            return_value=resolved,
    ):
        committed = adapter.commit_proportioned_pipe_schedule_v1()

    assert committed is True
    replacement = project.hydronic_proportioned_basis_snapshot
    assert replacement is not snapshot
    assert replacement.status == "COMMITTED_RESIZED_HYDRAULICS"
    assert replacement.committed_point_valve_bases == ()
    committed_material = (
        project.hydronic_proportioned_pipe_material_family_intent
    )
    assert committed_material.current_material_key == "mlcp"
    assert committed_material.proposed_material_key == "mlcp"
    assert (
        project.hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
        is None
    )
    assert project.hydronic_point_kvs_candidate_acceptance_intent is valve_intent
    assert project.hydronics_valid is False
    assert project.dirty_calls == 1
    assert state_changed.calls == 1
    assert changed.calls == 1
    assert refreshes == [True]
    assert proportioned_basis_snapshot_to_dict_v1(snapshot) == (
        original_snapshot_payload
    )
    assert material.to_dict() == original_material_payload

    # The exact replacement state persists through the existing ProjectState
    # schema without carrying the consumed schedule acceptance.
    persisted = ProjectState(project_id="hs61h2a", name="H-S61-H2A")
    persisted.hydronic_proportioned_basis_snapshot = replacement
    persisted.hydronic_proportioned_pipe_material_family_intent = (
        committed_material
    )
    persisted.hydronic_proportioned_pipe_resizing_schedule_acceptance_intent = (
        None
    )
    restored = ProjectState.from_dict(persisted.to_dict())
    assert restored.hydronic_proportioned_basis_snapshot is not None
    assert (
        restored.hydronic_proportioned_basis_snapshot.status
        == "COMMITTED_RESIZED_HYDRAULICS"
    )
    assert (
        restored.hydronic_proportioned_pipe_material_family_intent
        .current_material_key
        == "mlcp"
    )
    assert (
        restored.hydronic_proportioned_pipe_material_family_intent
        .proposed_material_key
        == "mlcp"
    )
    assert (
        restored
        .hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
        is None
    )

    # A stale resolution must leave every ProjectState field untouched.
    stale_project = _Project(
        snapshot=snapshot,
        material=material,
        acceptance_intent=stored_acceptance,
        valve_intent=valve_intent,
    )
    stale_adapter, stale_state, stale_changed, stale_refreshes = _adapter(
        stale_project,
        projection,
        reconciliation,
    )
    stale_resolution = replace(
        resolved,
        ready=False,
        accepted=False,
        blockers=("Accepted schedule fingerprint is stale",),
        status="Blocked — accepted schedule fingerprint is stale",
    )
    with patch.object(
            module,
            "resolve_proportioned_pipe_resizing_schedule_acceptance_v1",
            return_value=stale_resolution,
    ):
        blocked = stale_adapter.commit_proportioned_pipe_schedule_v1()

    assert blocked is False
    assert stale_project.hydronic_proportioned_basis_snapshot is snapshot
    assert (
        stale_project.hydronic_proportioned_pipe_material_family_intent
        is material
    )
    assert (
        stale_project
        .hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
        is stored_acceptance
    )
    assert stale_project.hydronic_point_kvs_candidate_acceptance_intent is (
        valve_intent
    )
    assert stale_project.hydronics_valid is True
    assert stale_project.dirty_calls == 0
    assert stale_state.calls == 0
    assert stale_changed.calls == 0
    assert stale_refreshes == []

    print(
        "OK — H-S61-H2A atomic accepted pipe-schedule ProjectState "
        "handoff passed."
    )


if __name__ == "__main__":
    main()
