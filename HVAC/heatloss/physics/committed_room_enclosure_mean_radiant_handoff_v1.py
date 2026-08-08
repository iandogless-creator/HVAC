# ======================================================================
# H-S66-N3D3 — Complete-room enclosure weighting into N3D
# ======================================================================

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
import math

from HVAC.heatloss.physics.committed_internal_surface_temperature_evidence_v1 import (
    CommittedInternalSurfaceTemperatureEvidenceV1,
)
from HVAC.heatloss.physics.committed_room_mean_radiant_temperature_authority_v1 import (
    CommittedRoomMeanRadiantTemperatureAuthorityV1,
    build_committed_room_mean_radiant_temperature_authority_v1,
)


def build_committed_room_enclosure_mean_radiant_handoff_v1(
        *,
        committed_room_ids: Iterable[str],
        internal_surface_temperature_evidence: (
            CommittedInternalSurfaceTemperatureEvidenceV1
        ),
) -> CommittedRoomMeanRadiantTemperatureAuthorityV1:
    """Area-normalise complete room surfaces and delegate Tri to N3D."""

    blockers: list[str] = []
    room_ids = _canonical_room_ids_v1(committed_room_ids, blockers)
    room_id_set = set(room_ids)
    if not isinstance(
        internal_surface_temperature_evidence,
        CommittedInternalSurfaceTemperatureEvidenceV1,
    ) or not internal_surface_temperature_evidence.ready:
        blockers.append("Ready N3D1 internal-surface temperature evidence is required")
        evidence_blockers = tuple(
            getattr(internal_surface_temperature_evidence, "blockers", ()) or ()
        )
        blockers.extend(str(value) for value in evidence_blockers if value)
        surfaces = ()
    else:
        surfaces = tuple(
            internal_surface_temperature_evidence.surfaces or ()
        )
        if not surfaces:
            blockers.append("Resolved internal-surface rows are required")

    grouped: dict[str, list[tuple[str, float, float]]] = {
        room_id: [] for room_id in room_ids
    }
    seen_surface_ids: set[str] = set()
    for index, surface in enumerate(surfaces):
        room_id = _canonical_text_v1(getattr(surface, "room_id", None))
        surface_id = _canonical_text_v1(getattr(surface, "surface_id", None))
        if room_id is None:
            blockers.append(f"Resolved surface row {index}: canonical room_id is required")
            continue
        if room_id not in room_id_set:
            blockers.append(
                f"{room_id}: resolved surface has no committed room identity"
            )
            continue
        if surface_id is None:
            blockers.append(f"{room_id}: canonical surface_id is required")
            continue
        if surface_id in seen_surface_ids:
            blockers.append(f"Duplicate resolved internal surface: {surface_id}")
            continue
        seen_surface_ids.add(surface_id)
        try:
            area_m2 = _positive_finite_v1(
                getattr(surface, "area_m2", None), "Resolved surface area"
            )
            temperature_C = _temperature_v1(
                getattr(surface, "internal_surface_temperature_C", None),
                "Resolved internal-surface temperature",
            )
        except ValueError as exc:
            blockers.append(f"{room_id}/{surface_id}: {exc}")
            continue
        grouped[room_id].append((surface_id, area_m2, temperature_C))

    weighted_rows: list[dict[str, object]] = []
    for room_id in room_ids:
        room_surfaces = tuple(grouped.get(room_id, ()))
        if not room_surfaces:
            blockers.append(
                f"{room_id}: complete resolved enclosure surfaces are required"
            )
            continue
        total_area_m2 = math.fsum(area for _sid, area, _temperature in room_surfaces)
        if not math.isfinite(total_area_m2) or total_area_m2 <= 0.0:
            blockers.append(
                f"{room_id}: total resolved enclosure area must be positive and finite"
            )
            continue
        for surface_id, area_m2, temperature_C in room_surfaces:
            weighted_rows.append(
                {
                    "room_id": room_id,
                    "surface_id": surface_id,
                    "internal_surface_temperature_C": temperature_C,
                    "radiant_view_factor": area_m2 / total_area_m2,
                }
            )

    if blockers:
        return _blocked_v1(*blockers)

    authority = build_committed_room_mean_radiant_temperature_authority_v1(
        surface_temperature_evidence_fresh=True,
        committed_room_ids=room_ids,
        internal_surface_rows=weighted_rows,
    )
    if not authority.ready:
        return authority

    source = (
        "N3D3 complete accepted-enclosure area-fraction weighting; "
        "not position-specific geometric view factors"
    )
    return CommittedRoomMeanRadiantTemperatureAuthorityV1(
        schema=authority.schema,
        ready=True,
        rooms=tuple(
            replace(
                row,
                source=source,
                status=(
                    "Ready — room Tri resolved from enclosure area-fraction "
                    "weighting"
                ),
            )
            for row in authority.rooms
        ),
        room_count=authority.room_count,
        status=(
            f"Ready — area-weighted enclosure Tri resolved for all "
            f"{authority.room_count} committed room(s)"
        ),
        blockers=(),
        note=(
            "Each room's complete resolved internal-surface evidence is "
            "weighted by Ai / sum(A) before delegation to N3D's "
            "fourth-power absolute-temperature mean. This is a declared "
            "room-enclosure area-fraction approximation, not a geometric "
            "view-factor solution for a particular pipe position. No "
            "temperature, view factor, thermal basis or mapping is persisted."
        ),
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
