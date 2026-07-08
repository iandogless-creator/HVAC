from __future__ import annotations

from types import SimpleNamespace

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.hydronics.proportioning.basis_only_proportioned_export_payload_v1 import (
    basis_only_proportioned_export_payload_to_dict_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )

    project = ProjectState(
        project_id="hs30i-adapter-payload",
        name="H-S30-I adapter payload preview",
    )
    project.hydronic_proportioned_basis_snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="F+RR",
        return_arrangement_status="Basis: F+RR / Reverse return",
        index_room_id="room-006",
        index_room_label="Bedroom 3",
    )

    adapter._project_state = project

    resolution = SimpleNamespace(
        rows=[
            SimpleNamespace(
                scope="System",
                target="Whole system",
                effective_basis="F+RR",
                source="Accepted system basis",
                status="Resolved",
            )
        ]
    )

    payload = adapter._build_basis_only_proportioned_export_payload_preview_v1(
        resolution=resolution,
        chosen_preview_rows=[
            SimpleNamespace(
                route="leg-001:primary-subleg",
                basis="F+RR",
                chosen_dp="7420.0 Pa",
                status="Preview only",
            )
        ],
        chosen_controlling_rows=[
            SimpleNamespace(
                route="leg-001:primary-subleg",
                chosen_dp="7420.0 Pa",
                controlling="Yes",
                required_added_dp="0.0 Pa",
            )
        ],
        provisional_burden_rows=[
            {
                "rank": "1",
                "route": "leg-001:primary-subleg",
                "flow_kg_s": "0.0227",
                "required_added_dp": "0.0 Pa",
                "resistance_pa_per_kg_s2": "0.0",
                "status": "Preview only — no valve selected",
            }
        ],
    )

    assert payload.ready is True
    assert payload.blockers == ()
    assert payload.committed_basis_snapshot is not None
    assert payload.committed_basis_snapshot["return_arrangement_basis"] == "F+RR"

    assert len(payload.resolved_return_arrangement_basis) == 1
    assert len(payload.chosen_basis_route_pressure_evidence) == 1
    assert len(payload.chosen_basis_controlling_shortfall_evidence) == 1
    assert len(payload.provisional_proportioning_burden) == 1

    assert "No pump selection" in payload.exclusions
    assert "No valve selection" in payload.exclusions
    assert "No final balancing" in payload.exclusions
    assert "No pipe resizing" in payload.exclusions
    assert "No final hydraulic result" in payload.exclusions

    payload_dict = basis_only_proportioned_export_payload_to_dict_v1(payload)

    assert payload_dict is not None
    assert payload_dict["ready"] is True
    assert payload_dict["schema"] == "basis_only_proportioned_export_payload_v1"

    blocked_adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    blocked_adapter._project_state = ProjectState(
        project_id="hs30i-blocked",
        name="H-S30-I blocked",
    )

    blocked = (
        blocked_adapter
        ._build_basis_only_proportioned_export_payload_preview_v1()
    )

    assert blocked.ready is False
    assert "Committed basis-only Proportioned snapshot required" in (
        blocked.blockers
    )

    print("OK — H-S30-I adapter export payload preview wiring passed.")


if __name__ == "__main__":
    main()
