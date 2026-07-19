# ======================================================================
# HVAC/dev/test_hs40b_common_main_leg_entry_pipe_sizing_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.dev.test_basic_ps_environment_delta_t_v1 import _emitter, _room
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.sizing.basic_ps_velocity_limit_resolver_v1 import (
    ENVIRONMENT_DEFAULT_SOURCE,
    LOCAL_SECTION_OVERRIDE_SOURCE,
)
from HVAC.hydronics.sizing.common_main_leg_entry_pipe_sizing_v1 import (
    build_common_main_leg_entry_pipe_sizing_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)
from HVAC.project.project_state import ProjectState


LEG_1_FLOW_KG_S = 0.1483
LEG_2_FLOW_KG_S = 0.0500
COMMON_1_ID = "common-main-to-leg-001-section-001"
COMMON_2_ID = "common-main-to-leg-002-section-001"
ENTRY_1_ID = "leg-001-entry-section-001"
ENTRY_2_ID = "leg-002-entry-section-001"


def _leg(leg_id: str, label: str, room_id: str) -> HydronicLegV1:
    subleg_id = primary_subleg_id_for_leg(leg_id)
    return HydronicLegV1(
        leg_id=leg_id,
        label=label,
        route_room_ids=[room_id],
        index_room_id=room_id,
        sublegs=[
            HydronicSublegV1(
                subleg_id=subleg_id,
                label=f"{label} primary subleg",
                origin_room_id="",
                route_room_ids=[room_id],
                index_room_id=room_id,
                sublegs=[],
            )
        ],
    )


def _project() -> ProjectState:
    project = ProjectState(project_id="hs40b", name="H-S40-B")
    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
        design_flow_temp_c=75.0,
        design_return_temp_c=65.0,
        basic_ps_max_velocity_m_s=1.0,
    )
    project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1()

    project.rooms["heat-source"] = _room("heat-source", "Boiler / Heat Source")
    project.rooms["room-1"] = _room("room-1", "Leg 1 Room")
    project.rooms["room-2"] = _room("room-2", "Leg 2 Room")
    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="heat-source",
        legs=[
            _leg("leg-001", "Heating Leg 1", "room-1"),
            _leg("leg-002", "Heating Leg 2", "room-2"),
        ],
    )
    project.emitters["emitter-1"] = _emitter(
        "emitter-1",
        "room-1",
        LEG_1_FLOW_KG_S * 4180.0 * 10.0,
    )
    project.emitters["emitter-2"] = _emitter(
        "emitter-2",
        "room-2",
        LEG_2_FLOW_KG_S * 4180.0 * 10.0,
    )
    return project


def _rows_by_id(project: ProjectState):
    projection = build_common_main_leg_entry_pipe_sizing_v1(project)
    assert projection.ready is True, projection.blockers
    assert len(projection.common_main_rows) == 2
    assert len(projection.leg_entry_rows) == 2
    return {row.section_id: row for row in projection.rows}


def main() -> None:
    project = _project()
    before = project.to_dict()

    baseline = _rows_by_id(project)
    assert set(baseline) == {COMMON_1_ID, COMMON_2_ID, ENTRY_1_ID, ENTRY_2_ID}
    assert baseline[COMMON_1_ID].carried_leg_ids == ("leg-001", "leg-002")
    assert baseline[COMMON_2_ID].carried_leg_ids == ("leg-002",)
    assert baseline[COMMON_1_ID].basic_pipe_size_label == "22 mm"
    assert baseline[COMMON_2_ID].basic_pipe_size_label == "10 mm"
    assert baseline[ENTRY_1_ID].basic_pipe_size_label == "22 mm"
    assert baseline[ENTRY_2_ID].basic_pipe_size_label == "10 mm"

    for row in baseline.values():
        assert row.basic_friction_method == "Haaland"
        assert row.basic_velocity_m_s > 0.0
        assert row.basic_reynolds_number > 0.0
        assert row.basic_friction_factor > 0.0
        assert row.basic_pressure_gradient_Pa_per_m > 0.0
        assert row.applied_max_velocity_m_s == 1.0
        assert row.max_velocity_source == ENVIRONMENT_DEFAULT_SOURCE

    assert project.to_dict() == before

    project.environment.basic_ps_max_velocity_m_s = 1.05
    inherited = _rows_by_id(project)
    assert inherited[ENTRY_1_ID].basic_pipe_size_label == "15 mm"
    assert inherited[ENTRY_1_ID].max_velocity_source == ENVIRONMENT_DEFAULT_SOURCE
    assert inherited[COMMON_1_ID].basic_pipe_size_label == "22 mm"

    project.environment.basic_ps_max_velocity_m_s = 1.0
    intent = project.basic_hydronic_sizing_intent
    assert intent is not None
    intent.set_section_max_velocity_override(COMMON_1_ID, 1.50)
    overridden = _rows_by_id(project)
    assert overridden[COMMON_1_ID].basic_pipe_size_label == "15 mm"
    assert overridden[COMMON_1_ID].applied_max_velocity_m_s == 1.50
    assert overridden[COMMON_1_ID].max_velocity_source == LOCAL_SECTION_OVERRIDE_SOURCE
    assert overridden[ENTRY_1_ID].basic_pipe_size_label == "22 mm"
    assert overridden[ENTRY_1_ID].max_velocity_source == ENVIRONMENT_DEFAULT_SOURCE

    print(
        "OK — H-S40-B common-main / leg-entry Basic PS sizing passed."
    )


if __name__ == "__main__":
    main()
