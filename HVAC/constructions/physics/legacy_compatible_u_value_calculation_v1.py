from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
    validate_shared_construction_layer_path_evidence_v1,
)


LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1 = (
    "legacy_area_weighted_path_transmittance_v1"
)


@dataclass(frozen=True, slots=True)
class LegacyLayerResistanceRowV1:
    layer_id: str
    label: str
    resistance_m2K_W: float


@dataclass(frozen=True, slots=True)
class LegacyHeatFlowPathCalculationV1:
    path_id: str
    label: str
    area_fraction: float
    layers: tuple[LegacyLayerResistanceRowV1, ...]
    layer_resistance_m2K_W: float
    surface_resistance_m2K_W: float
    total_resistance_m2K_W: float
    path_u_value_W_m2K: float
    weighted_u_contribution_W_m2K: float


@dataclass(frozen=True, slots=True)
class LegacyCompatibleUValueResultV1:
    ready: bool
    construction_id: str = ""
    method: str = LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1
    paths: tuple[LegacyHeatFlowPathCalculationV1, ...] = ()
    u_value_W_m2K: float | None = None
    effective_resistance_m2K_W: float | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Legacy-compatible U-value not resolved"


def resolve_legacy_compatible_u_value_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
) -> LegacyCompatibleUValueResultV1:
    """Resolve the traditional area-weighted parallel-path U-value.

    Each complete physical path is treated as a series resistance including
    the same explicit internal and external surface films. Path
    transmittances are then weighted by their area fractions:

        U = sum(f_path / R_total_path)

    This is intentionally a legacy-compatible method. It does not implement
    the ISO 6946 combined upper/lower resistance limit method.
    """

    validation = validate_shared_construction_layer_path_evidence_v1(evidence)
    if not validation.ready:
        return _blocked(
            evidence=evidence,
            blockers=validation.blockers,
            warnings=validation.warnings,
        )

    rsi = evidence.internal_surface_resistance_m2K_W
    rse = evidence.external_surface_resistance_m2K_W
    if rsi is None or rse is None:
        return _blocked(
            evidence=evidence,
            blockers=(
                "Legacy-compatible calculation requires explicit Rsi and Rse",
            ),
            warnings=validation.warnings,
        )

    try:
        surface_resistance = float(rsi) + float(rse)
    except (TypeError, ValueError):
        return _blocked(
            evidence=evidence,
            blockers=("Legacy surface resistances must be numeric",),
            warnings=validation.warnings,
        )
    if not math.isfinite(surface_resistance) or surface_resistance <= 0.0:
        return _blocked(
            evidence=evidence,
            blockers=("Legacy surface resistance total must be finite and positive",),
            warnings=validation.warnings,
        )

    layers_by_id = evidence.layer_by_id()
    path_rows: list[LegacyHeatFlowPathCalculationV1] = []
    blockers: list[str] = []
    u_value = 0.0

    for path in evidence.paths:
        layer_rows: list[LegacyLayerResistanceRowV1] = []
        layer_resistance = 0.0
        active_layer_ids = evidence.active_path_layer_ids(path.path_id)
        for layer_id in active_layer_ids:
            layer = layers_by_id[layer_id]
            try:
                resistance = float(layer.resolved_resistance_m2K_W())
            except (TypeError, ValueError) as exc:
                blockers.append(str(exc))
                continue
            if not math.isfinite(resistance) or resistance <= 0.0:
                blockers.append(
                    f"Layer {layer.layer_id} resistance must be finite and positive"
                )
                continue
            layer_rows.append(
                LegacyLayerResistanceRowV1(
                    layer_id=layer.layer_id,
                    label=layer.label,
                    resistance_m2K_W=resistance,
                )
            )
            layer_resistance += resistance

        if len(layer_rows) != len(active_layer_ids):
            continue

        total_resistance = surface_resistance + layer_resistance
        if not math.isfinite(total_resistance) or total_resistance <= 0.0:
            blockers.append(
                f"Path {path.path_id} total resistance must be finite and positive"
            )
            continue

        path_u_value = 1.0 / total_resistance
        weighted_contribution = float(path.area_fraction) * path_u_value
        if not math.isfinite(weighted_contribution):
            blockers.append(
                f"Path {path.path_id} weighted U-value contribution is not finite"
            )
            continue

        path_rows.append(
            LegacyHeatFlowPathCalculationV1(
                path_id=path.path_id,
                label=path.label,
                area_fraction=float(path.area_fraction),
                layers=tuple(layer_rows),
                layer_resistance_m2K_W=layer_resistance,
                surface_resistance_m2K_W=surface_resistance,
                total_resistance_m2K_W=total_resistance,
                path_u_value_W_m2K=path_u_value,
                weighted_u_contribution_W_m2K=weighted_contribution,
            )
        )
        u_value += weighted_contribution

    if blockers:
        return _blocked(
            evidence=evidence,
            blockers=tuple(blockers),
            warnings=validation.warnings,
        )
    if len(path_rows) != len(evidence.paths):
        return _blocked(
            evidence=evidence,
            blockers=("Every heat-flow path must resolve completely",),
            warnings=validation.warnings,
        )
    if not math.isfinite(u_value) or u_value <= 0.0:
        return _blocked(
            evidence=evidence,
            blockers=("Legacy-compatible U-value must be finite and positive",),
            warnings=validation.warnings,
        )

    return LegacyCompatibleUValueResultV1(
        ready=True,
        construction_id=evidence.construction_id,
        paths=tuple(path_rows),
        u_value_W_m2K=u_value,
        effective_resistance_m2K_W=1.0 / u_value,
        warnings=validation.warnings,
        status=(
            "Ready — legacy area-weighted path-transmittance U-value resolved"
        ),
    )


def _blocked(
    *,
    evidence: SharedConstructionLayerPathEvidenceV1 | object,
    blockers: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> LegacyCompatibleUValueResultV1:
    return LegacyCompatibleUValueResultV1(
        ready=False,
        construction_id=str(getattr(evidence, "construction_id", "") or ""),
        blockers=_unique(blockers) or ("Legacy-compatible U-value is blocked",),
        warnings=_unique(warnings),
        status="Blocked — legacy-compatible U-value evidence is incomplete",
    )


def _unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))
