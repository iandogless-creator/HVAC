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
from HVAC.hydronics.proportioning.common_main_leg_entry_pressure_authority_v1 import (
    build_common_main_leg_entry_pressure_authority_v1,
)


SECTION_IDS = (COMMON_1_ID, COMMON_2_ID, ENTRY_1_ID, ENTRY_2_ID)


def main() -> None:
    project = _project()

    incomplete = build_common_main_leg_entry_pressure_authority_v1(project)
    assert incomplete.ready is True
    assert incomplete.complete is False
    assert incomplete.missing_section_ids == SECTION_IDS
    assert len(incomplete.rows) == 4

    project.hydronic_local_k_intent = LocalKIntentV1(
        sections={
            section_id: LocalKSectionIntentV1(
                section_id=section_id,
                length_m=float(index + 2),
                bend_90_count=index + 1,
                tee_through_count=index,
                misc_k=0.25 * index,
            )
            for index, section_id in enumerate(SECTION_IDS)
        }
    )
    before = project.to_dict()
    projection = build_common_main_leg_entry_pressure_authority_v1(project)

    assert projection.ready is True, projection.blockers
    assert projection.complete is True, projection.missing_section_ids
    assert projection.missing_section_ids == ()
    assert len(projection.rows) == len(SECTION_IDS)
    assert tuple(row.section_id for row in projection.rows) == SECTION_IDS
    assert len({row.section_id for row in projection.rows}) == len(SECTION_IDS)

    for row in projection.rows:
        assert row.complete is True
        assert row.length_m is not None and row.length_m > 0.0
        assert row.k_total >= 0.0
        assert row.velocity_m_s > 0.0
        assert row.reynolds_number > 0.0
        assert row.friction_factor > 0.0
        assert row.friction_method == "colebrook"
        assert row.colebrook_converged is True
        assert row.colebrook_iteration_count > 0
        assert row.pressure_gradient_Pa_per_m > 0.0
        assert math.isclose(
            row.straight_pressure_drop_Pa,
            row.pressure_gradient_Pa_per_m * row.length_m,
            rel_tol=1.0e-12,
        )
        assert math.isclose(
            row.section_total_pressure_drop_Pa,
            row.straight_pressure_drop_Pa + row.local_pressure_drop_Pa,
            rel_tol=1.0e-12,
        )
        assert "Colebrook" in row.status

    # Rebuilding is deterministic and cannot double-count stable sections.
    repeated = build_common_main_leg_entry_pressure_authority_v1(project)
    assert repeated.rows == projection.rows
    assert sum(
        row.section_total_pressure_drop_Pa for row in repeated.rows
    ) == sum(
        row.section_total_pressure_drop_Pa for row in projection.rows
    )

    # Calculated pressure evidence is never persisted as authority.
    assert project.to_dict() == before

    print(
        "OK — H-S42-A common-main / leg-entry length and Local-K "
        "pressure authority passed."
    )


if __name__ == "__main__":
    main()
