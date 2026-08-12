from __future__ import annotations

from dataclasses import replace

from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    resolve_legacy_compatible_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    HOMOGENEOUS_LAYER_BASIS,
    ConstructionHeatFlowPathEvidenceV1,
    ConstructionThermalLayerEvidenceV1,
    SharedConstructionLayerPathEvidenceV1,
)


def layer(layer_id: str, thickness: float, conductivity: float):
    return ConstructionThermalLayerEvidenceV1(
        layer_id=layer_id,
        label=layer_id.replace("-", " ").title(),
        basis=HOMOGENEOUS_LAYER_BASIS,
        thickness_m=thickness,
        conductivity_W_mK=conductivity,
        source_kind="calculation_input",
        source_ref="ISO 6946 test evidence",
    )


def main() -> None:
    wall = SharedConstructionLayerPathEvidenceV1(
        construction_id="iso-stud-wall-001",
        label="ISO insulated timber stud wall",
        element_kind="external_wall",
        layers=(
            layer("lining", 0.0125, 0.19),
            layer("insulation", 0.100, 0.035),
            layer("stud", 0.100, 0.13),
            layer("sheathing", 0.012, 0.13),
        ),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "bay", "Insulated bay", 0.85,
                ("lining", "insulation", "sheathing"),
            ),
            ConstructionHeatFlowPathEvidenceV1(
                "stud", "Timber stud", 0.15,
                ("lining", "stud", "sheathing"),
            ),
        ),
        shared_layer_ids=("lining", "sheathing"),
        internal_surface_resistance_m2K_W=0.13,
        external_surface_resistance_m2K_W=0.04,
        source_ref="ISO 6946 test evidence",
    )
    result = resolve_iso_6946_combined_u_value_v1(wall)
    assert result.ready, result.blockers
    assert result.method == ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1
    assert not result.corrections_applied
    assert "correction terms are not applied" in " ".join(result.warnings)

    legacy = resolve_legacy_compatible_u_value_v1(wall)
    assert legacy.ready
    expected_upper = legacy.effective_resistance_m2K_W
    lining_r = 0.0125 / 0.19
    middle_r = 1.0 / (0.85 / (0.100 / 0.035) + 0.15 / (0.100 / 0.13))
    sheathing_r = 0.012 / 0.13
    expected_lower = 0.13 + lining_r + middle_r + sheathing_r + 0.04
    expected_combined = (expected_upper + expected_lower) / 2.0
    assert abs(result.upper_limit_resistance_m2K_W - expected_upper) < 1.0e-12
    assert abs(result.lower_limit_resistance_m2K_W - expected_lower) < 1.0e-12
    assert abs(result.combined_resistance_m2K_W - expected_combined) < 1.0e-12
    assert abs(result.uncorrected_u_value_W_m2K - 1.0 / expected_combined) < 1.0e-12

    assert len(result.layer_planes) == 3
    assert result.layer_planes[0].common_layer
    assert not result.layer_planes[1].common_layer
    assert result.layer_planes[2].common_layer
    assert [node.node_id for node in result.network_nodes] == [
        "inside-air",
        "interface-000",
        "interface-001",
        "interface-002",
        "interface-003",
        "outside-air",
    ]
    assert len(result.network_edges) == 6
    middle_edges = [
        edge for edge in result.network_edges
        if edge.from_node_id == "interface-001"
        and edge.to_node_id == "interface-002"
    ]
    assert {edge.layer_id for edge in middle_edges} == {"insulation", "stud"}
    assert abs(sum(edge.area_fraction for edge in middle_edges) - 1.0) < 1.0e-12

    single = replace(
        wall,
        construction_id="iso-single-path-001",
        layers=(layer("solid", 0.215, 0.77),),
        paths=(
            ConstructionHeatFlowPathEvidenceV1(
                "solid", "Solid", 1.0, ("solid",)
            ),
        ),
        shared_layer_ids=("solid",),
    )
    single_result = resolve_iso_6946_combined_u_value_v1(single)
    single_legacy = resolve_legacy_compatible_u_value_v1(single)
    assert single_result.ready, single_result.blockers
    assert abs(
        single_result.upper_limit_resistance_m2K_W
        - single_result.lower_limit_resistance_m2K_W
    ) < 1.0e-12
    assert abs(
        single_result.uncorrected_u_value_W_m2K
        - single_legacy.u_value_W_m2K
    ) < 1.0e-12

    unequal_counts = replace(
        wall,
        paths=(wall.paths[0], replace(wall.paths[1], layer_ids=("lining", "stud"))),
        shared_layer_ids=("lining",),
    )
    unequal_result = resolve_iso_6946_combined_u_value_v1(unequal_counts)
    assert not unequal_result.ready
    assert "equal layer counts" in " ".join(unequal_result.blockers)

    misplaced_shared = replace(
        wall,
        paths=(
            wall.paths[0],
            replace(wall.paths[1], layer_ids=("stud", "lining", "sheathing")),
        ),
    )
    misplaced_result = resolve_iso_6946_combined_u_value_v1(misplaced_shared)
    assert not misplaced_result.ready
    assert "same physical position" in " ".join(misplaced_result.blockers)

    unequal_stud = replace(wall.layers[2], thickness_m=0.090)
    unequal_thickness = replace(
        wall,
        layers=(wall.layers[0], wall.layers[1], unequal_stud, wall.layers[3]),
    )
    thickness_result = resolve_iso_6946_combined_u_value_v1(unequal_thickness)
    assert not thickness_result.ready
    assert "equal nominal thickness" in " ".join(thickness_result.blockers)

    print(
        "OK — U-S3 ISO 6946 combined upper/lower-limit base calculation "
        "and graph-ready thermal network evidence passed."
    )


if __name__ == "__main__":
    main()
