from __future__ import annotations

from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)


def test_return_comparison_snapshot_carries_rr_added_evidence() -> None:
    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=[],
        route_rows=[],
        shortfall_rows=[],
        return_comparison_rows=[
            {
                "route": "Heating Leg 1 / Leg 1A Common subleg",
                "room": "Bedroom 1",
                "emitter": "RAD-001",
                "direct_rank": "1",
                "direct_total_dp": "1000.0 Pa",
                "direct_controlling": "Yes",
                "reverse_rank": "1",
                "reverse_total_dp": "1200.0 Pa",
                "reverse_controlling": "Yes",
                "rr_added_length": "2.50 m",
                "rr_added_dp": "55.0 Pa",
                "rr_suitability": "RR comparable — ordered subleg",
                "status": "Flow + direct + reverse return paths ready",
            }
        ],
    )

    assert len(snapshot.return_comparisons) == 1

    row = snapshot.return_comparisons[0]

    assert row.rr_added_length == "2.50 m"
    assert row.rr_added_dp == "55.0 Pa"
    assert row.reverse_total_dp == "1200.0 Pa"


if __name__ == "__main__":
    test_return_comparison_snapshot_carries_rr_added_evidence()
    print("OK — H-S29-J RR added evidence visible in return comparison rows.")
