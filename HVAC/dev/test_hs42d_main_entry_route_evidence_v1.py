from __future__ import annotations

import math
from dataclasses import dataclass

from HVAC.dev.test_hs42c_route_specific_main_pressure_accumulation_v1 import (
    _install_lengths,
    _project,
)
from HVAC.hydronics.proportioning.chosen_basis_route_pressure_preview_v1 import (
    build_chosen_basis_route_pressure_preview_v1,
)
from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    build_circuit_return_path_comparison_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    build_route_pressure_accumulator_v1,
)


@dataclass(frozen=True)
class _Resolved:
    scope: str
    target_id: str
    target: str
    effective_basis: str
    source: str = "test"


def main() -> None:
    project = _project()
    _install_lengths(project)
    accumulator = build_route_pressure_accumulator_v1(project)

    for route in accumulator.rows:
        by_scope = {
            scope: sum(
                section.section_total_pressure_drop_Pa
                for section in route.sections
                if section.section_scope == scope
            )
            for scope in ("common_main", "leg_entry", "route_section")
        }
        assert math.isclose(
            route.common_main_pressure_drop_total_Pa, by_scope["common_main"]
        )
        assert math.isclose(
            route.leg_entry_pressure_drop_total_Pa, by_scope["leg_entry"]
        )
        assert math.isclose(
            route.route_section_pressure_drop_total_Pa, by_scope["route_section"]
        )

    comparison = build_circuit_return_path_comparison_v1(project)
    accumulator_by_route = {row.route_id: row for row in accumulator.rows}
    assert comparison.rows
    for row in comparison.rows:
        route = accumulator_by_route[row.route_id]
        main_entry = (
            route.common_main_pressure_drop_total_Pa
            + route.leg_entry_pressure_drop_total_Pa
        )
        assert math.isclose(row.physical_main_entry_dp_Pa, main_entry)
        assert math.isclose(
            row.direct_total_dp_Pa,
            row.flow_dp_Pa + row.direct_return_dp_Pa + main_entry,
        )
        assert math.isclose(
            row.reverse_return_total_dp_Pa,
            row.flow_dp_Pa
            + row.reverse_return_dp_Pa
            + row.rr_added_pressure_drop_Pa
            + main_entry,
        )

    route_id = comparison.rows[0].route_id
    route_rows = tuple(row for row in comparison.rows if row.route_id == route_id)
    route = accumulator_by_route[route_id]
    expected_direct = max(row.direct_total_dp_Pa for row in route_rows)
    expected_reverse = max(row.reverse_return_total_dp_Pa for row in route_rows)
    chosen = build_chosen_basis_route_pressure_preview_v1(
        [_Resolved("Route", route.subleg_id, route.route_label, "DIRECT_RETURN")],
        route_rows,
    )[0]
    assert chosen.chosen_dp_pa == expected_direct
    assert chosen.alternative_dp_pa == expected_reverse
    assert chosen.common_main_dp_pa == route.common_main_pressure_drop_total_Pa
    assert chosen.leg_entry_dp_pa == route.leg_entry_pressure_drop_total_Pa
    assert chosen.physical_main_entry_dp_pa == (
        route.common_main_pressure_drop_total_Pa
        + route.leg_entry_pressure_drop_total_Pa
    )

    # Removing one physical main length fails the affected totals closed.
    common_id = next(
        section.section_id
        for section in accumulator.rows[-1].sections
        if section.section_scope == "common_main"
    )
    project.hydronic_local_k_intent.sections[common_id].length_m = None
    incomplete = build_circuit_return_path_comparison_v1(project)
    assert any(row.direct_total_dp_Pa is None for row in incomplete.rows)
    assert any(row.reverse_return_total_dp_Pa is None for row in incomplete.rows)

    print(
        "OK — H-S42-D main/entry route evidence and chosen-basis "
        "no-double-counting passed."
    )


if __name__ == "__main__":
    main()
