# ======================================================================
# HVAC/dev/test_hs37b3_basic_ps_velocity_consumption_v1.py
# H-S37-B3 — Resolved velocity criterion reaches Basic PS sizing/evidence
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.dev.test_basic_ps_environment_delta_t_v1 import _emitter, _room
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.sizing.basic_ps_velocity_limit_resolver_v1 import (
    ENVIRONMENT_DEFAULT_SOURCE,
    LOCAL_SECTION_OVERRIDE_SOURCE,
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


TARGET_FLOW_KG_S = 0.1483


def _project() -> ProjectState:
    project = ProjectState(
        project_id="dev-hs37b3-velocity-consumption",
        name="DEV H-S37-B3 Velocity Consumption",
    )
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

    project.rooms["room-001"] = _room("room-001", "Boiler / Heat Source")
    project.rooms["room-002"] = _room("room-002", "Threshold room")

    subleg_id = primary_subleg_id_for_leg("leg-001")
    project.hydronic_topology = HydronicTopologyV1(
        heat_source_room_id="room-001",
        legs=[
            HydronicLegV1(
                leg_id="leg-001",
                label="Heating Leg 1",
                route_room_ids=["room-002"],
                index_room_id="room-002",
                sublegs=[
                    HydronicSublegV1(
                        subleg_id=subleg_id,
                        label="Primary subleg",
                        origin_room_id="",
                        route_room_ids=["room-002"],
                        index_room_id="room-002",
                        sublegs=[],
                    )
                ],
            )
        ],
    )

    carried_heat_W = TARGET_FLOW_KG_S * 4180.0 * 10.0
    project.emitters["emitter-threshold"] = _emitter(
        "emitter-threshold",
        "room-002",
        carried_heat_W,
    )
    return project


def _first_result(project: ProjectState):
    projection = build_basic_ps_readonly_projection_v1(
        project,
        leg_id="leg-001",
    )
    assert len(projection.pipe_sizing_projection.results) == 1
    return projection.pipe_sizing_projection.results[0]


def main() -> None:
    project = _project()

    baseline = _first_result(project)
    assert abs(baseline.carried_flow_kg_s - TARGET_FLOW_KG_S) < 1e-12
    assert baseline.pipe_size_label == "22 mm"
    assert baseline.applied_max_velocity_m_s == 1.0
    assert baseline.max_velocity_source == ENVIRONMENT_DEFAULT_SOURCE
    assert "Maximum velocity 1.00 m/s — Environment default" in baseline.status

    project.environment.basic_ps_max_velocity_m_s = 1.05
    inherited_105 = _first_result(project)
    assert inherited_105.pipe_size_label == "15 mm"
    assert 1.02 < inherited_105.velocity_m_s < 1.05
    assert inherited_105.applied_max_velocity_m_s == 1.05
    assert inherited_105.max_velocity_source == ENVIRONMENT_DEFAULT_SOURCE

    project.environment.basic_ps_max_velocity_m_s = 1.0
    intent = project.basic_hydronic_sizing_intent
    assert intent is not None
    intent.set_section_max_velocity_override(baseline.section_id, 1.05)

    locally_overridden = _first_result(project)
    assert locally_overridden.pipe_size_label == "15 mm"
    assert locally_overridden.applied_max_velocity_m_s == 1.05
    assert locally_overridden.max_velocity_source == LOCAL_SECTION_OVERRIDE_SOURCE
    assert "Local section override" in locally_overridden.status

    intent.clear_section_max_velocity_override(baseline.section_id)
    cleared = _first_result(project)
    assert cleared.pipe_size_label == "22 mm"
    assert cleared.applied_max_velocity_m_s == 1.0
    assert cleared.max_velocity_source == ENVIRONMENT_DEFAULT_SOURCE

    print(
        "OK — H-S37-B3 resolved Basic PS velocity consumption/evidence passed."
    )


if __name__ == "__main__":
    main()
