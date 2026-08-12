from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
    validate_shared_construction_layer_path_evidence_v1,
)


@dataclass(frozen=True, slots=True)
class ConstructionPathTemperaturePointV1:
    label: str
    resistance_m2K_W: float
    cumulative_resistance_m2K_W: float
    temperature_C: float
    kind: str
    layer_id: str = ""


@dataclass(frozen=True, slots=True)
class ConstructionPathHeatFlowRowV1:
    path_id: str
    label: str
    area_fraction: float
    total_resistance_m2K_W: float
    heat_flow_W_m2: float
    weighted_heat_flow_W_m2: float
    points: tuple[ConstructionPathTemperaturePointV1, ...]


@dataclass(frozen=True, slots=True)
class ConstructionPathHeatFlowTemperatureEvidenceV1:
    ready: bool
    construction_id: str = ""
    internal_temperature_C: float | None = None
    external_temperature_C: float | None = None
    paths: tuple[ConstructionPathHeatFlowRowV1, ...] = ()
    total_weighted_heat_flow_W_m2: float | None = None
    blockers: tuple[str, ...] = ()
    status: str = "Construction path heat-flow evidence not resolved"


def build_construction_path_heat_flow_temperature_evidence_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    *,
    internal_temperature_C: object,
    external_temperature_C: object,
) -> ConstructionPathHeatFlowTemperatureEvidenceV1:
    validation = validate_shared_construction_layer_path_evidence_v1(evidence)
    blockers = list(validation.blockers)
    ti = _temperature(internal_temperature_C, "Internal design temperature", blockers)
    te = _temperature(external_temperature_C, "External design temperature", blockers)
    rsi = _positive_resistance(
        evidence.internal_surface_resistance_m2K_W,
        "Rsi",
        blockers,
    )
    rso = _positive_resistance(
        evidence.external_surface_resistance_m2K_W,
        "Rso",
        blockers,
    )
    if ti is not None and te is not None and ti <= te:
        blockers.append("Internal design temperature must exceed external design temperature")
    if blockers:
        return _blocked(evidence, blockers)

    layers = evidence.layer_by_id()
    rows: list[ConstructionPathHeatFlowRowV1] = []
    total_weighted = 0.0
    for path in evidence.paths:
        series: list[tuple[str, float, str, str]] = [("Rsi", rsi, "surface", "")]
        for layer_id in evidence.active_path_layer_ids(path.path_id):
            layer = layers[layer_id]
            try:
                resistance = float(layer.resolved_resistance_m2K_W())
            except (TypeError, ValueError) as exc:
                blockers.append(str(exc))
                continue
            if not math.isfinite(resistance) or resistance <= 0.0:
                blockers.append(f"{layer.label} resistance must be finite and positive")
                continue
            series.append((layer.label, resistance, "layer", layer_id))
        series.append(("Rso", rso, "surface", ""))
        if blockers:
            continue

        total_r = sum(item[1] for item in series)
        heat_flow = (ti - te) / total_r
        cumulative = 0.0
        points = [
            ConstructionPathTemperaturePointV1(
                label="tai",
                resistance_m2K_W=0.0,
                cumulative_resistance_m2K_W=0.0,
                temperature_C=ti,
                kind="air",
            )
        ]
        for label, resistance, kind, layer_id in series:
            cumulative += resistance
            points.append(
                ConstructionPathTemperaturePointV1(
                    label=label,
                    resistance_m2K_W=resistance,
                    cumulative_resistance_m2K_W=cumulative,
                    temperature_C=ti - heat_flow * cumulative,
                    kind=kind,
                    layer_id=layer_id,
                )
            )
        weighted = float(path.area_fraction) * heat_flow
        total_weighted += weighted
        rows.append(
            ConstructionPathHeatFlowRowV1(
                path_id=path.path_id,
                label=path.label,
                area_fraction=float(path.area_fraction),
                total_resistance_m2K_W=total_r,
                heat_flow_W_m2=heat_flow,
                weighted_heat_flow_W_m2=weighted,
                points=tuple(points),
            )
        )

    if blockers or len(rows) != len(evidence.paths):
        return _blocked(evidence, blockers or ["Every path must resolve completely"])
    return ConstructionPathHeatFlowTemperatureEvidenceV1(
        ready=True,
        construction_id=evidence.construction_id,
        internal_temperature_C=ti,
        external_temperature_C=te,
        paths=tuple(rows),
        total_weighted_heat_flow_W_m2=total_weighted,
        status="Ready — candidate path heat flow and interface temperatures resolved",
    )


def _temperature(value: object, label: str, blockers: list[str]) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        blockers.append(f"{label} is required")
        return None
    if not math.isfinite(result):
        blockers.append(f"{label} must be finite")
        return None
    return result


def _positive_resistance(value: object, label: str, blockers: list[str]) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        blockers.append(f"{label} is required")
        return None
    if not math.isfinite(result) or result <= 0.0:
        blockers.append(f"{label} must be finite and positive")
        return None
    return result


def _blocked(evidence, blockers) -> ConstructionPathHeatFlowTemperatureEvidenceV1:
    return ConstructionPathHeatFlowTemperatureEvidenceV1(
        ready=False,
        construction_id=str(getattr(evidence, "construction_id", "") or ""),
        blockers=tuple(dict.fromkeys(str(item) for item in blockers if str(item))),
        status="Blocked — candidate path heat-flow evidence is incomplete",
    )
