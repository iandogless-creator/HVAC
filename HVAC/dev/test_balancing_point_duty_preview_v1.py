# ======================================================================
# HVAC/dev/test_balancing_point_duty_preview_v1.py
# H-S24-A — Balancing point duty preview projection test
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.balancing_point_duty_preview_v1 import (
    build_balancing_point_duty_preview_v1,
)
from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    PreliminaryBalancingResistanceRowV1,
)
from HVAC.hydronics.proportioning.preliminary_route_balancing_requirement_v1 import (
    PreliminaryRouteBalancingPreviewV1,
    PreliminaryRouteBalancingRequirementV1,
)


def main() -> None:
    route_preview = PreliminaryRouteBalancingPreviewV1(
        ready=True,
        status="Preliminary route balancing preview ready",
        controlling_route_id="route-b",
        controlling_route_label="Heating Leg 1 / Leg 1B Branch subleg",
        controlling_route_dp="17482.3 Pa",
        rows=[
            PreliminaryRouteBalancingRequirementV1(
                route_id="route-a",
                route_label="Heating Leg 1 / Leg 1A Common subleg",
                sections="6",
                route_dp="16254.1 Pa",
                controlling_route_dp="17482.3 Pa",
                shortfall_dp="1228.2 Pa",
                required_added_resistance_dp="1228.2 Pa",
                controlling="No",
                status="Preliminary added resistance requirement",
            ),
            PreliminaryRouteBalancingRequirementV1(
                route_id="route-b",
                route_label="Heating Leg 1 / Leg 1B Branch subleg",
                sections="4",
                route_dp="17482.3 Pa",
                controlling_route_dp="17482.3 Pa",
                shortfall_dp="0.0 Pa",
                required_added_resistance_dp="0.0 Pa",
                controlling="Yes",
                status="Controlling route — no added resistance required",
            ),
        ],
    )

    resistance_basis = PreliminaryBalancingResistanceBasisV1(
        ready=True,
        status="Preliminary balancing resistance basis ready",
        rows=[
            PreliminaryBalancingResistanceRowV1(
                route_id="route-a",
                route_label="Heating Leg 1 / Leg 1A Common subleg",
                sections="6",
                flow_kg_s="0.09330 kg/s",
                required_added_dp="1228.2 Pa",
                resistance_pa_per_kg_s2="141093.1 Pa/(kg/s)²",
                controlling="No",
                status="Preliminary resistance basis calculated",
            ),
            PreliminaryBalancingResistanceRowV1(
                route_id="route-b",
                route_label="Heating Leg 1 / Leg 1B Branch subleg",
                sections="4",
                flow_kg_s="0.07660 kg/s",
                required_added_dp="0.0 Pa",
                resistance_pa_per_kg_s2="0.0 Pa/(kg/s)²",
                controlling="Yes",
                status="No added resistance required",
            ),
        ],
    )

    preview = build_balancing_point_duty_preview_v1(
        route_balancing_preview=route_preview,
        resistance_basis=resistance_basis,
    )

    print()
    print("H-S24-A — Balancing point duty preview")
    print("======================================")
    print("status:", preview.status)

    for row in preview.rows:
        print(
            row.route_label,
            "| flow:", row.flow_kg_s,
            "| route Δp:", row.route_dp,
            "| controlling Δp:", row.controlling_route_dp,
            "| added Δp:", row.required_added_dp,
            "| R:", row.required_resistance_pa_per_kg_s2,
            "| controlling:", row.controlling,
            "| status:", row.status,
        )

    assert preview.ready is True
    assert preview.status == "Balancing point duty preview ready"
    assert len(preview.rows) == 2

    first = preview.rows[0]
    assert first.route_id == "route-a"
    assert first.flow_kg_s == "0.09330 kg/s"
    assert first.route_dp == "16254.1 Pa"
    assert first.controlling_route_dp == "17482.3 Pa"
    assert first.required_added_dp == "1228.2 Pa"
    assert first.required_resistance_pa_per_kg_s2 == "141093.1 Pa/(kg/s)²"
    assert first.balancing_point_scope == "route/subleg balancing point"
    assert first.status == "Balancing point duty preview calculated"

    second = preview.rows[1]
    assert second.controlling == "Yes"
    assert second.required_added_dp == "0.0 Pa"
    assert second.required_resistance_pa_per_kg_s2 == "0.0 Pa/(kg/s)²"
    assert second.status == "Controlling route — no balancing duty required"

    print()
    print("OK — balancing point duty preview projection passed.")


if __name__ == "__main__":
    main()
