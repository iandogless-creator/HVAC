from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.proportioning.chosen_basis_controlling_route_preview_v1 import (
    build_chosen_basis_controlling_route_preview_v1,
)


@dataclass(frozen=True)
class ChosenBasisRoutePressureRow:
    scope: str
    route_id: str
    route: str
    basis: str
    chosen_dp_pa: float
    source: str


def main() -> None:
    rows = [
        ChosenBasisRoutePressureRow(
            scope="Common",
            route_id="leg-001-primary-subleg",
            route="Leg 1A Common subleg",
            basis="F+RR",
            chosen_dp_pa=12839.0,
            source="subleg override",
        ),
        ChosenBasisRoutePressureRow(
            scope="Branch",
            route_id="leg-001-subleg-b",
            route="Leg 1B Branch subleg",
            basis="F+RR",
            chosen_dp_pa=28744.1,
            source="subleg override",
        ),
        ChosenBasisRoutePressureRow(
            scope="Common",
            route_id="leg-002-primary-subleg",
            route="Leg 2A Common subleg",
            basis="F&R",
            chosen_dp_pa=12754.4,
            source="inherit leg",
        ),
        ChosenBasisRoutePressureRow(
            scope="Branch",
            route_id="leg-002-subleg-b",
            route="Leg 2B Branch subleg",
            basis="F&R",
            chosen_dp_pa=29073.7,
            source="inherit parent subleg",
        ),
    ]

    preview = build_chosen_basis_controlling_route_preview_v1(rows)

    assert len(preview) == 4

    controlling = [row for row in preview if row.is_controlling]
    assert len(controlling) == 1

    assert controlling[0].route_id == "leg-002-subleg-b"
    assert controlling[0].chosen_dp_pa == 29073.7
    assert controlling[0].dp_below_controlling_pa == 0.0
    assert "controlling route" in controlling[0].status

    leg_1b = next(row for row in preview if row.route_id == "leg-001-subleg-b")
    assert leg_1b.is_controlling is False
    assert round(leg_1b.dp_below_controlling_pa or 0.0, 1) == 329.6
    assert "below" in leg_1b.status

    leg_1a = next(row for row in preview if row.route_id == "leg-001-primary-subleg")
    assert round(leg_1a.dp_below_controlling_pa or 0.0, 1) == 16234.7

    print("OK — H-S27-D chosen-basis controlling route preview passed.")


if __name__ == "__main__":
    main()
