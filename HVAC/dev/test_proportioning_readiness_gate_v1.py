from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)
from HVAC.hydronics.proportioning.proportioning_readiness_gate_v1 import (
    evaluate_proportioning_readiness_v1,
)


def main() -> None:
    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=[
            {
                "section_id": "section-001",
                "flow_kg_s": "0.0227",
                "pipe": "15 mm",
                "dp_per_m": "120 Pa/m",
                "section_dp": "138.0 Pa",
            }
        ],
        route_rows=[
            {
                "route_id": "route-001",
                "route": "Leg 1A Common subleg",
                "route_dp_sum": "7654.1 Pa",
                "complete": "Yes",
                "controlling": "Yes",
            }
        ],
        shortfall_rows=[
            {
                "route_id": "route-001",
                "shortfall_dp": "0.0 Pa",
            }
        ],
        return_comparison_rows=[
            {
                "route": "Leg 1A Common subleg",
                "room": "room-l1a-004",
                "emitter": "emitter-l1a-004",
                "direct_total_dp": "14680.6 Pa",
                "reverse_total_dp": "7835.4 Pa",
                "rr_suitability": "RR comparable — ordered subleg",
            }
        ],
    )

    gate = evaluate_proportioning_readiness_v1(snapshot)

    print("STATUS:", gate.status)
    print("READY:", gate.ready)
    print("BLOCKERS:", gate.blockers)

    for check in gate.checks:
        print(
            f"{'PASS' if check.passed else 'FAIL'} | "
            f"{check.code} | {check.label} | {check.detail}"
        )

    assert gate.ready is True
    assert gate.status == "Ready for preliminary proportioning"
    assert not gate.blockers


if __name__ == "__main__":
    main()