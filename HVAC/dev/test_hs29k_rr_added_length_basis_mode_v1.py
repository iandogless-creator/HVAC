from __future__ import annotations

from types import SimpleNamespace

from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    _downstream_proxy_rr_added_length_m_v1,
    _return_comparison_status_v1,
    _rr_added_length_basis_mode,
    _rr_added_length_for_row_v1,
)


def test_rr_added_length_basis_defaults_to_physical_loop_zero_extra() -> None:
    assert (
        _rr_added_length_basis_mode(SimpleNamespace())
        == "physical_loop_zero_extra"
    )


def test_rr_added_length_basis_accepts_downstream_proxy_alias() -> None:
    project_state = SimpleNamespace(
        hydronic_rr_added_length_basis_mode="downstream proxy"
    )

    assert _rr_added_length_basis_mode(project_state) == "downstream_proxy"


def test_downstream_proxy_excludes_current_section_and_sums_after_room() -> None:
    added_length = _downstream_proxy_rr_added_length_m_v1(
        reverse_return_section_ids=("section-001", "section-002", "section-003"),
        section_length_by_id={
            "section-001": 1.0,
            "section-002": 2.5,
            "section-003": 3.0,
        },
    )

    assert added_length == 5.5


def test_physical_loop_mode_adds_zero_extra_length() -> None:
    added_length = _rr_added_length_for_row_v1(
        project_state=SimpleNamespace(hydronic_rr_added_length_m=99.0),
        basis_mode="physical_loop_zero_extra",
        section_length_by_id={
            "section-001": 1.0,
            "section-002": 2.0,
        },
        reverse_return_section_ids=("section-001", "section-002"),
    )

    assert added_length == 0.0


def test_manual_mode_keeps_existing_hidden_allowance_hook() -> None:
    added_length = _rr_added_length_for_row_v1(
        project_state=SimpleNamespace(hydronic_rr_added_length_m=4.25),
        basis_mode="manual_allowance",
        section_length_by_id={},
        reverse_return_section_ids=("section-001",),
    )

    assert added_length == 4.25


def test_status_exposes_rr_length_basis() -> None:
    status = _return_comparison_status_v1(
        flow_section_ids=("section-001",),
        reverse_return_section_ids=("section-001", "section-002"),
        rr_added_length_basis_mode="physical_loop_zero_extra",
        rr_added_length_m=0.0,
        rr_added_pressure_drop_Pa=0.0,
    )

    assert "RR length basis" in status
    assert "Physical loop" in status


if __name__ == "__main__":
    test_rr_added_length_basis_defaults_to_physical_loop_zero_extra()
    test_rr_added_length_basis_accepts_downstream_proxy_alias()
    test_downstream_proxy_excludes_current_section_and_sums_after_room()
    test_physical_loop_mode_adds_zero_extra_length()
    test_manual_mode_keeps_existing_hidden_allowance_hook()
    test_status_exposes_rr_length_basis()
    print("OK — H-S29-K RR added-length basis mode passed.")
