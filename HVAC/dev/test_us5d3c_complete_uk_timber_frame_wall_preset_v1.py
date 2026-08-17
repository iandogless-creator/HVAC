from __future__ import annotations

from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)


def main() -> None:
    model = teaching_model_by_id_v1(TWO_PATH_MODEL_ID)
    evidence = model.evidence
    layers = evidence.layer_by_id()
    paths = {path.path_id: path for path in evidence.paths}

    assert model.model_id == "two_path_timber_stud_wall"
    assert evidence.construction_id == "teaching-stud-wall-001"
    assert "UK timber-frame" in evidence.label
    assert set(paths) == {"insulated-bay", "timber-stud"}
    assert paths["insulated-bay"].area_fraction == 0.85
    assert paths["timber-stud"].area_fraction == 0.15

    expected = {
        "lining",
        "service-void",
        "avcl",
        "insulation",
        "stud",
        "sheathing",
        "continuous-external-insulation",
        "breather-membrane",
        "external-cavity",
        "brick-outer-leaf",
        "rainscreen-cladding",
        "render-carrier-board",
    }
    assert set(layers) == expected
    assert layers["stud"].thickness_m == 0.140
    assert layers["sheathing"].label == "Structural OSB sheathing"
    assert layers["continuous-external-insulation"].included
    assert layers["brick-outer-leaf"].included
    assert not layers["service-void"].included
    assert not layers["rainscreen-cladding"].included
    assert not layers["render-carrier-board"].included
    assert "deferred condensation add-on" in layers["avcl"].property_notes
    assert "deferred condensation add-on" in layers["breather-membrane"].property_notes

    insulated = evidence.active_path_layer_ids("insulated-bay")
    timber = evidence.active_path_layer_ids("timber-stud")
    assert "insulation" in insulated and "stud" not in insulated
    assert "stud" in timber and "insulation" not in timber
    assert len(insulated) == len(timber)
    assert insulated.index("sheathing") == timber.index("sheathing")
    assert insulated.index("external-cavity") == timber.index("external-cavity")

    spacing = model.member_spacing_intent
    assert spacing is not None
    assert spacing.member_width_m == 0.038
    assert spacing.member_centres_m == 0.600
    assert spacing.declared_effective_member_fraction == 0.15

    # Every active layer remains resolvable by the existing V1 resistance authority.
    for layer_id in set(insulated).union(timber):
        assert layers[layer_id].resolved_resistance_m2K_W() > 0.0

    print(
        "OK — U-S5D3C complete UK timber-frame preset retains two-path "
        "framing authority and explicit configurable shared layers."
    )


if __name__ == "__main__":
    main()
