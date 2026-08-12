from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    LegacyHeatFlowPathCalculationV1,
    resolve_legacy_compatible_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
    validate_shared_construction_layer_path_evidence_v1,
)


ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1 = (
    "iso_6946_2017_combined_upper_lower_limits_base_v1"
)
PLANE_THICKNESS_TOLERANCE_M = 1.0e-9


@dataclass(frozen=True, slots=True)
class Iso6946LayerPlaneComponentV1:
    path_id: str
    layer_id: str
    label: str
    area_fraction: float
    thickness_m: float | None
    resistance_m2K_W: float


@dataclass(frozen=True, slots=True)
class Iso6946LayerPlaneV1:
    plane_index: int
    common_layer: bool
    components: tuple[Iso6946LayerPlaneComponentV1, ...]
    equivalent_resistance_m2K_W: float


@dataclass(frozen=True, slots=True)
class Iso6946ThermalNetworkNodeV1:
    node_id: str
    label: str
    order: int


@dataclass(frozen=True, slots=True)
class Iso6946ThermalNetworkEdgeV1:
    edge_id: str
    from_node_id: str
    to_node_id: str
    kind: str
    label: str
    layer_id: str
    path_ids: tuple[str, ...]
    area_fraction: float
    resistance_m2K_W: float
    area_weighted_conductance_W_m2K: float


@dataclass(frozen=True, slots=True)
class Iso6946CombinedUValueResultV1:
    ready: bool
    construction_id: str = ""
    method: str = ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1
    straight_paths: tuple[LegacyHeatFlowPathCalculationV1, ...] = ()
    layer_planes: tuple[Iso6946LayerPlaneV1, ...] = ()
    network_nodes: tuple[Iso6946ThermalNetworkNodeV1, ...] = ()
    network_edges: tuple[Iso6946ThermalNetworkEdgeV1, ...] = ()
    upper_limit_resistance_m2K_W: float | None = None
    lower_limit_resistance_m2K_W: float | None = None
    combined_resistance_m2K_W: float | None = None
    uncorrected_u_value_W_m2K: float | None = None
    corrections_applied: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "ISO 6946 combined-limit calculation not resolved"


def resolve_iso_6946_combined_u_value_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
) -> Iso6946CombinedUValueResultV1:
    """Resolve the uncorrected ISO 6946 combined upper/lower-limit basis.

    The shared U-S1 evidence represents constant-area straight paths. For the
    lower limit, layers at the same ordinal position are treated as one
    physical layer plane. Inhomogeneous plane components must therefore carry
    equal positive nominal thickness; otherwise their alignment is ambiguous
    and the calculation blocks.

    Correction terms for air gaps, mechanical fasteners and inverted roofs are
    deliberately outside this base stage and are never implied to be applied.
    """

    validation = validate_shared_construction_layer_path_evidence_v1(evidence)
    if not validation.ready:
        return _blocked(evidence, validation.blockers, validation.warnings)

    straight_path_result = resolve_legacy_compatible_u_value_v1(evidence)
    if not straight_path_result.ready:
        return _blocked(
            evidence,
            straight_path_result.blockers,
            straight_path_result.warnings,
        )

    alignment_blockers = _alignment_blockers(evidence)
    if alignment_blockers:
        return _blocked(
            evidence,
            alignment_blockers,
            straight_path_result.warnings,
        )

    rsi = float(evidence.internal_surface_resistance_m2K_W)
    rse = float(evidence.external_surface_resistance_m2K_W)
    layers_by_id = evidence.layer_by_id()
    layer_planes: list[Iso6946LayerPlaneV1] = []

    active_path_layers = {
        path.path_id: evidence.active_path_layer_ids(path.path_id)
        for path in evidence.paths
    }
    plane_count = len(active_path_layers[evidence.paths[0].path_id])
    for plane_index in range(plane_count):
        components: list[Iso6946LayerPlaneComponentV1] = []
        conductance = 0.0
        plane_layer_ids: set[str] = set()
        for path in evidence.paths:
            layer_id = active_path_layers[path.path_id][plane_index]
            layer = layers_by_id[layer_id]
            resistance = float(layer.resolved_resistance_m2K_W())
            fraction = float(path.area_fraction)
            conductance += fraction / resistance
            plane_layer_ids.add(layer_id)
            components.append(
                Iso6946LayerPlaneComponentV1(
                    path_id=path.path_id,
                    layer_id=layer_id,
                    label=layer.label,
                    area_fraction=fraction,
                    thickness_m=(
                        None
                        if layer.thickness_m is None
                        else float(layer.thickness_m)
                    ),
                    resistance_m2K_W=resistance,
                )
            )
        if not math.isfinite(conductance) or conductance <= 0.0:
            return _blocked(
                evidence,
                (f"Layer plane {plane_index + 1} conductance is invalid",),
                straight_path_result.warnings,
            )
        layer_planes.append(
            Iso6946LayerPlaneV1(
                plane_index=plane_index,
                common_layer=len(plane_layer_ids) == 1,
                components=tuple(components),
                equivalent_resistance_m2K_W=1.0 / conductance,
            )
        )

    upper_limit = float(straight_path_result.effective_resistance_m2K_W)
    lower_limit = rsi + sum(
        plane.equivalent_resistance_m2K_W for plane in layer_planes
    ) + rse
    combined_resistance = (upper_limit + lower_limit) / 2.0
    if not math.isfinite(combined_resistance) or combined_resistance <= 0.0:
        return _blocked(
            evidence,
            ("ISO 6946 combined resistance must be finite and positive",),
            straight_path_result.warnings,
        )

    nodes, edges = _build_network(evidence, tuple(layer_planes), rsi, rse)
    warnings = tuple(straight_path_result.warnings) + (
        "ISO 6946 correction terms are not applied in this base result",
    )
    return Iso6946CombinedUValueResultV1(
        ready=True,
        construction_id=evidence.construction_id,
        straight_paths=straight_path_result.paths,
        layer_planes=tuple(layer_planes),
        network_nodes=nodes,
        network_edges=edges,
        upper_limit_resistance_m2K_W=upper_limit,
        lower_limit_resistance_m2K_W=lower_limit,
        combined_resistance_m2K_W=combined_resistance,
        uncorrected_u_value_W_m2K=1.0 / combined_resistance,
        corrections_applied=False,
        warnings=_unique(warnings),
        status=(
            "Ready — uncorrected ISO 6946 combined upper/lower-limit "
            "U-value resolved"
        ),
    )


def _alignment_blockers(
    evidence: SharedConstructionLayerPathEvidenceV1,
) -> tuple[str, ...]:
    blockers: list[str] = []
    active_path_layers = {
        path.path_id: evidence.active_path_layer_ids(path.path_id)
        for path in evidence.paths
    }
    path_lengths = {len(layer_ids) for layer_ids in active_path_layers.values()}
    if len(path_lengths) != 1:
        return (
            "ISO 6946 layer-plane alignment requires equal layer counts in "
            "every path",
        )

    shared_positions: dict[str, set[int]] = {
        layer_id: set()
        for layer_id in evidence.shared_layer_ids
        if evidence.layer_by_id()[layer_id].included
    }
    for path in evidence.paths:
        for position, layer_id in enumerate(active_path_layers[path.path_id]):
            if layer_id in shared_positions:
                shared_positions[layer_id].add(position)
    for layer_id, positions in shared_positions.items():
        if len(positions) != 1:
            blockers.append(
                f"Shared layer {layer_id} must occupy the same physical "
                "position in every path"
            )

    layers_by_id = evidence.layer_by_id()
    plane_count = next(iter(path_lengths), 0)
    for plane_index in range(plane_count):
        layer_ids = {
            active_path_layers[path.path_id][plane_index]
            for path in evidence.paths
        }
        if len(layer_ids) <= 1:
            continue
        thicknesses: list[float] = []
        for layer_id in layer_ids:
            thickness = layers_by_id[layer_id].thickness_m
            if thickness is None:
                blockers.append(
                    f"Inhomogeneous layer plane {plane_index + 1} requires "
                    f"nominal thickness for layer {layer_id}"
                )
                continue
            try:
                value = float(thickness)
            except (TypeError, ValueError):
                blockers.append(
                    f"Layer {layer_id} nominal thickness must be numeric"
                )
                continue
            if not math.isfinite(value) or value <= 0.0:
                blockers.append(
                    f"Layer {layer_id} nominal thickness must be finite and positive"
                )
                continue
            thicknesses.append(value)
        if len(thicknesses) == len(layer_ids) and (
            max(thicknesses) - min(thicknesses)
            > PLANE_THICKNESS_TOLERANCE_M
        ):
            blockers.append(
                f"Inhomogeneous layer plane {plane_index + 1} components "
                "must have equal nominal thickness"
            )
    return _unique(blockers)


def _build_network(
    evidence: SharedConstructionLayerPathEvidenceV1,
    planes: tuple[Iso6946LayerPlaneV1, ...],
    rsi: float,
    rse: float,
) -> tuple[
    tuple[Iso6946ThermalNetworkNodeV1, ...],
    tuple[Iso6946ThermalNetworkEdgeV1, ...],
]:
    nodes = [
        Iso6946ThermalNetworkNodeV1("inside-air", "Inside air", 0),
    ]
    nodes.extend(
        Iso6946ThermalNetworkNodeV1(
            f"interface-{index:03d}",
            f"Thermal interface {index}",
            index + 1,
        )
        for index in range(len(planes) + 1)
    )
    nodes.append(
        Iso6946ThermalNetworkNodeV1(
            "outside-air", "Outside air", len(planes) + 2
        )
    )

    edges: list[Iso6946ThermalNetworkEdgeV1] = [
        Iso6946ThermalNetworkEdgeV1(
            edge_id="surface-internal",
            from_node_id="inside-air",
            to_node_id="interface-000",
            kind="surface_resistance",
            label="Rsi",
            layer_id="",
            path_ids=tuple(path.path_id for path in evidence.paths),
            area_fraction=1.0,
            resistance_m2K_W=rsi,
            area_weighted_conductance_W_m2K=1.0 / rsi,
        )
    ]
    for plane in planes:
        grouped: dict[str, list[Iso6946LayerPlaneComponentV1]] = {}
        for component in plane.components:
            grouped.setdefault(component.layer_id, []).append(component)
        for layer_id, components in grouped.items():
            fraction = sum(item.area_fraction for item in components)
            resistance = components[0].resistance_m2K_W
            edges.append(
                Iso6946ThermalNetworkEdgeV1(
                    edge_id=f"plane-{plane.plane_index:03d}-{layer_id}",
                    from_node_id=f"interface-{plane.plane_index:03d}",
                    to_node_id=f"interface-{plane.plane_index + 1:03d}",
                    kind=(
                        "common_layer"
                        if plane.common_layer
                        else "parallel_layer_path"
                    ),
                    label=components[0].label,
                    layer_id=layer_id,
                    path_ids=tuple(item.path_id for item in components),
                    area_fraction=fraction,
                    resistance_m2K_W=resistance,
                    area_weighted_conductance_W_m2K=fraction / resistance,
                )
            )
    edges.append(
        Iso6946ThermalNetworkEdgeV1(
            edge_id="surface-external",
            from_node_id=f"interface-{len(planes):03d}",
            to_node_id="outside-air",
            kind="surface_resistance",
            label="Rse",
            layer_id="",
            path_ids=tuple(path.path_id for path in evidence.paths),
            area_fraction=1.0,
            resistance_m2K_W=rse,
            area_weighted_conductance_W_m2K=1.0 / rse,
        )
    )
    return tuple(nodes), tuple(edges)


def _blocked(
    evidence: SharedConstructionLayerPathEvidenceV1 | object,
    blockers: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> Iso6946CombinedUValueResultV1:
    return Iso6946CombinedUValueResultV1(
        ready=False,
        construction_id=str(getattr(evidence, "construction_id", "") or ""),
        blockers=_unique(blockers) or ("ISO 6946 calculation is blocked",),
        warnings=_unique(warnings),
        status="Blocked — ISO 6946 layer-path evidence is incomplete",
    )


def _unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))
