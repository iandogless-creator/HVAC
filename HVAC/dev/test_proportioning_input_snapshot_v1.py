from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)


def main() -> None:
    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=[
            {
                "section_id": "section-001",
                "order": "1",
                "from": "Boiler",
                "to": "Leg 1",
                "flow_kg_s": "0.0227",
                "pipe": "15 mm",
                "dp_per_m": "120 Pa/m",
                "k_total": "2.50",
                "local_dp": "18.0 Pa",
                "straight_dp": "120.0 Pa",
                "section_dp": "138.0 Pa",
                "status": "Preview ready",
            }
        ],
        route_rows=[
            {
                "route_id": "leg-001:leg-001-primary-subleg",
                "route": "Leg 1A Common subleg",
                "sections": "5",
                "route_dp": "7654.1 Pa",
                "complete": "Yes",
                "controlling": "Yes",
                "status": "Route Δp preview ready",
            }
        ],
        shortfall_rows=[
            {
                "route_id": "leg-001:leg-001-primary-subleg",
                "shortfall_pa": "0.0 Pa",
            }
        ],
        return_comparison_rows=[
            {
                "route": "Leg 1A Common subleg",
                "room": "room-l1a-004",
                "emitter": "emitter-l1a-004",
                "room_id": "room-l1a-004",
                "emitter_id": "emitter-l1a-004",
                "direct_rank": "5",
                "direct_total_dp": "14680.6 Pa",
                "direct_controlling": "No",
                "reverse_rank": "11",
                "reverse_total_dp": "7835.4 Pa",
                "reverse_controlling": "No",
                "rr_suitability": "RR comparable — ordered subleg",
                "status": "Flow + direct + reverse return paths ready",
            }
        ],
    )

    print("STATUS:", snapshot.status)
    print("WARNINGS:", snapshot.warnings)
    print("SECTIONS:", len(snapshot.sections))
    print("ROUTES:", len(snapshot.routes))
    print("RETURN COMPARISONS:", len(snapshot.return_comparisons))

    assert snapshot.status == "Snapshot ready"
    assert len(snapshot.sections) == 1
    assert len(snapshot.routes) == 1
    assert len(snapshot.return_comparisons) == 1


if __name__ == "__main__":
    main()