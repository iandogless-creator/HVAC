from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    build_preliminary_balancing_resistance_basis_v1,
)
from HVAC.hydronics.proportioning.preliminary_route_balancing_requirement_v1 import (
    build_preliminary_route_balancing_preview_v1,
)
from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)


def main() -> None:
    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=[
            {
                "section_id": "section-route-001",
                "route_id": "route-001",
                "flow_kg_s": "0.05000",
                "pipe": "15 mm",
                "dp_per_m": "120 Pa/m",
                "section_dp": "138.0 Pa",
            },
            {
                "section_id": "section-route-002",
                "route_id": "route-002",
                "flow_kg_s": "0.02500",
                "pipe": "15 mm",
                "dp_per_m": "120 Pa/m",
                "section_dp": "138.0 Pa",
            },
        ],
        route_rows=[
            {
                "route_id": "route-001",
                "route": "Leg 1A Common subleg",
                "sections": "5",
                "route_dp": "7654.1 Pa",
                "complete": "Yes",
                "controlling": "Yes",
            },
            {
                "route_id": "route-002",
                "route": "Leg 1B Branch subleg",
                "sections": "4",
                "route_dp": "5100.0 Pa",
                "complete": "Yes",
                "controlling": "No",
            },
        ],
        shortfall_rows=[
            {
                "route_id": "route-001",
                "shortfall_dp": "0.0 Pa",
            },
            {
                "route_id": "route-002",
                "shortfall_dp": "2554.1 Pa",
            },
        ],
        return_comparison_rows=[
            {
                "route": "Leg 1A Common subleg",
                "room": "room-l1a-001",
                "emitter": "emitter-l1a-001",
                "direct_total_dp": "7698.2 Pa",
                "reverse_total_dp": "11383.6 Pa",
                "rr_suitability": "RR comparable — ordered subleg",
            }
        ],
    )

    balancing_preview = build_preliminary_route_balancing_preview_v1(snapshot)

    basis = build_preliminary_balancing_resistance_basis_v1(
        snapshot=snapshot,
        balancing_preview=balancing_preview,
    )

    print("STATUS:", basis.status)
    print("READY:", basis.ready)
    print("BLOCKERS:", basis.blockers)

    for row in basis.rows:
        print(
            row.route_label,
            "| flow:", row.flow_kg_s,
            "| added Δp:", row.required_added_dp,
            "| R:", row.resistance_pa_per_kg_s2,
            "|", row.status,
        )

    assert basis.ready is True
    assert basis.status == "Preliminary balancing resistance basis ready"
    assert len(basis.rows) == 2

    # route-002: R = 2554.1 / 0.025² = 4,086,560 Pa/(kg/s)²
    assert basis.rows[1].resistance_pa_per_kg_s2 == "4086560.0 Pa/(kg/s)²"


if __name__ == "__main__":
    main()