from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


SHARED_CONSTRUCTION_LAYER_PATH_SCHEMA_V1 = (
    "shared_construction_layer_path_evidence_v1"
)
HOMOGENEOUS_LAYER_BASIS = "homogeneous_layer"
DECLARED_RESISTANCE_LAYER_BASIS = "declared_resistance"

UNSPECIFIED_MATERIAL_DIRECTION = "unspecified"
ISOTROPIC_MATERIAL_DIRECTION = "isotropic"
PARALLEL_MATERIAL_DIRECTION = "parallel_to_grain_or_structure"
PERPENDICULAR_MATERIAL_DIRECTION = "perpendicular_to_grain_or_structure"
MATERIAL_DIRECTIONS = frozenset(
    {
        UNSPECIFIED_MATERIAL_DIRECTION,
        ISOTROPIC_MATERIAL_DIRECTION,
        PARALLEL_MATERIAL_DIRECTION,
        PERPENDICULAR_MATERIAL_DIRECTION,
    }
)

UNSPECIFIED_HEAT_FLOW = "unspecified"
HORIZONTAL_HEAT_FLOW = "horizontal"
UPWARD_HEAT_FLOW = "upward"
DOWNWARD_HEAT_FLOW = "downward"
HEAT_FLOW_DIRECTIONS = frozenset(
    {
        UNSPECIFIED_HEAT_FLOW,
        HORIZONTAL_HEAT_FLOW,
        UPWARD_HEAT_FLOW,
        DOWNWARD_HEAT_FLOW,
    }
)

PATH_FRACTION_TOLERANCE = 1.0e-6


@dataclass(frozen=True, slots=True)
class ConstructionThermalLayerEvidenceV1:
    """One homogeneous layer or one externally declared resistance."""

    layer_id: str
    label: str
    basis: str
    included: bool = True
    thickness_m: float | None = None
    conductivity_W_mK: float | None = None
    declared_resistance_m2K_W: float | None = None
    source_kind: str = ""
    source_ref: str = ""
    source_version: str = ""
    density_kg_m3: float | None = None
    specific_heat_capacity_J_kgK: float | None = None
    vapour_resistivity_MNs_gm: float | None = None
    surface_emissivity: float | None = None
    solar_absorptivity: float | None = None
    material_direction: str = UNSPECIFIED_MATERIAL_DIRECTION
    property_temperature_C: float | None = None
    moisture_condition: str = ""
    property_notes: str = ""

    def resolved_resistance_m2K_W(self) -> float:
        if self.basis == HOMOGENEOUS_LAYER_BASIS:
            if self.thickness_m is None or float(self.thickness_m) <= 0.0:
                raise ValueError(
                    f"Layer {self.layer_id} requires positive thickness"
                )
            if (
                self.conductivity_W_mK is None
                or float(self.conductivity_W_mK) <= 0.0
            ):
                raise ValueError(
                    f"Layer {self.layer_id} requires positive conductivity"
                )
            if self.declared_resistance_m2K_W is not None:
                raise ValueError(
                    f"Layer {self.layer_id} mixes calculated and declared "
                    "resistance authority"
                )
            return float(self.thickness_m) / float(self.conductivity_W_mK)

        if self.basis == DECLARED_RESISTANCE_LAYER_BASIS:
            if (
                self.declared_resistance_m2K_W is None
                or float(self.declared_resistance_m2K_W) <= 0.0
            ):
                raise ValueError(
                    f"Layer {self.layer_id} requires positive declared "
                    "resistance"
                )
            if self.conductivity_W_mK is not None:
                raise ValueError(
                    f"Layer {self.layer_id} mixes declared resistance and "
                    "conductivity authority"
                )
            if self.thickness_m is not None and float(self.thickness_m) <= 0.0:
                raise ValueError(
                    f"Layer {self.layer_id} has invalid nominal thickness"
                )
            return float(self.declared_resistance_m2K_W)

        raise ValueError(
            f"Layer {self.layer_id} has unknown resistance basis: {self.basis}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "label": self.label,
            "basis": self.basis,
            "included": self.included,
            "thickness_m": self.thickness_m,
            "conductivity_W_mK": self.conductivity_W_mK,
            "declared_resistance_m2K_W": self.declared_resistance_m2K_W,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "source_version": self.source_version,
            "density_kg_m3": self.density_kg_m3,
            "specific_heat_capacity_J_kgK": (
                self.specific_heat_capacity_J_kgK
            ),
            "vapour_resistivity_MNs_gm": self.vapour_resistivity_MNs_gm,
            "surface_emissivity": self.surface_emissivity,
            "solar_absorptivity": self.solar_absorptivity,
            "material_direction": self.material_direction,
            "property_temperature_C": self.property_temperature_C,
            "moisture_condition": self.moisture_condition,
            "property_notes": self.property_notes,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ConstructionThermalLayerEvidenceV1":
        return cls(
            layer_id=str(data.get("layer_id") or ""),
            label=str(data.get("label") or ""),
            basis=str(data.get("basis") or ""),
            included=bool(data.get("included", True)),
            thickness_m=_optional_float(data.get("thickness_m")),
            conductivity_W_mK=_optional_float(
                data.get("conductivity_W_mK")
            ),
            declared_resistance_m2K_W=_optional_float(
                data.get("declared_resistance_m2K_W")
            ),
            source_kind=str(data.get("source_kind") or ""),
            source_ref=str(data.get("source_ref") or ""),
            source_version=str(data.get("source_version") or ""),
            density_kg_m3=_optional_float(data.get("density_kg_m3")),
            specific_heat_capacity_J_kgK=_optional_float(
                data.get("specific_heat_capacity_J_kgK")
            ),
            vapour_resistivity_MNs_gm=_optional_float(
                data.get("vapour_resistivity_MNs_gm")
            ),
            surface_emissivity=_optional_float(
                data.get("surface_emissivity")
            ),
            solar_absorptivity=_optional_float(
                data.get("solar_absorptivity")
            ),
            material_direction=str(
                data.get("material_direction")
                or UNSPECIFIED_MATERIAL_DIRECTION
            ),
            property_temperature_C=_optional_float(
                data.get("property_temperature_C")
            ),
            moisture_condition=str(data.get("moisture_condition") or ""),
            property_notes=str(data.get("property_notes") or ""),
        )


@dataclass(frozen=True, slots=True)
class ConstructionHeatFlowPathEvidenceV1:
    """One explicit parallel heat-flow path and its area fraction."""

    path_id: str
    label: str
    area_fraction: float
    layer_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "label": self.label,
            "area_fraction": self.area_fraction,
            "layer_ids": list(self.layer_ids),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ConstructionHeatFlowPathEvidenceV1":
        return cls(
            path_id=str(data.get("path_id") or ""),
            label=str(data.get("label") or ""),
            area_fraction=float(data.get("area_fraction") or 0.0),
            layer_ids=tuple(
                str(value) for value in (data.get("layer_ids") or ())
            ),
        )


@dataclass(frozen=True, slots=True)
class SharedConstructionLayerPathEvidenceV1:
    """Method-neutral construction evidence for later U-value engines."""

    construction_id: str
    label: str
    element_kind: str
    layers: tuple[ConstructionThermalLayerEvidenceV1, ...]
    paths: tuple[ConstructionHeatFlowPathEvidenceV1, ...]
    shared_layer_ids: tuple[str, ...] = ()
    heat_flow_direction: str = UNSPECIFIED_HEAT_FLOW
    internal_surface_resistance_m2K_W: float | None = None
    external_surface_resistance_m2K_W: float | None = None
    source_kind: str = ""
    source_ref: str = ""
    source_version: str = ""
    schema: str = SHARED_CONSTRUCTION_LAYER_PATH_SCHEMA_V1

    def layer_by_id(self) -> dict[str, ConstructionThermalLayerEvidenceV1]:
        return {layer.layer_id: layer for layer in self.layers}

    def complete_path_layer_ids(self, path_id: str) -> tuple[str, ...]:
        path = next(
            (item for item in self.paths if item.path_id == str(path_id or "")),
            None,
        )
        if path is None:
            raise KeyError(f"Unknown construction heat-flow path: {path_id}")
        return tuple(path.layer_ids)

    def active_path_layer_ids(self, path_id: str) -> tuple[str, ...]:
        """Return included layers without erasing excluded candidate data."""

        layers = self.layer_by_id()
        return tuple(
            layer_id
            for layer_id in self.complete_path_layer_ids(path_id)
            if layers[layer_id].included
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "construction_id": self.construction_id,
            "label": self.label,
            "element_kind": self.element_kind,
            "layers": [layer.to_dict() for layer in self.layers],
            "paths": [path.to_dict() for path in self.paths],
            "shared_layer_ids": list(self.shared_layer_ids),
            "heat_flow_direction": self.heat_flow_direction,
            "internal_surface_resistance_m2K_W": (
                self.internal_surface_resistance_m2K_W
            ),
            "external_surface_resistance_m2K_W": (
                self.external_surface_resistance_m2K_W
            ),
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "source_version": self.source_version,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "SharedConstructionLayerPathEvidenceV1":
        return cls(
            schema=str(data.get("schema") or ""),
            construction_id=str(data.get("construction_id") or ""),
            label=str(data.get("label") or ""),
            element_kind=str(data.get("element_kind") or ""),
            layers=tuple(
                ConstructionThermalLayerEvidenceV1.from_dict(item)
                for item in (data.get("layers") or ())
                if isinstance(item, dict)
            ),
            paths=tuple(
                ConstructionHeatFlowPathEvidenceV1.from_dict(item)
                for item in (data.get("paths") or ())
                if isinstance(item, dict)
            ),
            shared_layer_ids=tuple(
                str(value) for value in (data.get("shared_layer_ids") or ())
            ),
            heat_flow_direction=str(
                data.get("heat_flow_direction") or UNSPECIFIED_HEAT_FLOW
            ),
            internal_surface_resistance_m2K_W=_optional_float(
                data.get("internal_surface_resistance_m2K_W")
            ),
            external_surface_resistance_m2K_W=_optional_float(
                data.get("external_surface_resistance_m2K_W")
            ),
            source_kind=str(data.get("source_kind") or ""),
            source_ref=str(data.get("source_ref") or ""),
            source_version=str(data.get("source_version") or ""),
        )


@dataclass(frozen=True, slots=True)
class SharedConstructionEvidenceValidationV1:
    ready: bool
    evidence: SharedConstructionLayerPathEvidenceV1 | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Shared construction evidence not validated"


def validate_shared_construction_layer_path_evidence_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
) -> SharedConstructionEvidenceValidationV1:
    """Validate identity, resistance bases and arbitrary N-path fractions."""

    if not isinstance(evidence, SharedConstructionLayerPathEvidenceV1):
        return _blocked("SharedConstructionLayerPathEvidenceV1 is required")

    blockers: list[str] = []
    warnings: list[str] = []
    if evidence.schema != SHARED_CONSTRUCTION_LAYER_PATH_SCHEMA_V1:
        blockers.append(f"Unsupported construction evidence schema: {evidence.schema}")
    if not str(evidence.construction_id or "").strip():
        blockers.append("Stable construction identity is required")
    if not str(evidence.label or "").strip():
        blockers.append("Construction label is required")
    if not str(evidence.element_kind or "").strip():
        blockers.append("Construction element kind is required")
    if evidence.heat_flow_direction not in HEAT_FLOW_DIRECTIONS:
        blockers.append(
            f"Unknown heat-flow direction: {evidence.heat_flow_direction}"
        )

    layer_ids = [str(layer.layer_id or "").strip() for layer in evidence.layers]
    if not layer_ids:
        blockers.append("At least one thermal layer is required")
    blockers.extend(_identity_blockers(layer_ids, "layer"))
    for layer in evidence.layers:
        if not str(layer.label or "").strip():
            blockers.append(f"Layer {layer.layer_id or '—'} requires a label")
        if layer.included:
            try:
                layer.resolved_resistance_m2K_W()
            except (TypeError, ValueError) as exc:
                blockers.append(str(exc))
        if layer.material_direction not in MATERIAL_DIRECTIONS:
            blockers.append(
                f"Layer {layer.layer_id} has unknown material direction: "
                f"{layer.material_direction}"
            )
        for property_name, value in (
            ("density", layer.density_kg_m3),
            ("specific heat capacity", layer.specific_heat_capacity_J_kgK),
            ("vapour resistivity", layer.vapour_resistivity_MNs_gm),
        ):
            if value is not None and (
                not math.isfinite(float(value)) or float(value) <= 0.0
            ):
                blockers.append(
                    f"Layer {layer.layer_id} {property_name} must be positive"
                )
        for property_name, value in (
            ("surface emissivity", layer.surface_emissivity),
            ("solar absorptivity", layer.solar_absorptivity),
        ):
            if value is not None and (
                not math.isfinite(float(value))
                or float(value) < 0.0
                or float(value) > 1.0
            ):
                blockers.append(
                    f"Layer {layer.layer_id} {property_name} must be between "
                    "0 and 1"
                )
        if layer.property_temperature_C is not None and not math.isfinite(
            float(layer.property_temperature_C)
        ):
            blockers.append(
                f"Layer {layer.layer_id} property temperature must be finite"
            )

    path_ids = [str(path.path_id or "").strip() for path in evidence.paths]
    if not path_ids:
        blockers.append("At least one heat-flow path is required")
    blockers.extend(_identity_blockers(path_ids, "path"))

    known_layer_ids = set(layer_ids)
    shared_layer_ids = tuple(
        str(layer_id or "").strip() for layer_id in evidence.shared_layer_ids
    )
    blockers.extend(_reference_blockers(shared_layer_ids, known_layer_ids, "shared"))
    blockers.extend(_duplicate_reference_blockers(shared_layer_ids, "shared layer"))

    referenced_layer_ids = set(shared_layer_ids)
    fraction_sum = 0.0
    for path in evidence.paths:
        if not str(path.label or "").strip():
            blockers.append(f"Path {path.path_id or '—'} requires a label")
        try:
            fraction = float(path.area_fraction)
        except (TypeError, ValueError):
            fraction = 0.0
            blockers.append(
                f"Path {path.path_id or '—'} area fraction must be numeric"
            )
        if not math.isfinite(fraction):
            blockers.append(
                f"Path {path.path_id or '—'} area fraction must be finite"
            )
        elif fraction <= 0.0 or fraction > 1.0:
            blockers.append(
                f"Path {path.path_id or '—'} area fraction must be > 0 and <= 1"
            )
        if math.isfinite(fraction):
            fraction_sum += fraction
        path_layer_ids = tuple(
            str(layer_id or "").strip() for layer_id in path.layer_ids
        )
        blockers.extend(
            _reference_blockers(path_layer_ids, known_layer_ids, f"path {path.path_id}")
        )
        blockers.extend(
            _duplicate_reference_blockers(path_layer_ids, f"path {path.path_id} layer")
        )
        missing_shared = set(shared_layer_ids).difference(path_layer_ids)
        if missing_shared:
            blockers.append(
                f"Path {path.path_id} omits shared layer(s): "
                + ", ".join(sorted(missing_shared))
            )
        if not path_layer_ids:
            blockers.append(f"Path {path.path_id} has no thermal layers")
        elif not any(
            layer_id in known_layer_ids
            and evidence.layer_by_id()[layer_id].included
            for layer_id in path_layer_ids
        ):
            blockers.append(f"Path {path.path_id} has no included thermal layers")
        referenced_layer_ids.update(path_layer_ids)

    if evidence.paths and abs(fraction_sum - 1.0) > PATH_FRACTION_TOLERANCE:
        blockers.append(
            f"Heat-flow path fractions total {fraction_sum:.9f}; required 1.0 "
            f"± {PATH_FRACTION_TOLERANCE:g}"
        )

    for name, value in (
        ("internal", evidence.internal_surface_resistance_m2K_W),
        ("external", evidence.external_surface_resistance_m2K_W),
    ):
        if value is None:
            continue
        try:
            resistance = float(value)
        except (TypeError, ValueError):
            blockers.append(
                f"Explicit {name} surface resistance must be numeric"
            )
            continue
        if not math.isfinite(resistance) or resistance <= 0.0:
            blockers.append(f"Explicit {name} surface resistance must be positive")
    if (
        evidence.internal_surface_resistance_m2K_W is None
    ) != (evidence.external_surface_resistance_m2K_W is None):
        blockers.append(
            "Explicit internal and external surface resistances must be "
            "provided together"
        )

    unused = known_layer_ids.difference(referenced_layer_ids)
    if unused:
        warnings.append(
            "Unreferenced thermal layer(s): " + ", ".join(sorted(unused))
        )
    excluded = sorted(layer.layer_id for layer in evidence.layers if not layer.included)
    if excluded:
        warnings.append(
            "Excluded candidate layer(s) omitted from calculation: "
            + ", ".join(excluded)
        )
    if not evidence.source_ref:
        warnings.append("Construction evidence source reference is not set")

    if blockers:
        return _blocked(*blockers, warnings=warnings)
    return SharedConstructionEvidenceValidationV1(
        ready=True,
        evidence=evidence,
        warnings=_unique(warnings),
        status=(
            "Ready — shared homogeneous, declared-resistance and arbitrary "
            "N-path construction evidence is complete"
        ),
    )


def _identity_blockers(values: list[str], kind: str) -> tuple[str, ...]:
    blockers: list[str] = []
    if any(not value for value in values):
        blockers.append(f"Every {kind} requires a stable identity")
    duplicates = sorted(
        value for value in set(values) if value and values.count(value) > 1
    )
    if duplicates:
        blockers.append(
            f"Duplicate {kind} identity/identities: " + ", ".join(duplicates)
        )
    return tuple(blockers)


def _reference_blockers(
    values: tuple[str, ...],
    known: set[str],
    scope: str,
) -> tuple[str, ...]:
    missing = sorted(value for value in values if value not in known)
    return (
        (f"Unknown {scope} layer reference(s): " + ", ".join(missing),)
        if missing
        else ()
    )


def _duplicate_reference_blockers(
    values: tuple[str, ...],
    scope: str,
) -> tuple[str, ...]:
    duplicates = sorted(
        value for value in set(values) if value and values.count(value) > 1
    )
    return (
        (f"Duplicate {scope} reference(s): " + ", ".join(duplicates),)
        if duplicates
        else ()
    )


def _blocked(
    *blockers: str,
    warnings: list[str] | tuple[str, ...] = (),
) -> SharedConstructionEvidenceValidationV1:
    return SharedConstructionEvidenceValidationV1(
        ready=False,
        blockers=_unique(blockers) or ("Shared construction evidence is blocked",),
        warnings=_unique(warnings),
        status="Blocked — shared construction evidence is not trustworthy",
    )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))
