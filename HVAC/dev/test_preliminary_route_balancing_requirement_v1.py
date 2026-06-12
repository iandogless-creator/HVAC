from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)
from HVAC.hydronics.proportioning.preliminary_route_balancing_requirement_v1 import (
    build_preliminary_route_balancing_preview_v1,
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

    preview = build_preliminary_route_balancing_preview_v1(snapshot)

    print("STATUS:", preview.status)
    print("READY:", preview.ready)
    print("CONTROLLING:", preview.controlling_route_label)
    print("CONTROLLING Δp:", preview.controlling_route_dp)
    print("BLOCKERS:", preview.blockers)

    for row in preview.rows:
        print(
            row.route_label,
            "| route Δp:", row.route_dp,
            "| shortfall:", row.shortfall_dp,
            "| added:", row.required_added_resistance_dp,
            "|", row.status,
        )

    assert preview.ready is True
    assert preview.status == "Preliminary route balancing preview ready"
    assert len(preview.rows) == 2
    assert preview.rows[0].required_added_resistance_dp == "0.0 Pa"
    assert preview.rows[1].required_added_resistance_dp == "2554.1 Pa"


if __name__ == "__main__":
    main()