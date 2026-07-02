from __future__ import annotations

from types import SimpleNamespace

from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    _dn_from_pipe_size_label_v1,
    _route_pressure_material_v1,
    build_route_pressure_accumulator_v1,
)
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    BasicPSTopologySectionV1,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    BasicPSPipeCandidateV1,
    build_basic_ps_pipe_sizing_v1,
)


def test_dn_parser_reads_common_labels() -> None:
    assert _dn_from_pipe_size_label_v1("10 mm") == 10
    assert _dn_from_pipe_size_label_v1("DN15") == 15
    assert _dn_from_pipe_size_label_v1("Copper 22 mm") == 22


def test_material_defaults_to_copper() -> None:
    project_state = SimpleNamespace()
    assert _route_pressure_material_v1(project_state) == "copper"


def test_mass_flow_wrapper_matches_basic_ps_candidate_for_copper_10() -> None:
    section = BasicPSTopologySectionV1(
        section_id="section-001",
        order=1,
        from_label="A",
        to_room_label="B",
        carried_heat_W=1000.0,
        carried_flow_kg_s=0.02,
        is_index_room=False,
        is_terminal=False,
    )

    candidate = BasicPSPipeCandidateV1(
        pipe_size_label="10 mm",
        internal_diameter_m=0.010,
        roughness_m=0.0000015,
    )

    basic_result = build_basic_ps_pipe_sizing_v1(
        sections=[section],
        candidates=[candidate],
    ).results[0]

    wrapper_result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=basic_result.carried_flow_kg_s,
        material="copper",
        dn=10,
        length_m=1.0,
        friction_method="colebrook",
    )

    assert abs(wrapper_result.velocity_m_s - basic_result.velocity_m_s) < 1.0e-12
    assert wrapper_result.pressure_gradient_pa_per_m > 0.0
    assert wrapper_result.colebrook_converged is True


if __name__ == "__main__":
    test_dn_parser_reads_common_labels()
    test_material_defaults_to_copper()
    test_mass_flow_wrapper_matches_basic_ps_candidate_for_copper_10()
    print("OK — H-S29-E route pressure uses hydronic mass-flow wrapper.")