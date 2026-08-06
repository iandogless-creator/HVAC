# ======================================================================
# H-S66-N3A — Committed room Cv/Tai evidence authority
# ======================================================================

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math

from HVAC.heatloss.physics.cv_tai_model import compute_cv_tai


@dataclass(frozen=True, slots=True)
class CommittedRoomCvTaiEvidenceRowV1:
    """Derived Cv/Tai evidence for one exact room identity."""

    room_id: str
    total_fabric_heat_loss_W: float
    total_exposed_area_m2: float
    tei_C: float
    cv_K: float
    tai_C: float
    tei_source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedRoomCvTaiEvidenceV1:
    """Fresh accepted fabric evidence resolved to room Cv and Tai."""

    schema: str = "committed_room_cv_tai_evidence_v1"
    ready: bool = False
    rooms: tuple[CommittedRoomCvTaiEvidenceRowV1, ...] = ()
    room_count: int = 0
    status: str = "Committed room Cv/Tai evidence not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Tai is derived from fresh accepted fabric-only room evidence: "
        "Cv = sum(Qf) / (sum(A) x 4.8), Tai = Tei + Cv. Qv is neither "
        "an input nor an output, so ventilation cannot feed back into Tai. "
        "No pipe-section mapping, persistence or GUI mutation occurs."
    )


def build_committed_room_cv_tai_evidence_v1(
        *,
        heatloss_results_valid: object,
        committed_room_ids: Iterable[str],
        total_fabric_heat_loss_W_by_room_id: Mapping[str, object],
        total_exposed_area_m2_by_room_id: Mapping[str, object],
        effective_tei_C_by_room_id: Mapping[str, object],
        tei_source_by_room_id: Mapping[str, str],
) -> CommittedRoomCvTaiEvidenceV1:
    """Resolve exact room Cv/Tai evidence without reading or mutating state."""

    blockers: list[str] = []
    if heatloss_results_valid is not True:
        blockers.append("Fresh accepted heat-loss results are required")

    room_ids = _canonical_room_ids_v1(committed_room_ids, blockers)
    qf_by_id = _canonical_mapping_v1(
        total_fabric_heat_loss_W_by_room_id,
        "Committed room fabric heat-loss",
        blockers,
    )
    area_by_id = _canonical_mapping_v1(
        total_exposed_area_m2_by_room_id,
        "Committed room exposed-area",
        blockers,
    )
    tei_by_id = _canonical_mapping_v1(
        effective_tei_C_by_room_id,
        "Effective room Tei",
        blockers,
    )
    tei_sources = _canonical_mapping_v1(
        tei_source_by_room_id,
        "Effective room Tei source",
        blockers,
    )

    required_ids = set(room_ids)
    for label, supplied in (
        ("fabric heat-loss", set(qf_by_id)),
        ("exposed-area", set(area_by_id)),
        ("Tei", set(tei_by_id)),
        ("Tei source", set(tei_sources)),
    ):
        for room_id in sorted(required_ids - supplied):
            blockers.append(f"{room_id}: committed room {label} is required")
        for room_id in sorted(supplied - required_ids):
            blockers.append(
                f"{room_id}: {label} evidence has no committed room identity"
            )

    normalised: dict[str, tuple[float, float, float, str]] = {}
    for room_id in room_ids:
        if not all(
            room_id in values
            for values in (qf_by_id, area_by_id, tei_by_id, tei_sources)
        ):
            continue
        try:
            qf_W = _nonnegative_finite_v1(
                qf_by_id[room_id], "Total fabric heat loss"
            )
            area_m2 = _positive_finite_v1(
                area_by_id[room_id], "Total exposed area"
            )
            tei_C = _finite_v1(tei_by_id[room_id], "Tei")
            tei_source = _text_v1(tei_sources[room_id])
            if not tei_source:
                raise ValueError("Tei source is required")
            normalised[room_id] = (qf_W, area_m2, tei_C, tei_source)
        except ValueError as exc:
            blockers.append(f"{room_id}: {exc}")

    if blockers:
        return _blocked_v1(*blockers)

    rows: list[CommittedRoomCvTaiEvidenceRowV1] = []
    for room_id in room_ids:
        qf_W, area_m2, tei_C, tei_source = normalised[room_id]
        result = compute_cv_tai(
            total_fabric_heat_loss_w=qf_W,
            total_exposed_area_m2=area_m2,
            tei_internal_env_temp_c=tei_C,
        )
        rows.append(
            CommittedRoomCvTaiEvidenceRowV1(
                room_id=room_id,
                total_fabric_heat_loss_W=qf_W,
                total_exposed_area_m2=area_m2,
                tei_C=float(result.tei_c),
                cv_K=float(result.cv_k),
                tai_C=float(result.tai_c),
                tei_source=tei_source,
                ready=True,
                status="Ready — Tai derived from fresh accepted fabric evidence",
            )
        )

    return CommittedRoomCvTaiEvidenceV1(
        ready=True,
        rooms=tuple(rows),
        room_count=len(rows),
        status=(
            f"Ready — Cv/Tai resolved for all {len(rows)} committed room(s)"
        ),
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
        room_id = _text_v1(raw_value)
        if not room_id or room_id != raw_value:
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
        room_id = _text_v1(raw_room_id)
        if not room_id or room_id != raw_room_id:
            blockers.append(f"Every {label.lower()} entry requires canonical room_id")
        elif room_id in result:
            blockers.append(f"Duplicate {label.lower()} identity: {room_id}")
        else:
            result[room_id] = value
    return result


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


def _text_v1(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _blocked_v1(*blockers: str) -> CommittedRoomCvTaiEvidenceV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedRoomCvTaiEvidenceV1(
        ready=False,
        rooms=(),
        room_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
