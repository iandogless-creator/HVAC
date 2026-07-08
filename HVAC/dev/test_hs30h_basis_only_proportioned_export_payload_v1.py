from __future__ import annotations

import json

from HVAC.hydronics.proportioning.basis_only_proportioned_export_payload_v1 import (
    basis_only_proportioned_export_payload_to_dict_v1,
    build_basis_only_proportioned_export_payload_preview_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


def main() -> None:
    snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="F+RR",
        return_arrangement_status="Basis: F+RR / Reverse return",
        index_room_id="room-006",
        index_room_label="Bedroom 3",
        terminal_room_id="room-006",
        terminal_room_label="Bedroom 3",
        terminal_alignment_status="Terminal aligned",
        basis_mode="Manual accepted",
        total_index_length_label="38.0 m",
        nominal_gradient_label="125 Pa/m",
    )

    payload = build_basis_only_proportioned_export_payload_preview_v1(
        snapshot=snapshot,
        resolved_return_arrangement_basis_rows=[
            {
                "scope": "System",
                "target": "Whole system",
                "effective_basis": "F+RR",
                "source": "Accepted system basis",
                "status": "Resolved",
            },
        ],
        chosen_basis_route_pressure_rows=[
            {
                "route": "leg-001:primary-subleg",
                "basis": "F+RR",
                "chosen_dp": "7420.0 Pa",
                "status": "Preview only",
            },
        ],
        chosen_basis_controlling_shortfall_rows=[
            {
                "route": "leg-001:primary-subleg",
                "chosen_dp": "7420.0 Pa",
                "controlling": "Yes",
                "required_added_dp": "0.0 Pa",
            },
        ],
        provisional_proportioning_burden_rows=[
            {
                "rank": "1",
                "route": "leg-001:primary-subleg",
                "flow_kg_s": "0.0227",
                "required_added_dp": "0.0 Pa",
                "resistance_pa_per_kg_s2": "0.0",
                "status": "Preview only — no valve selected",
            },
        ],
    )

    assert payload.ready is True
    assert payload.blockers == ()
    assert "basis-only" in payload.status

    assert payload.committed_basis_snapshot is not None
    assert payload.committed_basis_snapshot["basis_only_output_ready"] is True
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
    assert "final hydraulics not included" in payload_dict["note"]

    # Prove it is already JSON-safe for later export/report writers.
    json.dumps(payload_dict)

    blocked = build_basis_only_proportioned_export_payload_preview_v1(
        snapshot=None,
    )

    assert blocked.ready is False
    assert "Committed basis-only Proportioned snapshot required" in blocked.blockers

    not_ready_snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis="F+RR",
        basis_only_output_ready=False,
        basis_only_output_status="Not ready for basis-only export",
    )

    blocked_not_ready = build_basis_only_proportioned_export_payload_preview_v1(
        snapshot=not_ready_snapshot,
    )

    assert blocked_not_ready.ready is False
    assert (
        "Committed snapshot is not ready for basis-only output export"
        in blocked_not_ready.blockers
    )

    print("OK — H-S30-H basis-only Proportioned export payload passed.")


if __name__ == "__main__":
    main()
