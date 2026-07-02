from __future__ import annotations

from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)


def test_section_snapshot_carries_friction_metadata() -> None:
    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=[
            {
                "section_id": "section-001",
                "order": "1",
                "from": "A",
                "to": "B",
                "flow_kg_s": "0.0200 kg/s",
                "pipe": "10 mm",
                "velocity_m_s": "0.254 m/s",
                "dp_per_m": "123.4 Pa/m",
                "reynolds_number": "5084",
                "friction_factor": "0.0371",
                "friction_method": "Colebrook",
                "colebrook_iterations": "3",
                "colebrook_converged": "Yes",
                "length_m": "1.00 m",
                "k_total": "0.00",
                "local_dp": "0.0 Pa",
                "straight_dp": "123.4 Pa",
                "section_dp": "123.4 Pa",
                "status": "Basic PS + Local K preview only",
            }
        ],
        route_rows=[],
        shortfall_rows=[],
        return_comparison_rows=[],
    )

    assert len(snapshot.sections) == 1

    row = snapshot.sections[0]

    assert row.reynolds_number == "5084"
    assert row.friction_factor == "0.0371"
    assert row.friction_method == "Colebrook"
    assert row.colebrook_iterations == "3"
    assert row.colebrook_converged == "Yes"


if __name__ == "__main__":
    test_section_snapshot_carries_friction_metadata()
    print("OK — H-S29-F section friction metadata preview rows passed.")