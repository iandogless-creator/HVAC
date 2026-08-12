from __future__ import annotations

from dataclasses import dataclass, replace

from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    DECLARED_RESISTANCE_LAYER_BASIS,
    HOMOGENEOUS_LAYER_BASIS,
    ConstructionHeatFlowPathEvidenceV1,
    SharedConstructionLayerPathEvidenceV1,
    validate_shared_construction_layer_path_evidence_v1,
)


@dataclass(frozen=True, slots=True)
class StagedConstructionLayerV1:
    layer_id: str
    source_path_id: str
    shared_layer: bool
    shared_layer_index: int = -1


@dataclass(frozen=True, slots=True)
class ConstructionLayerCandidateEditV1:
    operation_ready: bool
    evidence: SharedConstructionLayerPathEvidenceV1 | None = None
    staged_layer: StagedConstructionLayerV1 | None = None
    candidate_valid: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Construction layer candidate not changed"


def update_construction_layer_properties_candidate_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    *,
    layer_id: str,
    label: str,
    basis: str,
    thickness_m: float | None,
    conductivity_W_mK: float | None,
    declared_resistance_m2K_W: float | None,
    included: bool = True,
    density_kg_m3: float | None = None,
    specific_heat_capacity_J_kgK: float | None = None,
    vapour_resistivity_MNs_gm: float | None = None,
    surface_emissivity: float | None = None,
    solar_absorptivity: float | None = None,
    material_direction: str = "unspecified",
    property_temperature_C: float | None = None,
    moisture_condition: str = "",
    source_kind: str = "",
    source_ref: str = "",
    source_version: str = "",
    property_notes: str = "",
) -> ConstructionLayerCandidateEditV1:
    """Replace one exact layer's candidate properties without project mutation."""

    wanted = str(layer_id or "")
    layer_map = evidence.layer_by_id()
    if wanted not in layer_map:
        return _blocked("Exact focused construction layer is required")
    basis = str(basis or "")
    if basis not in {
        HOMOGENEOUS_LAYER_BASIS,
        DECLARED_RESISTANCE_LAYER_BASIS,
    }:
        return _blocked("Recognised layer resistance basis is required")
    replacement = replace(
        layer_map[wanted],
        label=str(label or "").strip(),
        basis=basis,
        included=bool(included),
        thickness_m=_optional_number(thickness_m),
        conductivity_W_mK=(
            _optional_number(conductivity_W_mK)
            if basis == HOMOGENEOUS_LAYER_BASIS
            else None
        ),
        declared_resistance_m2K_W=(
            _optional_number(declared_resistance_m2K_W)
            if basis == DECLARED_RESISTANCE_LAYER_BASIS
            else None
        ),
        density_kg_m3=_optional_number(density_kg_m3),
        specific_heat_capacity_J_kgK=_optional_number(
            specific_heat_capacity_J_kgK
        ),
        vapour_resistivity_MNs_gm=_optional_number(
            vapour_resistivity_MNs_gm
        ),
        surface_emissivity=_optional_number(surface_emissivity),
        solar_absorptivity=_optional_number(solar_absorptivity),
        material_direction=str(material_direction or "unspecified"),
        property_temperature_C=_optional_number(property_temperature_C),
        moisture_condition=str(moisture_condition or "").strip(),
        source_kind=str(source_kind or "").strip(),
        source_ref=str(source_ref or "").strip(),
        source_version=str(source_version or "").strip(),
        property_notes=str(property_notes or "").strip(),
    )
    updated = replace(
        evidence,
        layers=tuple(
            replacement if layer.layer_id == wanted else layer
            for layer in evidence.layers
        ),
    )
    return _completed(updated, "Focused layer properties updated")


def update_construction_path_properties_candidate_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    *,
    path_id: str,
    label: str,
    area_fraction: float,
) -> ConstructionLayerCandidateEditV1:
    """Replace one exact path label/fraction; validation reports the total."""

    wanted = str(path_id or "")
    path_map = {path.path_id: path for path in evidence.paths}
    if wanted not in path_map:
        return _blocked("Exact focused construction path is required")
    try:
        fraction = float(area_fraction)
    except (TypeError, ValueError):
        return _blocked("Focused path area fraction must be numeric")
    replacement = replace(
        path_map[wanted],
        label=str(label or "").strip(),
        area_fraction=fraction,
    )
    updated = replace(
        evidence,
        paths=tuple(
            replacement if path.path_id == wanted else path
            for path in evidence.paths
        ),
    )
    return _completed(updated, "Focused path properties updated")


def move_construction_layer_candidate_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    *,
    layer_id: str,
    source_path_id: str,
    target_path_id: str,
    target_index: int,
) -> ConstructionLayerCandidateEditV1:
    layer_id = str(layer_id or "")
    source_path_id = str(source_path_id or "")
    target_path_id = str(target_path_id or "")
    target_index = _integer_index(target_index)
    path_map = {path.path_id: path for path in evidence.paths}
    if source_path_id not in path_map or target_path_id not in path_map:
        return _blocked("Exact source and target paths are required")
    if layer_id not in path_map[source_path_id].layer_ids:
        return _blocked("Dragged layer is not present in its source path")

    shared = layer_id in evidence.shared_layer_ids
    if not shared and source_path_id != target_path_id:
        return _blocked(
            "A path-only layer can only be reordered within its existing path"
        )

    if shared:
        stripped = [
            tuple(item for item in path.layer_ids if item != layer_id)
            for path in evidence.paths
        ]
        if any(layer_id not in path.layer_ids for path in evidence.paths):
            return _blocked("Shared layer must exist in every path before moving")
        if target_index < 0 or any(target_index > len(items) for items in stripped):
            return _blocked("Shared-layer target position is outside a path")
        new_paths = tuple(
            replace(
                path,
                layer_ids=(
                    items[:target_index]
                    + (layer_id,)
                    + items[target_index:]
                ),
            )
            for path, items in zip(evidence.paths, stripped)
        )
    else:
        source = path_map[source_path_id]
        stripped = tuple(item for item in source.layer_ids if item != layer_id)
        if target_index < 0 or target_index > len(stripped):
            return _blocked("Layer target position is outside its path")
        replacement = replace(
            source,
            layer_ids=(
                stripped[:target_index]
                + (layer_id,)
                + stripped[target_index:]
            ),
        )
        new_paths = tuple(
            replacement if path.path_id == source_path_id else path
            for path in evidence.paths
        )
    return _completed(
        replace(evidence, paths=new_paths),
        "Layer-order candidate updated",
    )


def stage_construction_layer_candidate_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    *,
    layer_id: str,
    source_path_id: str,
) -> ConstructionLayerCandidateEditV1:
    layer_id = str(layer_id or "")
    source_path_id = str(source_path_id or "")
    path_map = {path.path_id: path for path in evidence.paths}
    if source_path_id not in path_map:
        return _blocked("Exact source path is required")
    if layer_id not in path_map[source_path_id].layer_ids:
        return _blocked("Dragged layer is not present in its source path")

    shared = layer_id in evidence.shared_layer_ids
    if shared:
        new_paths = tuple(
            replace(
                path,
                layer_ids=tuple(
                    item for item in path.layer_ids if item != layer_id
                ),
            )
            for path in evidence.paths
        )
        shared_ids = tuple(
            item for item in evidence.shared_layer_ids if item != layer_id
        )
    else:
        new_paths = tuple(
            replace(
                path,
                layer_ids=tuple(
                    item for item in path.layer_ids if item != layer_id
                ),
            )
            if path.path_id == source_path_id
            else path
            for path in evidence.paths
        )
        shared_ids = evidence.shared_layer_ids
    staged = StagedConstructionLayerV1(
        layer_id=layer_id,
        source_path_id=source_path_id,
        shared_layer=shared,
        shared_layer_index=(
            evidence.shared_layer_ids.index(layer_id) if shared else -1
        ),
    )
    return _completed(
        replace(evidence, paths=new_paths, shared_layer_ids=shared_ids),
        "Layer moved to candidate staging",
        staged_layer=staged,
    )


def restore_staged_construction_layer_candidate_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    staged_layer: StagedConstructionLayerV1,
    *,
    target_path_id: str,
    target_index: int,
) -> ConstructionLayerCandidateEditV1:
    target_path_id = str(target_path_id or "")
    target_index = _integer_index(target_index)
    if not isinstance(staged_layer, StagedConstructionLayerV1):
        return _blocked("Recognised staged construction layer is required")
    if staged_layer.layer_id not in evidence.layer_by_id():
        return _blocked("Staged layer no longer exists in construction evidence")
    path_map = {path.path_id: path for path in evidence.paths}
    if target_path_id not in path_map:
        return _blocked("Exact target path is required")
    if any(staged_layer.layer_id in path.layer_ids for path in evidence.paths):
        return _blocked("Staged layer is already present in a construction path")

    if staged_layer.shared_layer:
        if target_index < 0 or any(
            target_index > len(path.layer_ids) for path in evidence.paths
        ):
            return _blocked("Shared-layer target position is outside a path")
        new_paths = tuple(
            replace(
                path,
                layer_ids=(
                    path.layer_ids[:target_index]
                    + (staged_layer.layer_id,)
                    + path.layer_ids[target_index:]
                ),
            )
            for path in evidence.paths
        )
        shared_index = staged_layer.shared_layer_index
        if shared_index < 0 or shared_index > len(evidence.shared_layer_ids):
            return _blocked("Staged shared-layer identity order is invalid")
        shared_ids = (
            evidence.shared_layer_ids[:shared_index]
            + (staged_layer.layer_id,)
            + evidence.shared_layer_ids[shared_index:]
        )
    else:
        if target_path_id != staged_layer.source_path_id:
            return _blocked(
                "A staged path-only layer must return to its original path"
            )
        target = path_map[target_path_id]
        if target_index < 0 or target_index > len(target.layer_ids):
            return _blocked("Layer target position is outside its path")
        replacement = replace(
            target,
            layer_ids=(
                target.layer_ids[:target_index]
                + (staged_layer.layer_id,)
                + target.layer_ids[target_index:]
            ),
        )
        new_paths = tuple(
            replacement if path.path_id == target_path_id else path
            for path in evidence.paths
        )
        shared_ids = evidence.shared_layer_ids
    return _completed(
        replace(evidence, paths=new_paths, shared_layer_ids=shared_ids),
        "Staged layer restored to candidate",
    )


def _completed(
    evidence: SharedConstructionLayerPathEvidenceV1,
    status: str,
    *,
    staged_layer: StagedConstructionLayerV1 | None = None,
) -> ConstructionLayerCandidateEditV1:
    validation = validate_shared_construction_layer_path_evidence_v1(evidence)
    return ConstructionLayerCandidateEditV1(
        operation_ready=True,
        evidence=evidence,
        staged_layer=staged_layer,
        candidate_valid=validation.ready,
        blockers=validation.blockers,
        warnings=validation.warnings,
        status=status,
    )


def _blocked(*blockers: str) -> ConstructionLayerCandidateEditV1:
    return ConstructionLayerCandidateEditV1(
        operation_ready=False,
        blockers=tuple(blockers),
        status="Construction layer candidate edit blocked",
    )


def _integer_index(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _optional_number(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
