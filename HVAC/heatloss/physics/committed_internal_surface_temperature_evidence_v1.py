# ======================================================================
# H-S66-N3D1 — Standard-Rsi internal-surface temperature evidence
# ======================================================================

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math


HORIZONTAL_HEAT_FLOW_RSI_M2K_W_V1 = 0.13
UPWARD_HEAT_FLOW_RSI_M2K_W_V1 = 0.10
DOWNWARD_HEAT_FLOW_RSI_M2K_W_V1 = 0.17

_HORIZONTAL_SURFACE_CLASSES_V1 = frozenset(
    {
        "wall",
        "external_wall",
        "internal_wall",
        "window",
        "door",
        "opening",
        "glazed_door",
    }
)
_UPWARD_SURFACE_CLASSES_V1 = frozenset(
    {"roof", "ceiling", "flat_roof", "pitched_roof", "external_roof"}
)
_DOWNWARD_SURFACE_CLASSES_V1 = frozenset(
    {"floor", "ground_floor", "exposed_floor", "external_floor"}
)


@dataclass(frozen=True, slots=True)
class CommittedInternalSurfaceTemperatureRowV1:
    """Derived internal face temperature for one accepted fabric row."""

    room_id: str
    surface_id: str
    surface_class: str
    area_m2: float
    fabric_heat_flow_W: float
    internal_air_temperature_C: float
    heat_flow_direction: str
    internal_surface_resistance_m2K_W: float
    internal_surface_temperature_C: float
    resistance_source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedInternalSurfaceTemperatureEvidenceV1:
    """Fresh accepted fabric rows resolved with declared standard Rsi."""

    schema: str = "committed_internal_surface_temperature_evidence_v1"
    ready: bool = False
    surfaces: tuple[CommittedInternalSurfaceTemperatureRowV1, ...] = ()
    surface_count: int = 0
    room_count: int = 0
    status: str = "Committed internal-surface temperature evidence not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Tsi = Ti - (Qf / A) x Rsi, with signed outward fabric heat flow. "
        "Declared standard Rsi values are 0.13 m2K/W for horizontal heat "
        "flow, 0.10 m2K/W for upward heat flow and 0.17 m2K/W for "
        "downward heat flow. These defaults do not come from, alter or "
        "complete the U-value construction workflow. No view factors, Tri, "
        "pipe-section handoff or persistence are resolved here."
    )


def build_committed_internal_surface_temperature_evidence_v1(
        *,
        heatloss_results_valid: object,
        committed_room_ids: Iterable[str],
        effective_internal_temperature_C_by_room_id: Mapping[str, object],
        accepted_fabric_rows: Iterable[object],
) -> CommittedInternalSurfaceTemperatureEvidenceV1:
    """Derive exact accepted-row Tsi values without reading or mutating state."""

    blockers: list[str] = []
    if heatloss_results_valid is not True:
        blockers.append("Fresh accepted heat-loss results are required")

    room_ids = _canonical_room_ids_v1(committed_room_ids, blockers)
    room_id_set = set(room_ids)
    temperatures = _canonical_mapping_v1(
        effective_internal_temperature_C_by_room_id,
        "Effective internal temperature",
        blockers,
    )
    for room_id in sorted(room_id_set - set(temperatures)):
        blockers.append(f"{room_id}: effective internal temperature is required")
    for room_id in sorted(set(temperatures) - room_id_set):
        blockers.append(
            f"{room_id}: internal-temperature evidence has no committed room identity"
        )

    ti_by_room: dict[str, float] = {}
    for room_id in room_ids:
        if room_id not in temperatures:
            continue
        try:
            ti_by_room[room_id] = _temperature_v1(
                temperatures[room_id], "Effective internal temperature"
            )
        except ValueError as exc:
            blockers.append(f"{room_id}: {exc}")

    try:
        raw_rows = tuple(accepted_fabric_rows)
    except TypeError:
        raw_rows = ()
        blockers.append("Accepted fabric rows are required")
    if not raw_rows:
        blockers.append("Accepted fabric rows are required")

    normalised: list[
        tuple[str, str, str, float, float, str, float]
    ] = []
    seen_surface_ids: set[str] = set()
    row_count_by_room = {room_id: 0 for room_id in room_ids}
    for index, row in enumerate(raw_rows):
        room_id = _canonical_text_v1(_field_v1(row, "room_id"))
        surface_id = _canonical_text_v1(_field_v1(row, "surface_id"))
        surface_class = _normalised_surface_class_v1(
            _field_v1(row, "surface_class", "element_class", "element")
        )
        if room_id is None:
            blockers.append(f"Fabric row {index}: canonical room_id is required")
            continue
        if room_id not in room_id_set:
            blockers.append(
                f"{room_id}: fabric row has no committed room identity"
            )
            continue
        if surface_id is None:
            blockers.append(f"{room_id}: canonical fabric surface_id is required")
            continue
        if surface_id in seen_surface_ids:
            blockers.append(f"Duplicate accepted fabric surface: {surface_id}")
            continue
        seen_surface_ids.add(surface_id)
        if surface_class is None:
            blockers.append(
                f"{room_id}/{surface_id}: supported surface class is required"
            )
            continue
        try:
            area_m2 = _positive_finite_v1(
                _field_v1(row, "area_m2", "A"), "Accepted fabric area"
            )
            heat_flow_W = _finite_v1(
                _field_v1(row, "q_fabric_W", "qf_W", "Qf"),
                "Accepted fabric heat flow",
            )
            direction, rsi = standard_rsi_for_surface_class_v1(surface_class)
        except ValueError as exc:
            blockers.append(f"{room_id}/{surface_id}: {exc}")
            continue
        if room_id not in ti_by_room:
            continue
        normalised.append(
            (
                room_id,
                surface_id,
                surface_class,
                area_m2,
                heat_flow_W,
                direction,
                rsi,
            )
        )
        row_count_by_room[room_id] += 1

    for room_id in room_ids:
        if row_count_by_room[room_id] == 0:
            blockers.append(f"{room_id}: accepted fabric rows are required")

    if blockers:
        return _blocked_v1(*blockers)

    resolved: list[CommittedInternalSurfaceTemperatureRowV1] = []
    for (
        room_id,
        surface_id,
        surface_class,
        area_m2,
        heat_flow_W,
        direction,
        rsi,
    ) in normalised:
        ti_C = ti_by_room[room_id]
        tsi_C = ti_C - (heat_flow_W / area_m2) * rsi
        if tsi_C <= -273.15 or not math.isfinite(tsi_C):
            blockers.append(
                f"{room_id}/{surface_id}: derived internal-surface temperature "
                "must be finite and above absolute zero"
            )
            continue
        resolved.append(
            CommittedInternalSurfaceTemperatureRowV1(
                room_id=room_id,
                surface_id=surface_id,
                surface_class=surface_class,
                area_m2=area_m2,
                fabric_heat_flow_W=heat_flow_W,
                internal_air_temperature_C=ti_C,
                heat_flow_direction=direction,
                internal_surface_resistance_m2K_W=rsi,
                internal_surface_temperature_C=tsi_C,
                resistance_source="Declared standard Rsi by heat-flow direction",
                ready=True,
                status="Ready — Tsi derived from accepted fabric-row heat flow",
            )
        )

    if blockers or len(resolved) != len(normalised):
        return _blocked_v1(*blockers)

    return CommittedInternalSurfaceTemperatureEvidenceV1(
        ready=True,
        surfaces=tuple(resolved),
        surface_count=len(resolved),
        room_count=len(room_ids),
        status=(
            f"Ready — Tsi resolved for {len(resolved)} accepted fabric "
            f"surface(s) across {len(room_ids)} committed room(s)"
        ),
        blockers=(),
    )


def standard_rsi_for_surface_class_v1(
        surface_class: str,
) -> tuple[str, float]:
    """Return bounded standard heat-flow direction and Rsi evidence."""

    normalised = _normalised_surface_class_v1(surface_class)
    if normalised in _HORIZONTAL_SURFACE_CLASSES_V1:
        return "horizontal", HORIZONTAL_HEAT_FLOW_RSI_M2K_W_V1
    if normalised in _UPWARD_SURFACE_CLASSES_V1:
        return "upward", UPWARD_HEAT_FLOW_RSI_M2K_W_V1
    if normalised in _DOWNWARD_SURFACE_CLASSES_V1:
        return "downward", DOWNWARD_HEAT_FLOW_RSI_M2K_W_V1
    raise ValueError(f"Unsupported surface class for standard Rsi: {surface_class!r}")


def _canonical_room_ids_v1(
        values: Iterable[str], blockers: list[str]
) -> tuple[str, ...]:
    try:
        raw_values = tuple(values)
    except TypeError:
        blockers.append("Committed room identities are required")
        return ()
    room_ids: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        room_id = _canonical_text_v1(raw_value)
        if room_id is None:
            blockers.append("Every committed room requires canonical room_id")
        elif room_id in seen:
            blockers.append(f"Duplicate committed room identity: {room_id}")
        else:
            seen.add(room_id)
            room_ids.append(room_id)
    if not room_ids:
        blockers.append("At least one committed room identity is required")
    return tuple(room_ids)


def _canonical_mapping_v1(
        values: Mapping[str, object], label: str, blockers: list[str]
) -> dict[str, object]:
    if not isinstance(values, Mapping):
        blockers.append(f"{label} mapping is required")
        return {}
    result: dict[str, object] = {}
    for raw_room_id, value in values.items():
        room_id = _canonical_text_v1(raw_room_id)
        if room_id is None:
            blockers.append(f"Every {label.lower()} entry requires canonical room_id")
        else:
            result[room_id] = value
    return result


def _field_v1(row: object, *names: str) -> object:
    for name in names:
        if isinstance(row, Mapping) and name in row:
            return row.get(name)
        if hasattr(row, name):
            return getattr(row, name)
    return None


def _canonical_text_v1(value: object) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    return value


def _normalised_surface_class_v1(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _finite_v1(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be numeric") from None
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _positive_finite_v1(value: object, label: str) -> float:
    number = _finite_v1(value, label)
    if number <= 0.0:
        raise ValueError(f"{label} must be greater than zero")
    return number


def _temperature_v1(value: object, label: str) -> float:
    number = _finite_v1(value, label)
    if number <= -273.15:
        raise ValueError(f"{label} must be above absolute zero")
    return number


def _blocked_v1(
        *blockers: str,
) -> CommittedInternalSurfaceTemperatureEvidenceV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedInternalSurfaceTemperatureEvidenceV1(
        ready=False,
        surfaces=(),
        surface_count=0,
        room_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
