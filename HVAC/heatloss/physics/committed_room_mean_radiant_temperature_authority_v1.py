# ======================================================================
# H-S66-N3D — Committed-room mean-radiant temperature authority
# ======================================================================

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class CommittedRoomMeanRadiantTemperatureRowV1:
    """Resolved radiative enclosure temperature for one exact room."""

    room_id: str
    mean_radiant_temperature_C: float
    surface_count: int
    radiant_view_factor_sum: float
    source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedRoomMeanRadiantTemperatureAuthorityV1:
    """Fresh committed internal-surface evidence resolved to room Tri."""

    schema: str = "committed_room_mean_radiant_temperature_authority_v1"
    ready: bool = False
    rooms: tuple[CommittedRoomMeanRadiantTemperatureRowV1, ...] = ()
    room_count: int = 0
    status: str = "Committed-room mean-radiant temperature authority not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Tri is the fourth-power mean of absolute internal-surface "
        "temperatures, weighted by explicit radiant view factors. Each "
        "room's factors must sum to one. This authority does not infer "
        "surface temperatures from Qf, area or Tai, does not use an "
        "Environment-temperature proxy, and performs no persistence or "
        "pipe-section handoff."
    )


def build_committed_room_mean_radiant_temperature_authority_v1(
        *,
        surface_temperature_evidence_fresh: object,
        committed_room_ids: Iterable[str],
        internal_surface_rows: Iterable[object],
) -> CommittedRoomMeanRadiantTemperatureAuthorityV1:
    """Resolve exact room Tri from explicit surface temperatures and weights."""

    blockers: list[str] = []
    if surface_temperature_evidence_fresh is not True:
        blockers.append("Fresh internal-surface temperature evidence is required")

    room_ids = _canonical_room_ids_v1(committed_room_ids, blockers)
    required_room_ids = set(room_ids)
    try:
        raw_rows = tuple(internal_surface_rows)
    except TypeError:
        raw_rows = ()
        blockers.append("Internal-surface temperature rows are required")
    if not raw_rows:
        blockers.append("Internal-surface temperature rows are required")

    grouped: dict[str, list[tuple[float, float]]] = {
        room_id: [] for room_id in room_ids
    }
    seen_surface_ids: set[str] = set()
    for index, row in enumerate(raw_rows):
        room_id = _canonical_text_v1(_field_v1(row, "room_id"))
        surface_id = _canonical_text_v1(_field_v1(row, "surface_id"))
        if room_id is None:
            blockers.append(f"Surface row {index}: canonical room_id is required")
            continue
        if room_id not in required_room_ids:
            blockers.append(
                f"{room_id}: surface evidence has no committed room identity"
            )
            continue
        if surface_id is None:
            blockers.append(f"{room_id}: canonical surface_id is required")
            continue
        if surface_id in seen_surface_ids:
            blockers.append(
                f"Duplicate committed internal-surface identity: {surface_id}"
            )
            continue
        seen_surface_ids.add(surface_id)
        try:
            temperature_C = _temperature_v1(
                _field_v1(
                    row,
                    "internal_surface_temperature_C",
                    "surface_temperature_C",
                ),
                "Internal-surface temperature",
            )
            view_factor = _positive_finite_v1(
                _field_v1(row, "radiant_view_factor", "view_factor"),
                "Radiant view factor",
            )
            if view_factor > 1.0:
                raise ValueError("Radiant view factor must not exceed one")
        except ValueError as exc:
            blockers.append(f"{room_id}/{surface_id}: {exc}")
            continue
        grouped[room_id].append((temperature_C, view_factor))

    normalised: dict[str, tuple[tuple[tuple[float, float], ...], float]] = {}
    for room_id in room_ids:
        rows = tuple(grouped.get(room_id, ()))
        if not rows:
            blockers.append(
                f"{room_id}: complete internal-surface evidence is required"
            )
            continue
        weight_sum = math.fsum(weight for _temperature, weight in rows)
        if not math.isclose(weight_sum, 1.0, rel_tol=0.0, abs_tol=1.0e-9):
            blockers.append(
                f"{room_id}: radiant view factors must sum to one "
                f"(resolved {weight_sum:.12g})"
            )
            continue
        normalised[room_id] = (rows, weight_sum)

    if blockers:
        return _blocked_v1(*blockers)

    resolved: list[CommittedRoomMeanRadiantTemperatureRowV1] = []
    for room_id in room_ids:
        rows, weight_sum = normalised[room_id]
        radiant_temperature_K4 = math.fsum(
            weight * (temperature_C + 273.15) ** 4
            for temperature_C, weight in rows
        )
        tri_C = radiant_temperature_K4 ** 0.25 - 273.15
        resolved.append(
            CommittedRoomMeanRadiantTemperatureRowV1(
                room_id=room_id,
                mean_radiant_temperature_C=tri_C,
                surface_count=len(rows),
                radiant_view_factor_sum=weight_sum,
                source=(
                    "Fresh committed internal-surface temperatures and "
                    "explicit radiant view factors"
                ),
                ready=True,
                status="Ready — room Tri resolved from complete surface evidence",
            )
        )

    return CommittedRoomMeanRadiantTemperatureAuthorityV1(
        ready=True,
        rooms=tuple(resolved),
        room_count=len(resolved),
        status=f"Ready — Tri resolved for all {len(resolved)} committed room(s)",
        blockers=(),
    )


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
) -> CommittedRoomMeanRadiantTemperatureAuthorityV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedRoomMeanRadiantTemperatureAuthorityV1(
        ready=False,
        rooms=(),
        room_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
