from __future__ import annotations

import math

from HVAC.dev.test_hs40b_common_main_leg_entry_pipe_sizing_v1 import (
    COMMON_1_ID,
    COMMON_2_ID,
    ENTRY_1_ID,
    ENTRY_2_ID,
    _project,
)
from HVAC.hydronics.local_losses.local_k_intent_v1 import (
    LocalKIntentV1,
    LocalKSectionIntentV1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    build_route_pressure_accumulator_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)


MAIN_IDS = (COMMON_1_ID, COMMON_2_ID, ENTRY_1_ID, ENTRY_2_ID)


def _install_lengths(project) -> dict[str, tuple[str, ...]]:
    intent = LocalKIntentV1()
    route_ids_by_leg: dict[str, tuple[str, ...]] = {}

    for index, section_id in enumerate(MAIN_IDS):
        intent.sections[section_id] = LocalKSectionIntentV1(
            section_id=section_id,
            length_m=float(index + 2),
            bend_90_count=index + 1,
            tee_through_count=index,
        )

    for leg in project.hydronic_topology.legs:
        subleg = leg.sublegs[0]
        basic = build_basic_ps_readonly_projection_v1(
            project,
            leg_id=leg.leg_id,
            subleg_id=subleg.subleg_id,
        )
        route_ids = tuple(
            result.section_id for result in basic.pipe_sizing_projection.results
        )
        route_ids_by_leg[leg.leg_id] = route_ids
        for section_id in route_ids:
            intent.sections[section_id] = LocalKSectionIntentV1(
                section_id=section_id,
                length_m=5.0,
                bend_90_count=1,
            )

    project.hydronic_local_k_intent = intent
    return route_ids_by_leg


def _assert_totals(row) -> None:
    ids = tuple(section.section_id for section in row.sections)
    assert len(ids) == len(set(ids))
    assert row.section_count == len(row.sections)
    assert math.isclose(
        row.straight_pressure_drop_total_Pa,
        sum(section.straight_pressure_drop_Pa for section in row.sections),
        rel_tol=1.0e-12,
    )
    assert math.isclose(
        row.local_pressure_drop_total_Pa,
        sum(section.local_pressure_drop_Pa for section in row.sections),
        rel_tol=1.0e-12,
    )
    assert math.isclose(
        row.route_pressure_drop_total_Pa,
        sum(section.section_total_pressure_drop_Pa for section in row.sections),
        rel_tol=1.0e-12,
    )


def main() -> None:
    project = _project()
    route_ids_by_leg = _install_lengths(project)
    before = project.to_dict()

    projection = build_route_pressure_accumulator_v1(project)
    rows_by_leg = {row.leg_id: row for row in projection.rows}
    leg_1 = rows_by_leg["leg-001"]
    leg_2 = rows_by_leg["leg-002"]
    assert leg_1.complete is True
    assert leg_2.complete is True

    leg_1_ids = tuple(section.section_id for section in leg_1.sections)
    leg_2_ids = tuple(section.section_id for section in leg_2.sections)
    assert leg_1_ids == (
        COMMON_1_ID,
        ENTRY_1_ID,
        *route_ids_by_leg["leg-001"],
    )
    assert leg_2_ids == (
        COMMON_1_ID,
        COMMON_2_ID,
        ENTRY_2_ID,
        *route_ids_by_leg["leg-002"],
    )
    assert COMMON_2_ID not in leg_1_ids
    assert leg_1_ids.count(COMMON_1_ID) == 1
    assert leg_2_ids.count(COMMON_1_ID) == 1

    for row in (leg_1, leg_2):
        _assert_totals(row)
        assert row.sections[0].section_scope == "common_main"
        assert any(
            section.section_scope == "leg_entry" for section in row.sections
        )
        assert any(
            section.section_scope == "route_section" for section in row.sections
        )

    repeated = build_route_pressure_accumulator_v1(project)
    assert repeated.rows == projection.rows
    assert project.to_dict() == before

    # A missing leg-2-only main length cannot make leg 1 incomplete.
    project.hydronic_local_k_intent.sections[COMMON_2_ID].length_m = None
    incomplete = build_route_pressure_accumulator_v1(project)
    incomplete_by_leg = {row.leg_id: row for row in incomplete.rows}
    assert incomplete_by_leg["leg-001"].complete is True
    assert incomplete_by_leg["leg-002"].complete is False
    assert incomplete_by_leg["leg-002"].route_pressure_drop_total_Pa is None

    print(
        "OK — H-S42-C route-specific common-main / leg-entry pressure "
        "accumulation passed."
    )


if __name__ == "__main__":
    main()
