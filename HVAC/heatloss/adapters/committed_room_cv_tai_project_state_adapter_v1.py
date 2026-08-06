# ======================================================================
# H-S66-N3A1 — ProjectState handoff into committed room Cv/Tai evidence
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
import math

from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.heatloss.physics.committed_room_cv_tai_evidence_v1 import (
    CommittedRoomCvTaiEvidenceV1,
    build_committed_room_cv_tai_evidence_v1,
)


def build_committed_room_cv_tai_from_project_state_v1(
        project_state: object,
) -> CommittedRoomCvTaiEvidenceV1:
    """Extract fresh committed room Qf/A and effective Ti/Tei for N3A."""

    if project_state is None:
        return _blocked_v1("ProjectState is required")
    if getattr(project_state, "heatloss_valid", False) is not True:
        return _blocked_v1("Fresh accepted heat-loss results are required")

    rooms = getattr(project_state, "rooms", None)
    if not isinstance(rooms, Mapping) or not rooms:
        return _blocked_v1("Committed ProjectState room identities are required")
    room_ids = tuple(str(room_id) for room_id in rooms)
    if any(not room_id.strip() or room_id != room_id.strip() for room_id in room_ids):
        return _blocked_v1("Every ProjectState room requires canonical room_id")

    results = getattr(project_state, "heatloss_results", None)
    if not isinstance(results, Mapping):
        return _blocked_v1("Accepted heat-loss result container is required")
    room_totals = results.get("room_totals")
    if not isinstance(room_totals, Mapping):
        return _blocked_v1("Accepted room heat-loss totals are required")

    blockers: list[str] = []
    qf_by_room: dict[str, object] = {}
    for raw_room_id, raw_total in room_totals.items():
        room_id = _canonical_id_v1(raw_room_id)
        if room_id is None:
            blockers.append(
                "Every accepted room heat-loss total requires canonical room_id"
            )
            continue
        if not isinstance(raw_total, Mapping):
            blockers.append(f"{room_id}: accepted room heat-loss total is invalid")
            continue
        if "q_fabric_W" not in raw_total:
            blockers.append(f"{room_id}: accepted room Qf is required")
            continue
        qf_by_room[room_id] = raw_total.get("q_fabric_W")

    fabric_rows = _fabric_rows_v1(results.get("fabric"), blockers)
    area_by_room: dict[str, float] = {}
    row_qf_by_room: dict[str, float] = {}
    delta_t_by_room: dict[str, list[float]] = {}
    seen_surface_ids: set[str] = set()
    for index, row in enumerate(fabric_rows):
        room_id = _canonical_id_v1(_field_v1(row, "room_id"))
        surface_id = _canonical_id_v1(_field_v1(row, "surface_id"))
        if room_id is None:
            blockers.append(f"Fabric row {index}: canonical room_id is required")
            continue
        if surface_id is None:
            blockers.append(f"{room_id}: canonical fabric surface_id is required")
            continue
        if surface_id in seen_surface_ids:
            blockers.append(f"Duplicate accepted fabric surface identity: {surface_id}")
            continue
        seen_surface_ids.add(surface_id)
        try:
            area_m2 = _positive_finite_v1(
                _field_v1(row, "area_m2"), "Accepted fabric area"
            )
            row_qf_W = _nonnegative_finite_v1(
                _field_v1(row, "q_fabric_W", "qf_W"),
                "Accepted fabric-row Qf",
            )
            delta_t_K = _finite_v1(
                _field_v1(row, "delta_t_K"), "Accepted fabric-row delta T"
            )
        except ValueError as exc:
            blockers.append(f"{room_id}/{surface_id}: {exc}")
            continue
        area_by_room[room_id] = area_by_room.get(room_id, 0.0) + area_m2
        row_qf_by_room[room_id] = row_qf_by_room.get(room_id, 0.0) + row_qf_W
        delta_t_by_room.setdefault(room_id, []).append(delta_t_K)

    environment = getattr(project_state, "environment", None)
    try:
        external_C = _finite_v1(
            getattr(environment, "external_design_temp_C", None),
            "Environment external design temperature",
        )
    except ValueError as exc:
        blockers.append(str(exc))
        external_C = math.nan

    ti_by_room: dict[str, object] = {}
    ti_source_by_room: dict[str, str] = {}
    for room_id, room in rooms.items():
        effective_ti, source = resolve_effective_internal_temp_C(
            project_state, room
        )
        if effective_ti is None:
            blockers.append(f"{room_id}: effective Ti/Tei is required")
            continue
        try:
            ti_C = _finite_v1(effective_ti, "Effective Ti/Tei")
        except ValueError as exc:
            blockers.append(f"{room_id}: {exc}")
            continue
        ti_by_room[room_id] = ti_C
        ti_source_by_room[room_id] = (
            "Room internal design temperature (Ti/Tei)"
            if source == "room"
            else "Environment internal design temperature (Ti/Tei)"
        )

        deltas = delta_t_by_room.get(room_id, [])
        if deltas:
            accepted_delta_t_K = deltas[0]
            if any(
                not math.isclose(
                    value, accepted_delta_t_K, rel_tol=1.0e-9, abs_tol=1.0e-9
                )
                for value in deltas[1:]
            ):
                blockers.append(
                    f"{room_id}: accepted fabric rows do not share one Ti/Tei basis"
                )
            expected_delta_t_K = ti_C - external_C
            if math.isfinite(external_C) and not math.isclose(
                accepted_delta_t_K,
                expected_delta_t_K,
                rel_tol=1.0e-9,
                abs_tol=1.0e-9,
            ):
                blockers.append(
                    f"{room_id}: accepted fabric Ti/Tei basis is stale"
                )

    for room_id in sorted(set(qf_by_room) & set(row_qf_by_room)):
        try:
            committed_qf_W = _nonnegative_finite_v1(
                qf_by_room[room_id], "Accepted room Qf"
            )
        except ValueError as exc:
            blockers.append(f"{room_id}: {exc}")
            continue
        if not math.isclose(
            committed_qf_W,
            row_qf_by_room[room_id],
            rel_tol=1.0e-9,
            abs_tol=1.0e-6,
        ):
            blockers.append(
                f"{room_id}: accepted room Qf does not match its fabric rows"
            )

    if blockers:
        return _blocked_v1(*blockers)

    return build_committed_room_cv_tai_evidence_v1(
        heatloss_results_valid=True,
        committed_room_ids=room_ids,
        total_fabric_heat_loss_W_by_room_id=qf_by_room,
        total_exposed_area_m2_by_room_id=area_by_room,
        effective_tei_C_by_room_id=ti_by_room,
        tei_source_by_room_id=ti_source_by_room,
    )


def _fabric_rows_v1(raw_fabric: object, blockers: list[str]) -> tuple[object, ...]:
    if isinstance(raw_fabric, (list, tuple)):
        rows = tuple(raw_fabric)
    elif isinstance(raw_fabric, Mapping):
        raw_rows = raw_fabric.get("rows", raw_fabric.get("surfaces"))
        rows = tuple(raw_rows) if isinstance(raw_rows, (list, tuple)) else ()
    else:
        raw_rows = getattr(raw_fabric, "surfaces", None)
        rows = tuple(raw_rows) if isinstance(raw_rows, (list, tuple)) else ()
    if not rows:
        blockers.append("Accepted fabric result rows are required")
    return rows


def _field_v1(row: object, *names: str) -> object:
    for name in names:
        if isinstance(row, Mapping) and name in row:
            return row.get(name)
        if hasattr(row, name):
            return getattr(row, name)
    return None


def _canonical_id_v1(value: object) -> str | None:
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


def _nonnegative_finite_v1(value: object, label: str) -> float:
    number = _finite_v1(value, label)
    if number < 0.0:
        raise ValueError(f"{label} must not be negative")
    return number


def _blocked_v1(*blockers: str) -> CommittedRoomCvTaiEvidenceV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedRoomCvTaiEvidenceV1(
        ready=False,
        rooms=(),
        room_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
