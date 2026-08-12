from __future__ import annotations

from dataclasses import replace

from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
    resolve_legacy_compatible_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    DECLARED_RESISTANCE_LAYER_BASIS,
    HOMOGENEOUS_LAYER_BASIS,
    HORIZONTAL_HEAT_FLOW,
    ConstructionHeatFlowPathEvidenceV1,
    ConstructionThermalLayerEvidenceV1,
    SharedConstructionLayerPathEvidenceV1,
)


def layer(layer_id: str, thickness_m: float, conductivity: float):
    return ConstructionThermalLayerEvidenceV1(
        layer_id=layer_id,
        label=layer_id.replace("-", " ").title(),
        basis=HOMOGENEOUS_LAYER_BASIS,
        thickness_m=thickness_m,
        conductivity_W_mK=conductivity,
        source_kind="legacy_workbook",
        source_ref="Audited legacy construction input",
    )


def main() -> None:
    wall = SharedConstructionLayerPathEvidenceV1(
        construction_id="legacy-stud-wall-001",
        label="Legacy insulated timber stud wall",
        element_kind="external_wall",
        heat_flow_direction=HORIZONTAL_HEAT_FLOW,
        internal_surface_resistance_m2K_W=0.13,
        external_surface_resistance_m2K_W=0.04,
        layers=(
            layer("lining", 0.0125, 0.19),
            layer("insulation", 0.100, 0.035),
            layer("stud", 0.100, 0.13),
            layer("sheathing", 0.012, 0.13),
        ),
        shared_layer_ids=("lining", "sheathing"),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "insulated-bay",
                "Insulated bay",
                0.85,
                ("lining", "insulation", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "timber-stud",
                "Timber stud",
                0.15,
                ("lining", "stud", "sheathing"),
            ),
        ),
        source_kind="legacy_workbook",
        source_ref="Audited legacy construction input",
    )

    result = resolve_legacy_compatible_u_value_v1(wall)
    assert result.ready, result.blockers
    assert result.method == LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1
    assert len(result.paths) == 2

    common_r = (0.0125 / 0.19) + (0.012 / 0.13)
    expected_insulation_r = 0.13 + common_r + (0.100 / 0.035) + 0.04
    expected_stud_r = 0.13 + common_r + (0.100 / 0.13) + 0.04
    expected_u = (0.85 / expected_insulation_r) + (0.15 / expected_stud_r)
    assert abs(result.u_value_W_m2K - expected_u) < 1.0e-12
    assert abs(result.effective_resistance_m2K_W - (1.0 / expected_u)) < 1.0e-12
    assert abs(
        sum(row.weighted_u_contribution_W_m2K for row in result.paths)
        - result.u_value_W_m2K
    ) < 1.0e-12
    assert result.paths[0].layers[1].layer_id == "insulation"

    single_path = SharedConstructionLayerPathEvidenceV1(
        construction_id="legacy-solid-wall-001",
        label="Legacy solid wall",
        element_kind="external_wall",
        layers=(layer("masonry", 0.215, 0.77),),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "solid", "Solid path", 1.0, ("masonry",)
            ),
        ),
        internal_surface_resistance_m2K_W=0.13,
        external_surface_resistance_m2K_W=0.04,
        source_ref="Legacy series check",
    )
    single_result = resolve_legacy_compatible_u_value_v1(single_path)
    assert single_result.ready, single_result.blockers
    expected_single_u = 1.0 / (0.13 + (0.215 / 0.77) + 0.04)
    assert abs(single_result.u_value_W_m2K - expected_single_u) < 1.0e-12

    declared_product = SharedConstructionLayerPathEvidenceV1(
        construction_id="legacy-declared-panel-001",
        label="Declared panel",
        element_kind="panel",
        layers=(
            ConstructionThermalLayerEvidenceV1(
                layer_id="panel",
                label="Declared panel",
                basis=DECLARED_RESISTANCE_LAYER_BASIS,
                declared_resistance_m2K_W=4.8,
                source_kind="declared_product",
                source_ref="Product declaration",
            ),
        ),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "panel", "Panel path", 1.0, ("panel",)
            ),
        ),
        internal_surface_resistance_m2K_W=0.10,
        external_surface_resistance_m2K_W=0.04,
        source_ref="Product declaration",
    )
    declared_result = resolve_legacy_compatible_u_value_v1(declared_product)
    assert declared_result.ready, declared_result.blockers
    assert abs(declared_result.u_value_W_m2K - (1.0 / 4.94)) < 1.0e-12

    three_path = replace(
        wall,
        construction_id="legacy-three-path-001",
        layers=wall.layers + (layer("web", 0.100, 0.50),),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "bay-a", "Bay A", 0.60, ("lining", "insulation", "sheathing")
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "stud", "Stud", 0.30, ("lining", "stud", "sheathing")
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "web", "Web", 0.10, ("lining", "web", "sheathing")
            ),
        ),
    )
    three_path_result = resolve_legacy_compatible_u_value_v1(three_path)
    assert three_path_result.ready, three_path_result.blockers
    assert len(three_path_result.paths) == 3

    missing_films = replace(
        wall,
        internal_surface_resistance_m2K_W=None,
        external_surface_resistance_m2K_W=None,
    )
    missing_film_result = resolve_legacy_compatible_u_value_v1(missing_films)
    assert not missing_film_result.ready
    assert "explicit Rsi and Rse" in " ".join(missing_film_result.blockers)

    invalid_fraction = replace(
        wall,
        paths=(
            replace(wall.paths[0], area_fraction=0.50),
            replace(wall.paths[1], area_fraction=0.25),
        ),
    )
    invalid_result = resolve_legacy_compatible_u_value_v1(invalid_fraction)
    assert not invalid_result.ready
    assert "fractions total" in " ".join(invalid_result.blockers)

    non_finite_layer = replace(
        wall.layers[1],
        conductivity_W_mK=float("nan"),
    )
    non_finite_evidence = replace(
        wall,
        layers=(wall.layers[0], non_finite_layer, *wall.layers[2:]),
    )
    non_finite_result = resolve_legacy_compatible_u_value_v1(
        non_finite_evidence
    )
    assert not non_finite_result.ready
    assert "finite and positive" in " ".join(non_finite_result.blockers)

    print(
        "OK — U-S2 legacy series-path resistance and area-weighted parallel "
        "transmittance calculation passed."
    )


if __name__ == "__main__":
    main()
