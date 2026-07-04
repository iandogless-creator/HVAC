from __future__ import annotations

from types import SimpleNamespace

from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    _RRSectionPressureBasisV1,
    _reverse_return_total_with_rr_added_dp_v1,
    _rr_added_length_m,
    _rr_added_length_pressure_drop_Pa,
)


def test_rr_added_length_defaults_to_zero() -> None:
    assert _rr_added_length_m(SimpleNamespace()) == 0.0


def test_rr_added_length_reads_project_state_attribute() -> None:
    project_state = SimpleNamespace(hydronic_rr_added_length_m=2.5)

    assert _rr_added_length_m(project_state) == 2.5


def test_rr_added_length_pressure_drop_is_calculated_from_length() -> None:
    project_state = SimpleNamespace()

    basis_by_id = {
        "section-001": _RRSectionPressureBasisV1(
            mass_flow_kg_s=0.02,
            pipe_size_label="10 mm",
        )
    }

    dp = _rr_added_length_pressure_drop_Pa(
        project_state=project_state,
        section_pressure_basis_by_id=basis_by_id,
        candidate_section_ids=("section-001",),
        length_m=2.0,
    )

    assert dp > 0.0

    zero_dp = _rr_added_length_pressure_drop_Pa(
        project_state=project_state,
        section_pressure_basis_by_id=basis_by_id,
        candidate_section_ids=("section-001",),
        length_m=0.0,
    )

    assert zero_dp == 0.0


def test_reverse_total_includes_rr_added_pressure_only_on_reverse_side() -> None:
    total = _reverse_return_total_with_rr_added_dp_v1(
        flow_dp_Pa=100.0,
        reverse_return_dp_Pa=200.0,
        rr_added_pressure_drop_Pa=30.0,
    )

    assert total == 330.0

    missing = _reverse_return_total_with_rr_added_dp_v1(
        flow_dp_Pa=100.0,
        reverse_return_dp_Pa=None,
        rr_added_pressure_drop_Pa=30.0,
    )

    assert missing is None


if __name__ == "__main__":
    test_rr_added_length_defaults_to_zero()
    test_rr_added_length_reads_project_state_attribute()
    test_rr_added_length_pressure_drop_is_calculated_from_length()
    test_reverse_total_includes_rr_added_pressure_only_on_reverse_side()
    print("OK — H-S29-I RR added length applies to reverse comparison.")
