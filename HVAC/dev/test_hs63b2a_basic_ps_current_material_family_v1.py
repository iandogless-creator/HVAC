from __future__ import annotations

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.dev.test_hs40b_common_main_leg_entry_pipe_sizing_v1 import _project
from HVAC.hydronics.proportioning.proportioned_pipe_material_family_intent_v1 import (
    ProportionedPipeMaterialFamilyIntentV1,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    BASIC_PS_PIPE_MATERIAL_SIZE_KEYS_V1,
    DEFAULT_PIPE_CANDIDATES,
    build_basic_ps_pipe_candidates_for_material_v1,
    current_basic_ps_pipe_material_key_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.sizing.common_main_leg_entry_pipe_sizing_v1 import (
    build_common_main_leg_entry_pipe_sizing_v1,
)


def _assert_family(material_key: str) -> None:
    material = get_material(material_key)
    assert material is not None
    candidates = build_basic_ps_pipe_candidates_for_material_v1(material_key)
    expected_keys = BASIC_PS_PIPE_MATERIAL_SIZE_KEYS_V1[material_key]
    assert tuple(row.pipe_size_key for row in candidates) == expected_keys
    assert {row.material_key for row in candidates} == {material_key}
    assert {row.material_label for row in candidates} == {material.name}
    for candidate in candidates:
        assert candidate.pipe_size_key is not None
        size = material.sizes[candidate.pipe_size_key]
        assert abs(
            candidate.internal_diameter_m - float(size.id_mm) / 1000.0
        ) < 1.0e-12
        assert abs(
            candidate.roughness_m
            - float(material.roughness_mm) / 1000.0
        ) < 1.0e-12


def main() -> None:
    assert {row.material_key for row in DEFAULT_PIPE_CANDIDATES} == {"copper"}
    for family in ("copper", "mlcp", "pex", "steel"):
        _assert_family(family)

    project = _project()
    project.hydronic_proportioned_pipe_material_family_intent = (
        ProportionedPipeMaterialFamilyIntentV1(
            current_material_key="mlcp",
            proposed_material_key="copper",
        )
    )
    before = project.to_dict()
    assert current_basic_ps_pipe_material_key_v1(project) == "mlcp"

    main_projection = build_common_main_leg_entry_pipe_sizing_v1(project)
    assert main_projection.ready is True, main_projection.status
    assert main_projection.rows
    assert {row.basic_material_key for row in main_projection.rows} == {"mlcp"}
    assert all(row.basic_pipe_size_key in {16, 20, 26, 32} for row in main_projection.rows)
    assert all("×" in row.basic_pipe_size_label for row in main_projection.rows)

    route_projection = build_basic_ps_readonly_projection_v1(
        project,
        leg_id="leg-001",
    )
    route_results = route_projection.pipe_sizing_projection.results
    assert route_results
    assert {row.material_key for row in route_results} == {"mlcp"}
    assert all(row.pipe_size_key in {16, 20, 26, 32} for row in route_results)
    assert all("×" in row.pipe_size_label for row in route_results)

    # Proposed copper is preview-only and must not influence either path.
    assert project.hydronic_proportioned_pipe_material_family_intent.proposed_material_key == "copper"
    assert project.to_dict() == before

    legacy_project = _project()
    legacy_project.hydronic_proportioned_pipe_material_family_intent = None
    assert current_basic_ps_pipe_material_key_v1(legacy_project) == "copper"

    print(
        "OK — H-S63-B2A both Basic PS paths use exact persisted current "
        "material-family candidates and identity."
    )


if __name__ == "__main__":
    main()
