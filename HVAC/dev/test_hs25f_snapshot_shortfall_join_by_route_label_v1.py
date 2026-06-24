# ======================================================================
# HVAC/dev/test_hs25f_snapshot_shortfall_join_by_route_label_v1.py
# H-S25-F — Snapshot joins route shortfall rows by route_id or label
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    build_proportioning_input_snapshot_v1,
)
from HVAC.hydronics.proportioning.proportioning_readiness_gate_v1 import (
    evaluate_proportioning_readiness_v1,
)


def _section_row(index: int) -> dict:
    return {
        "section_id": f"section-{index}",
        "order": str(index),
        "from": f"from-{index}",
        "to": f"to-{index}",
        "route_id": "leg-001:leg-001-subleg-b",
        "route": "Heating Leg 1 / Leg 1B Branch subleg",
        "flow_kg_s": "0.1000 kg/s",
        "pipe": "22 mm",
        "dp_per_m": "100.0",
        "section_dp": "500.0 Pa",
    }


def main() -> None:
    snapshot = build_proportioning_input_snapshot_v1(
        section_rows=[_section_row(1)],
        route_rows=[
            {
                "route_id": "leg-001:leg-001-subleg-b",
                "route": "Heating Leg 1 / Leg 1B Branch subleg",
                "sections": "1",
                "route_dp": "1000.0 Pa",
                "complete": "Yes",
                "controlling": "Yes",
            }
        ],
        shortfall_rows=[
            {
                # Deliberately no route_id here.
                # This mirrors the GUI shortfall table using the route label.
                "route": "Heating Leg 1 / Leg 1B Branch subleg",
                "shortfall_dp": "0.0 Pa",
            }
        ],
        return_comparison_rows=[
            {
                "route": "Heating Leg 1 / Leg 1B Branch subleg",
                "room": "room-001",
                "emitter": "emitter-001",
                "direct_total_dp": "1000.0 Pa",
                "reverse_total_dp": "900.0 Pa",
                "rr_suitability": "RR comparable",
            }
        ],
    )

    route = snapshot.routes[0]
    gate = evaluate_proportioning_readiness_v1(snapshot)

    print()
    print("H-S25-F — Snapshot route shortfall joins by label")
    print("================================================")
    print("route_id:", route.route_id)
    print("route_label:", route.route_label)
    print("shortfall_pa:", route.shortfall_pa)
    print("gate ready:", gate.ready)
    print("blockers:", gate.blockers)

    assert route.shortfall_pa == "0.0 Pa"
    assert gate.ready is True
    assert gate.blockers == []

    print()
    print("OK — snapshot shortfall basis joins by route label.")


if __name__ == "__main__":
    main()
