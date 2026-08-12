from __future__ import annotations

from dataclasses import dataclass

from HVAC.constructions.physics.two_path_member_spacing_fraction_v1 import (
    DECLARED_EFFECTIVE_MEMBER_FRACTION,
    TwoPathMemberSpacingIntentV1,
    resolve_two_path_member_spacing_fraction_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    DECLARED_RESISTANCE_LAYER_BASIS,
    HOMOGENEOUS_LAYER_BASIS,
    HORIZONTAL_HEAT_FLOW,
    ConstructionHeatFlowPathEvidenceV1,
    ConstructionThermalLayerEvidenceV1,
    SharedConstructionLayerPathEvidenceV1,
)


ONE_PATH_MODEL_ID = "one_path_solid_wall"
CAVITY_WALL_MODEL_ID = "one_path_partial_fill_masonry_cavity_wall"
TWO_PATH_MODEL_ID = "two_path_timber_stud_wall"
THREE_PATH_MODEL_ID = "three_path_composite_panel"


@dataclass(frozen=True, slots=True)
class UValueTeachingModelV1:
    model_id: str
    label: str
    description: str
    evidence: SharedConstructionLayerPathEvidenceV1
    member_spacing_intent: TwoPathMemberSpacingIntentV1 | None = None


def build_u_value_teaching_models_v1() -> tuple[UValueTeachingModelV1, ...]:
    """Return practical candidate models for calculation and visual inspection."""

    stud_spacing_intent = TwoPathMemberSpacingIntentV1(
        member_path_id="timber-stud",
        clear_path_id="insulated-bay",
        member_label="Timber stud",
        member_width_m=0.038,
        member_centres_m=0.600,
        controlling_basis=DECLARED_EFFECTIVE_MEMBER_FRACTION,
        declared_effective_member_fraction=0.15,
        source_note=(
            "38 mm member at 600 mm centres; 15% declared effective framing "
            "fraction includes additional framing beyond repeating studs."
        ),
    )
    stud_fraction = resolve_two_path_member_spacing_fraction_v1(
        stud_spacing_intent
    )
    if not stud_fraction.ready:
        raise RuntimeError("; ".join(stud_fraction.blockers))

    return (
        UValueTeachingModelV1(
            model_id=ONE_PATH_MODEL_ID,
            label="One path — existing solid brick wall",
            description=(
                "Practical existing-wall geometry: 13 mm internal plaster "
                "and 215 mm solid brickwork with an exposed external brick "
                "face. No cavity, insulation or render. Thermal properties "
                "remain illustrative until a verified catalogue source is "
                "selected."
            ),
            evidence=SharedConstructionLayerPathEvidenceV1(
                construction_id="teaching-solid-wall-001",
                label="Existing 215 mm solid brick wall",
                element_kind="external_wall",
                heat_flow_direction=HORIZONTAL_HEAT_FLOW,
                layers=(
                    _layer(
                        "plaster",
                        "Internal plaster",
                        0.013,
                        0.57,
                        source_ref=(
                            "Illustrative teaching value — verified "
                            "catalogue source not yet selected"
                        ),
                        property_notes=(
                            "Practical layer geometry; thermal property "
                            "requires source selection."
                        ),
                    ),
                    _layer(
                        "masonry",
                        "Solid brickwork",
                        0.215,
                        0.77,
                        source_ref=(
                            "Illustrative teaching value — verified "
                            "catalogue source not yet selected"
                        ),
                        property_notes=(
                            "One-brick solid-wall thickness including "
                            "mortar joints; thermal property requires "
                            "source selection."
                        ),
                    ),
                ),
                paths=(
                    ConstructionHeatFlowPathEvidenceV1(
                        "solid-path",
                        "Uniform wall path",
                        1.0,
                        ("plaster", "masonry"),
                    ),
                ),
                shared_layer_ids=("plaster", "masonry"),
                internal_surface_resistance_m2K_W=0.13,
                external_surface_resistance_m2K_W=0.04,
                source_kind="teaching_model",
                source_ref=(
                    "HVACgooee U-S5D1 practical geometry; material "
                    "properties pending verified catalogue selection"
                ),
                source_version="v1-practical-geometry",
            ),
        ),
        UValueTeachingModelV1(
            model_id=CAVITY_WALL_MODEL_ID,
            label="One path — partial-fill masonry cavity wall",
            description=(
                "Practical configurable masonry wall: 13 mm internal plaster, "
                "100 mm block inner leaf, 100 mm insulation, 50 mm residual "
                "unventilated air cavity and 102.5 mm outer brick leaf. Every "
                "layer may be included or excluded and its geometry edited. "
                "Thermal properties and cavity resistance remain illustrative "
                "until verified catalogue and cavity authorities are selected."
            ),
            evidence=SharedConstructionLayerPathEvidenceV1(
                construction_id="teaching-masonry-cavity-wall-001",
                label="Partial-fill masonry cavity wall candidate",
                element_kind="external_wall",
                heat_flow_direction=HORIZONTAL_HEAT_FLOW,
                layers=(
                    _layer("cavity-plaster", "Internal plaster", 0.013, 0.57),
                    _layer("inner-leaf", "Blockwork inner leaf", 0.100, 0.51),
                    _layer("cavity-insulation", "Cavity insulation", 0.100, 0.022),
                    _declared_layer(
                        "residual-air-cavity",
                        "Residual unventilated air cavity",
                        0.050,
                        0.18,
                    ),
                    _layer("outer-leaf", "Outer brick leaf", 0.1025, 0.77),
                ),
                paths=(
                    ConstructionHeatFlowPathEvidenceV1(
                        "masonry-cavity-path",
                        "Masonry cavity wall path",
                        1.0,
                        (
                            "cavity-plaster",
                            "inner-leaf",
                            "cavity-insulation",
                            "residual-air-cavity",
                            "outer-leaf",
                        ),
                    ),
                ),
                shared_layer_ids=(
                    "cavity-plaster",
                    "inner-leaf",
                    "cavity-insulation",
                    "residual-air-cavity",
                    "outer-leaf",
                ),
                internal_surface_resistance_m2K_W=0.13,
                external_surface_resistance_m2K_W=0.04,
                source_kind="teaching_model",
                source_ref="HVACgooee U-S5D1D practical masonry cavity wall",
                source_version="v1 illustrative",
            ),
        ),
        UValueTeachingModelV1(
            model_id=TWO_PATH_MODEL_ID,
            label="Two paths — insulation and timber stud",
            description=(
                "Common linings split into insulation and timber paths, "
                "then rejoin."
            ),
            evidence=SharedConstructionLayerPathEvidenceV1(
                construction_id="teaching-stud-wall-001",
                label="Insulated timber stud wall",
                element_kind="external_wall",
                heat_flow_direction=HORIZONTAL_HEAT_FLOW,
                layers=(
                    _layer("lining", "Plasterboard lining", 0.0125, 0.19),
                    _layer("insulation", "Mineral wool", 0.100, 0.035),
                    _layer("stud", "Timber stud", 0.100, 0.13),
                    _layer("sheathing", "Sheathing", 0.012, 0.13),
                ),
                paths=(
                    ConstructionHeatFlowPathEvidenceV1(
                        "insulated-bay",
                        "Insulated bay",
                        stud_fraction.controlling_clear_fraction,
                        ("lining", "insulation", "sheathing"),
                    ),
                    ConstructionHeatFlowPathEvidenceV1(
                        "timber-stud",
                        "Timber stud",
                        stud_fraction.controlling_member_fraction,
                        ("lining", "stud", "sheathing"),
                    ),
                ),
                shared_layer_ids=("lining", "sheathing"),
                internal_surface_resistance_m2K_W=0.13,
                external_surface_resistance_m2K_W=0.04,
                source_kind="teaching_model",
                source_ref="HVACgooee U-S5D3 practical timber framing candidate",
                source_version="v1 member-spacing basis",
            ),
            member_spacing_intent=stud_spacing_intent,
        ),
        UValueTeachingModelV1(
            model_id=THREE_PATH_MODEL_ID,
            label="Three paths — composite panel",
            description=(
                "Two core regions and one structural web between common faces."
            ),
            evidence=SharedConstructionLayerPathEvidenceV1(
                construction_id="teaching-composite-panel-001",
                label="Three-path composite panel",
                element_kind="wall_panel",
                heat_flow_direction=HORIZONTAL_HEAT_FLOW,
                layers=(
                    _layer("inner-face", "Inner face", 0.008, 0.20),
                    _layer("core-a", "Core zone A", 0.080, 0.024),
                    _layer("core-b", "Core zone B", 0.080, 0.060),
                    _layer("web", "Structural web", 0.080, 0.50),
                    _layer("outer-face", "Outer face", 0.008, 0.20),
                ),
                paths=(
                    ConstructionHeatFlowPathEvidenceV1(
                        "core-a-path",
                        "Core A",
                        0.60,
                        ("inner-face", "core-a", "outer-face"),
                    ),
                    ConstructionHeatFlowPathEvidenceV1(
                        "core-b-path",
                        "Core B",
                        0.30,
                        ("inner-face", "core-b", "outer-face"),
                    ),
                    ConstructionHeatFlowPathEvidenceV1(
                        "web-path",
                        "Structural web",
                        0.10,
                        ("inner-face", "web", "outer-face"),
                    ),
                ),
                shared_layer_ids=("inner-face", "outer-face"),
                internal_surface_resistance_m2K_W=0.13,
                external_surface_resistance_m2K_W=0.04,
                source_kind="teaching_model",
                source_ref="HVACgooee U-S5 three-path teaching model",
                source_version="v1",
            ),
        ),
    )


def teaching_model_by_id_v1(model_id: str) -> UValueTeachingModelV1:
    wanted = str(model_id or "")
    for model in build_u_value_teaching_models_v1():
        if model.model_id == wanted:
            return model
    raise KeyError(f"Unknown U-value teaching model: {model_id}")


def _layer(
    layer_id: str,
    label: str,
    thickness_m: float,
    conductivity_W_mK: float,
    *,
    source_ref: str = "HVACgooee U-S5 teaching material",
    property_notes: str = "",
) -> ConstructionThermalLayerEvidenceV1:
    return ConstructionThermalLayerEvidenceV1(
        layer_id=layer_id,
        label=label,
        basis=HOMOGENEOUS_LAYER_BASIS,
        thickness_m=thickness_m,
        conductivity_W_mK=conductivity_W_mK,
        source_kind="teaching_model",
        source_ref=source_ref,
        source_version="v1",
        property_notes=property_notes,
    )

def _declared_layer(
    layer_id: str,
    label: str,
    thickness_m: float,
    declared_resistance_m2K_W: float,
) -> ConstructionThermalLayerEvidenceV1:
    return ConstructionThermalLayerEvidenceV1(
        layer_id=layer_id,
        label=label,
        basis=DECLARED_RESISTANCE_LAYER_BASIS,
        thickness_m=thickness_m,
        declared_resistance_m2K_W=declared_resistance_m2K_W,
        source_kind="teaching_model",
        source_ref="Illustrative unventilated cavity resistance pending audit",
        source_version="U-S5D1D v1 illustrative",
        property_notes=(
            "Air cavity uses declared resistance authority; conductivity is "
            "not applicable."
        ),
    )

