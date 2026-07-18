from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    _resolve_route_rr_added_length_basis_v1,
    _return_comparison_status_v1,
    _rr_added_length_for_row_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    ReturnArrangementIntentV1,
)


def main() -> None:
    intent = ReturnArrangementIntentV1()
    intent.rr_added_length_basis_mode = "manual_allowance"
    intent.rr_added_length_m = 10.0
    intent.leg_rr_added_length_basis_modes["leg-001"] = "manual_allowance"
    intent.leg_rr_added_lengths_m["leg-001"] = 8.0
    intent.subleg_rr_added_length_basis_modes[
        "leg-001-primary-subleg"
    ] = "manual_allowance"
    intent.subleg_rr_added_lengths_m["leg-001-primary-subleg"] = 4.0

    project = SimpleNamespace(hydronic_return_arrangement_intent=intent)

    common = _resolve_route_rr_added_length_basis_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-primary-subleg",
    )
    branch_inherited = _resolve_route_rr_added_length_basis_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-subleg-b",
        parent_subleg_id="leg-001-primary-subleg",
    )

    assert common.effective_added_length_m == 4.0
    assert branch_inherited.effective_added_length_m == 4.0
    assert branch_inherited.source == "inherit parent subleg"
    assert branch_inherited.inherited_from == "leg-001-primary-subleg"

    # Most-specific wins: 1.5 m is applied, never 10 + 8 + 4 + 1.5 m.
    intent.subleg_rr_added_length_basis_modes[
        "leg-001-subleg-b"
    ] = "manual_allowance"
    intent.subleg_rr_added_lengths_m["leg-001-subleg-b"] = 1.5

    branch_local = _resolve_route_rr_added_length_basis_v1(
        project,
        leg_id="leg-001",
        subleg_id="leg-001-subleg-b",
        parent_subleg_id="leg-001-primary-subleg",
    )
    applied = _rr_added_length_for_row_v1(
        project_state=project,
        basis_mode=branch_local.effective_basis_mode,
        section_length_by_id={},
        reverse_return_section_ids=("section-001",),
        manual_added_length_m=branch_local.effective_added_length_m,
    )

    assert branch_local.effective_added_length_m == 1.5
    assert branch_local.source == "subleg override"
    assert applied == 1.5
    assert applied != 23.5

    # Downstream proxy remains a route-derived value and does not absorb any
    # configured manual values from parent scopes.
    proxy = _rr_added_length_for_row_v1(
        project_state=project,
        basis_mode="downstream_proxy",
        section_length_by_id={
            "section-001": 2.0,
            "section-002": 3.5,
            "section-003": 4.0,
        },
        reverse_return_section_ids=(
            "section-001",
            "section-002",
            "section-003",
        ),
        manual_added_length_m=99.0,
    )
    assert proxy == 7.5

    status = _return_comparison_status_v1(
        flow_section_ids=("section-001",),
        reverse_return_section_ids=("section-001", "section-002"),
        rr_added_length_basis_mode=branch_local.effective_basis_mode,
        rr_added_length_m=applied,
        rr_added_pressure_drop_Pa=125.0,
        rr_added_length_source=branch_local.source,
        rr_added_length_inherited_from=branch_local.inherited_from,
    )
    assert "subleg override" in status
    assert "one effective allowance only" in status
    assert "no scope summing" in status

    circuit_source = Path(
        "HVAC/hydronics/proportioning/circuit_return_path_comparison_v1.py"
    ).read_text()
    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()

    assert "rr_length_resolution.effective_added_length_m" in circuit_source
    assert "find_primary_subleg_for_leg" in circuit_source
    assert '"rr_added_length_basis_mode"' in adapter_source
    assert '"rr_added_length_source"' in adapter_source

    print(
        "OK — H-S38-A3 route-specific RR length consumption and "
        "no-double-counting evidence passed."
    )


if __name__ == "__main__":
    main()
