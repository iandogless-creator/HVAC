# ======================================================================
# H-S61-H1A — Committed material/bore hydraulic-input identity
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    build_committed_proportioning_hydraulic_input_authority_v1,
    committed_proportioning_hydraulic_input_authority_from_dict_v1,
    committed_proportioning_hydraulic_input_authority_to_dict_v1,
)


def _initial_copper_authority():
    section = SimpleNamespace(
        section_id="section-1",
        section_scope="common_main",
        order=1,
        from_label="Boiler",
        to_label="T1",
        carried_flow_kg_s=0.20,
        pipe_size_label="22 mm",
        dn=22,
        length_m=8.0,
        k_total=1.5,
        velocity_m_s=0.64,
        reynolds_number=12800.0,
        friction_factor=0.029,
        friction_method="colebrook",
        colebrook_iteration_count=5,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=120.0,
        straight_pressure_drop_Pa=960.0,
        local_pressure_drop_Pa=31.0,
        section_total_pressure_drop_Pa=991.0,
    )
    route_projection = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-1",
                complete=True,
                sections=(section,),
            ),
        ),
    )
    chosen = (
        SimpleNamespace(
            route_id="route-1",
            route="Route 1",
            basis="F+R",
            chosen_dp_pa=991.0,
            is_controlling=True,
            common_main_dp_pa=991.0,
            leg_entry_dp_pa=None,
            physical_main_entry_dp_pa=None,
        ),
    )
    resistance = SimpleNamespace(
        rows=(
            SimpleNamespace(
                route_id="route-1",
                required_added_dp=0.0,
                resistance_pa_per_kg_s2=0.0,
            ),
        ),
    )
    return build_committed_proportioning_hydraulic_input_authority_v1(
        route_pressure_projection=route_projection,
        chosen_controlling_rows=chosen,
        resistance_basis=resistance,
    )


def main() -> None:
    copper = _initial_copper_authority()
    assert copper.ready is True
    assert len(copper.sections) == 1
    copper_section = copper.sections[0]
    assert copper_section.material_key == "copper"
    assert copper_section.material_label == "Copper EN1057"
    assert abs(copper_section.internal_diameter_m - 0.020) < 1.0e-12
    assert abs(copper_section.material_roughness_m - 0.0000015) < 1.0e-12

    mlcp_section = replace(
        copper_section,
        pipe_size_label="20×2 mm",
        dn=20,
        material_key="mlcp",
        material_label="MLCP",
        internal_diameter_m=0.016,
        material_roughness_m=0.000007,
    )
    mlcp = replace(copper, sections=(mlcp_section,))
    payload = committed_proportioning_hydraulic_input_authority_to_dict_v1(
        mlcp
    )
    assert payload is not None
    raw = payload["sections"][0]
    assert raw["material_key"] == "mlcp"
    assert raw["material_label"] == "MLCP"
    assert raw["internal_diameter_m"] == 0.016
    assert raw["material_roughness_m"] == 0.000007

    restored = (
        committed_proportioning_hydraulic_input_authority_from_dict_v1(
            payload
        )
    )
    assert restored is not None
    assert restored.sections == mlcp.sections

    legacy_payload = (
        committed_proportioning_hydraulic_input_authority_to_dict_v1(copper)
    )
    assert legacy_payload is not None
    legacy_raw = legacy_payload["sections"][0]
    for key in (
        "material_key",
        "material_label",
        "internal_diameter_m",
        "material_roughness_m",
    ):
        legacy_raw.pop(key)
    legacy = (
        committed_proportioning_hydraulic_input_authority_from_dict_v1(
            legacy_payload
        )
    )
    assert legacy is not None
    assert legacy.sections[0].material_key == "copper"
    assert legacy.sections[0].internal_diameter_m == 0.020

    invalid_payload = (
        committed_proportioning_hydraulic_input_authority_to_dict_v1(mlcp)
    )
    assert invalid_payload is not None
    invalid_payload["sections"][0]["internal_diameter_m"] = 0.020
    assert (
        committed_proportioning_hydraulic_input_authority_from_dict_v1(
            invalid_payload
        )
        is None
    )

    print(
        "OK — H-S61-H1A committed material, size, actual bore and "
        "roughness authority passed."
    )


if __name__ == "__main__":
    main()
