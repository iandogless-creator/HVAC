from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    _freeze_section,
)
from HVAC.hydronics.proportioning.common_main_leg_entry_pressure_authority_v1 import (
    _basic_ps_main_pipe_identity_v1,
    build_common_main_leg_entry_pressure_authority_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_material_family_intent_v1 import (
    ProportionedPipeMaterialFamilyIntentV1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    _basic_ps_result_pipe_identity_v1,
    _main_pressure_contribution_v1,
)


SECTION_IDS = (COMMON_1_ID, COMMON_2_ID, ENTRY_1_ID, ENTRY_2_ID)


def main() -> None:
    misleading = SimpleNamespace(
        material_key="pex",
        pipe_size_key=26,
        pipe_size_label="Copper 999 mm",
    )
    assert _basic_ps_result_pipe_identity_v1(misleading) == ("pex", 26)
    misleading_main = SimpleNamespace(
        basic_material_key="steel",
        basic_pipe_size_key=32,
        basic_pipe_size_label="MLCP 16×2 mm",
    )
    assert _basic_ps_main_pipe_identity_v1(misleading_main) == ("steel", 32)

    project = _project()
    project.hydronic_proportioned_pipe_material_family_intent = (
        ProportionedPipeMaterialFamilyIntentV1(
            current_material_key="mlcp",
            proposed_material_key="copper",
        )
    )
    project.hydronic_local_k_intent = LocalKIntentV1(
        sections={
            section_id: LocalKSectionIntentV1(
                section_id=section_id,
                length_m=float(index + 2),
            )
            for index, section_id in enumerate(SECTION_IDS)
        }
    )
    before = project.to_dict()
    projection = build_common_main_leg_entry_pressure_authority_v1(project)
    assert projection.ready is True, projection.blockers
    assert projection.complete is True, projection.missing_section_ids
    assert projection.rows
    for row in projection.rows:
        assert row.material == "mlcp"
        assert row.material_label == "MLCP"
        assert row.dn in {16, 20, 26, 32}
        assert row.internal_diameter_m is not None
        assert row.material_roughness_m == 0.000007
        assert "×" in row.pipe_size_label

    contribution = _main_pressure_contribution_v1(projection.rows[0])
    frozen = _freeze_section(contribution, route_ids=("route-a",))
    assert frozen.material_key == "mlcp"
    assert frozen.material_label == "MLCP"
    assert frozen.dn == contribution.dn
    assert frozen.internal_diameter_m == contribution.internal_diameter_m
    assert frozen.material_roughness_m == contribution.material_roughness_m
    assert project.to_dict() == before

    route_source = Path(
        "HVAC/hydronics/proportioning/route_pressure_accumulator_v1.py"
    ).read_text(encoding="utf-8")
    main_source = Path(
        "HVAC/hydronics/proportioning/"
        "common_main_leg_entry_pressure_authority_v1.py"
    ).read_text(encoding="utf-8")
    assert "hydronic_pipe_material" not in route_source
    assert "hydronic_pipe_material" not in main_source
    assert "_dn_from_pipe_size_label_v1" not in route_source
    assert "_dn_from_label_v1" not in main_source

    print(
        "OK — H-S63-B2B exact Basic PS material, size, bore and roughness "
        "reach route/main pressure and committed freezing."
    )


if __name__ == "__main__":
    main()
