from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    HOMOGENEOUS_LAYER_BASIS,
    ConstructionHeatFlowPathEvidenceV1,
    ConstructionThermalLayerEvidenceV1,
    SharedConstructionLayerPathEvidenceV1,
)
from HVAC.constructions.physics.u_value_method_comparison_acceptance_v1 import (
    NOT_SET_U_VALUE_METHOD,
    UValueMethodAcceptanceIntentV1,
    build_u_value_method_acceptance_intent_v1,
    build_u_value_method_comparison_v1,
    construction_evidence_fingerprint_v1,
    resolve_accepted_u_value_method_v1,
)


def layer(layer_id: str, thickness: float, conductivity: float):
    return ConstructionThermalLayerEvidenceV1(
        layer_id=layer_id,
        label=layer_id.title(),
        basis=HOMOGENEOUS_LAYER_BASIS,
        thickness_m=thickness,
        conductivity_W_mK=conductivity,
        source_kind="comparison_test",
        source_ref="U-S4 fixture",
    )


def main() -> None:
    wall = SharedConstructionLayerPathEvidenceV1(
        construction_id="comparison-wall-001",
        label="Comparison stud wall",
        element_kind="external_wall",
        layers=(
            layer("lining", 0.0125, 0.19),
            layer("insulation", 0.100, 0.035),
            layer("stud", 0.100, 0.13),
            layer("sheathing", 0.012, 0.13),
        ),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "bay", "Bay", 0.85,
                ("lining", "insulation", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "stud", "Stud", 0.15,
                ("lining", "stud", "sheathing"),
            ),
        ),
        shared_layer_ids=("lining", "sheathing"),
        internal_surface_resistance_m2K_W=0.13,
        external_surface_resistance_m2K_W=0.04,
        source_ref="U-S4 fixture",
    )

    comparison = build_u_value_method_comparison_v1(wall)
    assert comparison.ready, comparison.blockers
    assert len(comparison.rows) == 2
    assert comparison.rows[0].method == LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1
    assert comparison.rows[1].method == ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1
    assert comparison.iso_minus_legacy_W_m2K is not None
    assert comparison.iso_minus_legacy_percent is not None
    assert comparison.evidence_fingerprint == construction_evidence_fingerprint_v1(wall)

    single_path = replace(
        wall,
        construction_id="comparison-solid-wall-001",
        label="Single-path solid wall",
        layers=(layer("solid-masonry", 0.215, 0.77),),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "solid", "Solid masonry", 1.0, ("solid-masonry",)
            ),
        ),
        shared_layer_ids=("solid-masonry",),
    )
    single_comparison = build_u_value_method_comparison_v1(single_path)
    assert single_comparison.ready, single_comparison.blockers
    assert abs(single_comparison.iso_minus_legacy_W_m2K) < 1.0e-12
    assert abs(single_comparison.iso_minus_legacy_percent) < 1.0e-12

    three_path = replace(
        wall,
        construction_id="comparison-three-path-panel-001",
        label="Three-path composite panel",
        layers=(
            wall.layers[0],
            wall.layers[1],
            wall.layers[2],
            layer("structural-web", 0.100, 0.50),
            wall.layers[3],
        ),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "core-a", "Core A", 0.60,
                ("lining", "insulation", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "core-b", "Core B", 0.30,
                ("lining", "stud", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "web", "Structural web", 0.10,
                ("lining", "structural-web", "sheathing"),
            ),
        ),
    )
    three_path_comparison = build_u_value_method_comparison_v1(three_path)
    assert three_path_comparison.ready, three_path_comparison.blockers
    assert len(three_path_comparison.rows) == 2
    assert three_path_comparison.iso_minus_legacy_W_m2K is not None

    legacy_intent = build_u_value_method_acceptance_intent_v1(
        wall,
        LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
    )
    assert UValueMethodAcceptanceIntentV1.from_dict(
        legacy_intent.to_dict()
    ) == legacy_intent
    legacy_acceptance = resolve_accepted_u_value_method_v1(wall, legacy_intent)
    assert legacy_acceptance.ready, legacy_acceptance.blockers
    assert legacy_acceptance.accepted_u_value_W_m2K == comparison.rows[0].u_value_W_m2K
    assert "explicitly selected" in " ".join(legacy_acceptance.warnings)

    iso_intent = build_u_value_method_acceptance_intent_v1(
        wall,
        ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
    )
    iso_acceptance = resolve_accepted_u_value_method_v1(wall, iso_intent)
    assert iso_acceptance.ready, iso_acceptance.blockers
    assert iso_acceptance.accepted_u_value_W_m2K == comparison.rows[1].u_value_W_m2K
    assert "correction terms are not applied" in " ".join(iso_acceptance.warnings)

    not_set = build_u_value_method_acceptance_intent_v1(
        wall,
        NOT_SET_U_VALUE_METHOD,
    )
    not_set_result = resolve_accepted_u_value_method_v1(wall, not_set)
    assert not not_set_result.ready
    assert "method is not set" in " ".join(not_set_result.blockers)

    changed_wall = replace(
        wall,
        layers=(replace(wall.layers[0], thickness_m=0.015), *wall.layers[1:]),
    )
    stale_result = resolve_accepted_u_value_method_v1(changed_wall, iso_intent)
    assert not stale_result.ready
    assert "stale" in " ".join(stale_result.blockers)

    wrong_identity = replace(iso_intent, construction_id="another-wall")
    wrong_identity_result = resolve_accepted_u_value_method_v1(wall, wrong_identity)
    assert not wrong_identity_result.ready
    assert "identity" in " ".join(wrong_identity_result.blockers)

    invalid_method = replace(iso_intent, selected_method="mystery_method")
    invalid_method_result = resolve_accepted_u_value_method_v1(wall, invalid_method)
    assert not invalid_method_result.ready
    assert "Unsupported" in " ".join(invalid_method_result.blockers)

    unequal_stud = replace(wall.layers[2], thickness_m=0.090)
    incomplete_iso = replace(
        wall,
        layers=(wall.layers[0], wall.layers[1], unequal_stud, wall.layers[3]),
    )
    incomplete_comparison = build_u_value_method_comparison_v1(incomplete_iso)
    assert not incomplete_comparison.ready
    incomplete_intent = build_u_value_method_acceptance_intent_v1(
        incomplete_iso,
        LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
    )
    incomplete_acceptance = resolve_accepted_u_value_method_v1(
        incomplete_iso,
        incomplete_intent,
    )
    assert not incomplete_acceptance.ready
    assert "equal nominal thickness" in " ".join(incomplete_acceptance.blockers)

    module_source = Path(
        "HVAC/constructions/physics/u_value_method_comparison_acceptance_v1.py"
    ).read_text(encoding="utf-8")
    assert "ProjectState" not in module_source
    assert "u_value_W_m2K =" not in module_source

    print(
        "OK — U-S4 side-by-side legacy/ISO comparison and fresh explicit "
        "method acceptance passed."
    )


if __name__ == "__main__":
    main()
