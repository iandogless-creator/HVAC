# ======================================================================
# H-S54-B2 — committed snapshot dirty/signal persistence notification
# ======================================================================

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.gui_v3.adapters import hydronics_schematic_panel_adapter as module
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)


class _Signal:
    def __init__(self):
        self.calls = 0

    def emit(self, *args):
        self.calls += 1


class _Project:
    def __init__(self):
        self.hydronic_proportioned_basis_snapshot = None
        self.hydronics_valid = True
        self.dirty_calls = 0

    def mark_dirty(self):
        self.dirty_calls += 1


def main() -> None:
    snapshot = SimpleNamespace(return_arrangement_basis="F&R")
    project = _Project()
    state_changed = _Signal()
    changed = _Signal()
    refreshes = []
    stub = SimpleNamespace(
        _project_state=project,
        _panel=SimpleNamespace(),
        _context=SimpleNamespace(
            project_state_changed=state_changed,
            project_changed=changed,
        ),
        _balancing_point_accepted_kvs_consequence_disposition_resolution=(
            object()
        ),
        _committed_hydraulic_route_pressure_projection_v1=object(),
        _committed_hydraulic_chosen_controlling_rows_v1=(object(),),
        _committed_hydraulic_resistance_basis_v1=object(),
        _committed_balancing_point_allocation_projection_v1=object(),
        refresh=lambda: refreshes.append(True),
    )

    replacements = {
        "build_proportioning_readiness_v1": lambda project: SimpleNamespace(
            return_arrangement_basis_ready=True,
            proportioning_status="Ready",
        ),
        "build_point_proportioning_commit_readiness_v1": (
            lambda resolution: SimpleNamespace(
                ready=True,
                status="Ready",
            )
        ),
        "build_committed_proportioning_hydraulic_input_authority_v1": (
            lambda **kwargs: SimpleNamespace(
                ready=True,
                status="Ready",
            )
        ),
        "build_committed_balancing_point_allocation_authority_v1": (
            lambda projection: SimpleNamespace(
                ready=True,
                status="Ready",
            )
        ),
        "build_proportioned_basis_snapshot_v1": (
            lambda project, **kwargs: SimpleNamespace(
                ready=True,
                snapshot=snapshot,
                status="Ready",
            )
        ),
    }
    originals = {
        name: getattr(module, name)
        for name in replacements
    }
    try:
        for name, value in replacements.items():
            setattr(module, name, value)
        HydronicsSchematicPanelAdapter.commit_proportioning_basis_snapshot(
            stub
        )
    finally:
        for name, value in originals.items():
            setattr(module, name, value)

    assert project.hydronic_proportioned_basis_snapshot is snapshot
    assert project.hydronics_valid is False
    assert project.dirty_calls == 1
    assert state_changed.calls == 1
    assert changed.calls == 1
    assert refreshes == [True]

    print(
        "OK — H-S54-B2 committed snapshot dirty/signal persistence "
        "notification passed."
    )


if __name__ == "__main__":
    main()
