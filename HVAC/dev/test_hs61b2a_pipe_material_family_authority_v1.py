# ======================================================================
# H-S61-B2A — typed, persisted pipe-material-family authority
# ======================================================================

from __future__ import annotations

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.proportioning.proportioned_pipe_material_family_intent_v1 import (
    ProportionedPipeMaterialFamilyIntentV1,
    SUPPORTED_PROPORTIONED_PIPE_MATERIAL_FAMILIES_V1,
    proportioned_pipe_material_family_intent_from_dict_v1,
    proportioned_pipe_material_family_intent_to_dict_v1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    intent = ProportionedPipeMaterialFamilyIntentV1()
    assert intent.current_material_key == "copper"
    assert intent.proposed_material_key == "copper"
    assert intent.material_change_proposed is False
    assert intent.current_material_label == "Copper EN1057"

    assert SUPPORTED_PROPORTIONED_PIPE_MATERIAL_FAMILIES_V1 == (
        "copper",
        "mlcp",
        "pex",
        "steel",
    )
    for material_key in SUPPORTED_PROPORTIONED_PIPE_MATERIAL_FAMILIES_V1:
        assert get_material(material_key) is not None

    intent.set_proposed_material_family("MLCP")
    assert intent.proposed_material_key == "mlcp"
    assert intent.proposed_material_label == "MLCP"
    assert intent.material_change_proposed is True
    assert intent.current_material_key == "copper"

    intent.set_proposed_material_family("PEX-AL-PEX")
    assert intent.proposed_material_key == "pex"
    assert intent.proposed_material_label == "PEX-AL-PEX"
    assert intent.current_material_key == "copper"

    payload = proportioned_pipe_material_family_intent_to_dict_v1(intent)
    restored = proportioned_pipe_material_family_intent_from_dict_v1(payload)
    assert restored == intent

    restored.reset_proposed_material_family()
    assert restored.proposed_material_key == "copper"
    assert restored.material_change_proposed is False

    for excluded_key in ("pvc", "unknown", ""):
        try:
            intent.set_proposed_material_family(excluded_key)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Excluded material family was accepted: {excluded_key!r}"
            )

    project = ProjectState(project_id="hs61b2a", name="H-S61-B2A")
    project.hydronic_proportioned_pipe_material_family_intent = (
        ProportionedPipeMaterialFamilyIntentV1(
            current_material_key="copper",
            proposed_material_key="mlcp",
        )
    )
    project_payload = project.to_dict()
    raw = project_payload[
        "hydronic_proportioned_pipe_material_family_intent"
    ]
    assert raw["current_material_key"] == "copper"
    assert raw["proposed_material_key"] == "mlcp"

    project_restored = ProjectState.from_dict(project_payload)
    restored_intent = (
        project_restored
        .hydronic_proportioned_pipe_material_family_intent
    )
    assert restored_intent.current_material_key == "copper"
    assert restored_intent.proposed_material_key == "mlcp"

    legacy_payload = ProjectState(
        project_id="legacy",
        name="Legacy",
    ).to_dict()
    legacy_payload.pop(
        "hydronic_proportioned_pipe_material_family_intent"
    )
    legacy_restored = ProjectState.from_dict(legacy_payload)
    legacy_intent = (
        legacy_restored
        .hydronic_proportioned_pipe_material_family_intent
    )
    assert legacy_intent.current_material_key == "copper"
    assert legacy_intent.proposed_material_key == "copper"

    assert (
        project.hydronic_proportioned_pipe_resizing_schedule_acceptance_intent
        is None
    )

    print(
        "OK — H-S61-B2A typed persisted current/proposed "
        "pipe-material-family authority passed."
    )


if __name__ == "__main__":
    main()
