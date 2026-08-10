from __future__ import annotations

from dataclasses import replace

from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    DECLARED_RESISTANCE_LAYER_BASIS,
    HOMOGENEOUS_LAYER_BASIS,
    HORIZONTAL_HEAT_FLOW,
    ConstructionHeatFlowPathEvidenceV1,
    ConstructionThermalLayerEvidenceV1,
    SharedConstructionLayerPathEvidenceV1,
    validate_shared_construction_layer_path_evidence_v1,
)


def homogeneous(layer_id: str, label: str, thickness: float, conductivity: float):
    return ConstructionThermalLayerEvidenceV1(
        layer_id=layer_id,
        label=label,
        basis=HOMOGENEOUS_LAYER_BASIS,
        thickness_m=thickness,
        conductivity_W_mK=conductivity,
        source_kind="legacy_workbook",
        source_ref="Ian composite construction examples",
    )


def main() -> None:
    wall = SharedConstructionLayerPathEvidenceV1(
        construction_id="wall-stud-001",
        label="Insulated timber stud wall",
        element_kind="external_wall",
        heat_flow_direction=HORIZONTAL_HEAT_FLOW,
        internal_surface_resistance_m2K_W=0.13,
        external_surface_resistance_m2K_W=0.04,
        layers=(
            homogeneous("lining", "Plasterboard", 0.0125, 0.19),
            homogeneous("insulation", "Mineral wool", 0.100, 0.035),
            homogeneous("stud", "Timber stud", 0.100, 0.13),
            homogeneous("sheathing", "Sheathing", 0.012, 0.13),
        ),
        shared_layer_ids=("lining", "sheathing"),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                path_id="insulated-bay",
                label="Insulated bay",
                area_fraction=0.85,
                layer_ids=("lining", "insulation", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                path_id="timber-stud",
                label="Timber stud",
                area_fraction=0.15,
                layer_ids=("lining", "stud", "sheathing"),
            ),
        ),
        source_kind="legacy_workbook",
        source_ref="Ian composite construction examples",
        source_version="audit-v1",
    )
    validation = validate_shared_construction_layer_path_evidence_v1(wall)
    assert validation.ready, validation.blockers
    assert wall.complete_path_layer_ids("insulated-bay") == (
        "lining",
        "insulation",
        "sheathing",
    )
    assert abs(wall.layer_by_id()["insulation"].resolved_resistance_m2K_W() - 2.857142857) < 1.0e-8

    modern_composite = SharedConstructionLayerPathEvidenceV1(
        construction_id="panel-three-path-001",
        label="Three-path composite panel",
        element_kind="wall_panel",
        layers=(
            homogeneous("face", "Common face", 0.008, 0.20),
            homogeneous("core-a", "Core zone A", 0.080, 0.024),
            homogeneous("core-b", "Core zone B", 0.080, 0.060),
            homogeneous("web", "Structural web", 0.080, 0.50),
        ),
        shared_layer_ids=("face",),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "zone-a", "Core A", 0.60, ("face", "core-a")
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "zone-b", "Core B", 0.30, ("face", "core-b")
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "web", "Web", 0.10, ("face", "web")
            ),
        ),
        source_kind="manufacturer",
        source_ref="Example composite product declaration",
    )
    assert validate_shared_construction_layer_path_evidence_v1(
        modern_composite
    ).ready

    declared = SharedConstructionLayerPathEvidenceV1(
        construction_id="declared-panel-001",
        label="Declared composite product",
        element_kind="insulated_panel",
        layers=(
            ConstructionThermalLayerEvidenceV1(
                layer_id="declared-product",
                label="Certified composite panel",
                basis=DECLARED_RESISTANCE_LAYER_BASIS,
                thickness_m=0.120,
                declared_resistance_m2K_W=4.80,
                source_kind="declared_product",
                source_ref="Product declaration ref",
                source_version="2026",
            ),
        ),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "declared", "Declared whole product", 1.0, ("declared-product",)
            ),
        ),
        source_kind="declared_product",
        source_ref="Product declaration ref",
    )
    declared_validation = validate_shared_construction_layer_path_evidence_v1(
        declared
    )
    assert declared_validation.ready, declared_validation.blockers
    assert declared.layers[0].resolved_resistance_m2K_W() == 4.80
    roundtrip = SharedConstructionLayerPathEvidenceV1.from_dict(
        declared.to_dict()
    )
    assert roundtrip == declared

    wrong_fraction = SharedConstructionLayerPathEvidenceV1.from_dict(
        wall.to_dict()
    )
    wrong_fraction = replace(
        wrong_fraction,
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "insulated-bay",
                "Insulated bay",
                0.79,
                ("lining", "insulation", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "timber-stud",
                "Timber stud",
                0.79,
                ("lining", "stud", "sheathing"),
            ),
        ),
    )
    fraction_validation = validate_shared_construction_layer_path_evidence_v1(
        wrong_fraction
    )
    assert not fraction_validation.ready
    assert "fractions total" in " ".join(fraction_validation.blockers)

    malformed_fraction = replace(
        wall,
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "bad-fraction",
                "Bad fraction",
                "not-a-number",  # type: ignore[arg-type]
                ("lining", "insulation", "sheathing"),
            ),
        ),
    )
    malformed_validation = validate_shared_construction_layer_path_evidence_v1(
        malformed_fraction
    )
    assert not malformed_validation.ready
    assert "must be numeric" in " ".join(malformed_validation.blockers)

    non_finite_fraction = replace(
        wall,
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "non-finite",
                "Non-finite fraction",
                float("nan"),
                ("lining", "insulation", "sheathing"),
            ),
        ),
    )
    non_finite_validation = validate_shared_construction_layer_path_evidence_v1(
        non_finite_fraction
    )
    assert not non_finite_validation.ready
    assert "must be finite" in " ".join(non_finite_validation.blockers)

    mixed_authority_layer = ConstructionThermalLayerEvidenceV1(
        layer_id="mixed",
        label="Mixed authority",
        basis=HOMOGENEOUS_LAYER_BASIS,
        thickness_m=0.1,
        conductivity_W_mK=0.04,
        declared_resistance_m2K_W=2.5,
    )
    try:
        mixed_authority_layer.resolved_resistance_m2K_W()
    except ValueError as exc:
        assert "mixes calculated and declared" in str(exc)
    else:
        raise AssertionError("Mixed resistance authority was not blocked")

    unknown_reference = SharedConstructionLayerPathEvidenceV1.from_dict(
        wall.to_dict()
    )
    unknown_reference = SharedConstructionLayerPathEvidenceV1(
        construction_id=unknown_reference.construction_id,
        label=unknown_reference.label,
        element_kind=unknown_reference.element_kind,
        layers=unknown_reference.layers,
        shared_layer_ids=unknown_reference.shared_layer_ids,
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "bad", "Bad path", 1.0, ("missing-layer",)
            ),
        ),
        source_ref="audit",
    )
    reference_validation = validate_shared_construction_layer_path_evidence_v1(
        unknown_reference
    )
    assert not reference_validation.ready
    assert "Unknown path bad layer" in " ".join(
        reference_validation.blockers
    )

    print(
        "OK — U-S1 shared homogeneous, declared-resistance and arbitrary "
        "N-path composite construction evidence passed."
    )


if __name__ == "__main__":
    main()
