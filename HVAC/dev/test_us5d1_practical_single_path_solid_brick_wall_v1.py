from __future__ import annotations

from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    resolve_legacy_compatible_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    validate_shared_construction_layer_path_evidence_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    ONE_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)


def main() -> None:
    model = teaching_model_by_id_v1(ONE_PATH_MODEL_ID)
    evidence = model.evidence

    assert model.label == "One path — existing solid brick wall"
    assert "Practical existing-wall geometry" in model.description
    assert "No cavity, insulation or render" in model.description
    assert "illustrative" in model.description

    assert evidence.label == "Existing 215 mm solid brick wall"
    assert evidence.element_kind == "external_wall"
    assert evidence.source_version == "v1-practical-geometry"
    assert len(evidence.paths) == 1
    assert evidence.paths[0].label == "Uniform wall path"
    assert evidence.paths[0].area_fraction == 1.0
    assert evidence.paths[0].layer_ids == ("plaster", "masonry")
    assert evidence.shared_layer_ids == ("plaster", "masonry")

    layers = evidence.layer_by_id()
    assert tuple(layers) == ("plaster", "masonry")
    assert layers["plaster"].label == "Internal plaster"
    assert layers["plaster"].thickness_m == 0.013
    assert layers["masonry"].label == "Solid brickwork"
    assert layers["masonry"].thickness_m == 0.215
    assert "verified catalogue source not yet selected" in (
        layers["masonry"].source_ref
    )
    assert "One-brick solid-wall thickness" in (
        layers["masonry"].property_notes
    )
    assert not any(
        term in layer.label.lower()
        for layer in evidence.layers
        for term in ("cavity", "insulation", "render")
    )

    validation = validate_shared_construction_layer_path_evidence_v1(evidence)
    assert validation.ready, validation.blockers

    legacy = resolve_legacy_compatible_u_value_v1(evidence)
    iso = resolve_iso_6946_combined_u_value_v1(evidence)
    assert legacy.ready, legacy.blockers
    assert iso.ready, iso.blockers
    expected_u = 1.0 / (0.13 + (0.013 / 0.57) + (0.215 / 0.77) + 0.04)
    assert abs(legacy.u_value_W_m2K - expected_u) < 1.0e-12
    assert abs(iso.uncorrected_u_value_W_m2K - expected_u) < 1.0e-12

    print(
        "OK — U-S5D1 practical single-path existing 215 mm solid-brick "
        "wall geometry passed."
    )


if __name__ == "__main__":
    main()
