# ======================================================================
# H-S66-N3C — Committed pipe-section ambient Tai runtime handoff
# ======================================================================

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import math

from HVAC.heatloss.physics.committed_pipe_section_room_mapping_intent_v1 import (
    ENVIRONMENT_AMBIENT_SCOPE_V1,
    NOT_SET_AMBIENT_SCOPE_V1,
    ROOM_AMBIENT_SCOPE_V1,
    CommittedPipeSectionRoomMappingIntentV1,
    resolve_effective_committed_pipe_section_room_mapping_v1,
)
from HVAC.heatloss.physics.committed_room_cv_tai_evidence_v1 import (
    CommittedRoomCvTaiEvidenceV1,
)
from HVAC.heatloss.physics.committed_room_mean_radiant_temperature_authority_v1 import (
    CommittedRoomMeanRadiantTemperatureAuthorityV1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionAmbientTaiRuntimeRowV1:
    section_id: str
    ambient_scope: str
    room_id: str | None
    ambient_air_temperature_C: float
    ambient_air_temperature_source: str
    mean_radiant_temperature_C: float
    mean_radiant_temperature_source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionAmbientTaiRuntimeHandoffV1:
    schema: str = "committed_pipe_section_ambient_tai_runtime_handoff_v1"
    ready: bool = False
    sections: tuple[CommittedPipeSectionAmbientTaiRuntimeRowV1, ...] = ()
    section_count: int = 0
    room_mapped_section_count: int = 0
    environment_fallback_section_count: int = 0
    status: str = "Committed pipe-section ambient Tai handoff not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "An exact room mapping uses that room's fresh N3A Tai. An explicitly "
        "Environment / general-space choice uses the Environment internal "
        "temperature. Not set is calculation-blocking. "
        "A mapped section's mean-radiant temperature uses the exact fresh N3D "
        "room Tri and never copies Tai or Ti/Tei. No mapping, temperature, "
        "thermal basis or heat loss is persisted."
    )


def build_committed_pipe_section_ambient_tai_runtime_handoff_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        available_room_ids: Iterable[str],
        room_mapping_intent: CommittedPipeSectionRoomMappingIntentV1 | None,
        room_cv_tai_evidence: CommittedRoomCvTaiEvidenceV1 | None,
        room_mean_radiant_authority: (
            CommittedRoomMeanRadiantTemperatureAuthorityV1 | None
        ),
        environment_fallback_temperature_C: object,
) -> CommittedPipeSectionAmbientTaiRuntimeHandoffV1:
    """Resolve one authoritative local air temperature for every section."""

    blockers: list[str] = []
    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ) or not committed_authority.ready:
        blockers.append(
            "Ready committed proportioning hydraulic-input authority required"
        )
    sections = tuple(getattr(committed_authority, "sections", ()) or ())
    if not sections:
        blockers.append("Committed pipe sections are required")

    try:
        raw_room_ids = tuple(available_room_ids)
    except TypeError:
        raw_room_ids = ()
        blockers.append("Current ProjectState room identities are required")
    room_ids = tuple(_canonical_text_v1(value) for value in raw_room_ids)
    if not room_ids or any(not value for value in room_ids):
        blockers.append("Current ProjectState room identities are required")
    if len(set(room_ids)) != len(room_ids):
        blockers.append("ProjectState room identities must be unique")

    environment_C, environment_blocker = _temperature_v1(
        environment_fallback_temperature_C,
        "Environment internal-temperature fallback",
    )
    if environment_blocker:
        blockers.append(environment_blocker)

    tai_by_room_id: dict[str, float] = {}
    if isinstance(room_cv_tai_evidence, CommittedRoomCvTaiEvidenceV1):
        for row in tuple(room_cv_tai_evidence.rooms or ()):
            room_id = _canonical_text_v1(getattr(row, "room_id", ""))
            if not room_id:
                blockers.append("Every N3A Tai row requires canonical room_id")
                continue
            if room_id in tai_by_room_id:
                blockers.append(f"Duplicate N3A Tai room identity: {room_id}")
                continue
            try:
                tai_by_room_id[room_id] = _finite_v1(
                    getattr(row, "tai_C", None), "Room Tai"
                )
            except ValueError as exc:
                blockers.append(f"{room_id}: {exc}")

    tri_by_room_id: dict[str, float] = {}
    tri_source_by_room_id: dict[str, str] = {}
    tri_authority_blockers: list[str] = []
    if isinstance(
        room_mean_radiant_authority,
        CommittedRoomMeanRadiantTemperatureAuthorityV1,
    ):
        if room_mean_radiant_authority.ready:
            for row in tuple(room_mean_radiant_authority.rooms or ()):
                room_id = _canonical_text_v1(getattr(row, "room_id", ""))
                if not room_id:
                    tri_authority_blockers.append(
                        "Every N3D Tri row requires canonical room_id"
                    )
                    continue
                if room_id in tri_by_room_id:
                    tri_authority_blockers.append(
                        f"Duplicate N3D Tri room identity: {room_id}"
                    )
                    continue
                try:
                    tri_by_room_id[room_id] = _finite_v1(
                        getattr(row, "mean_radiant_temperature_C", None),
                        "Room Tri",
                    )
                except ValueError as exc:
                    tri_authority_blockers.append(f"{room_id}: {exc}")
                    continue
                tri_source_by_room_id[room_id] = str(
                    getattr(row, "source", "") or "N3D room Tri"
                )
        else:
            tri_authority_blockers.extend(
                str(value)
                for value in tuple(room_mean_radiant_authority.blockers or ())
                if value
            )

    if blockers:
        return _blocked_v1(*blockers)

    resolved: list[CommittedPipeSectionAmbientTaiRuntimeRowV1] = []
    seen: set[str] = set()
    for section in sections:
        section_id = _canonical_text_v1(getattr(section, "section_id", ""))
        if not section_id:
            blockers.append("Every committed pipe section requires section_id")
            continue
        if section_id in seen:
            blockers.append(f"Duplicate committed pipe section: {section_id}")
            continue
        seen.add(section_id)
        try:
            effective = resolve_effective_committed_pipe_section_room_mapping_v1(
                committed_authority=committed_authority,
                available_room_ids=room_ids,
                intent=room_mapping_intent,
                section_id=section_id,
            )
        except (TypeError, ValueError) as exc:
            blockers.append(f"{section_id}: {exc}")
            continue

        if effective.ambient_scope == ROOM_AMBIENT_SCOPE_V1:
            room_id = str(effective.room_id or "")
            if not isinstance(
                room_cv_tai_evidence, CommittedRoomCvTaiEvidenceV1
            ) or not room_cv_tai_evidence.ready:
                blockers.append(
                    f"{section_id}: fresh N3A room Tai evidence is required"
                )
                continue
            if room_id not in tai_by_room_id:
                blockers.append(
                    f"{section_id}: mapped room {room_id} has no exact N3A Tai"
                )
                continue
            if not isinstance(
                room_mean_radiant_authority,
                CommittedRoomMeanRadiantTemperatureAuthorityV1,
            ) or not room_mean_radiant_authority.ready:
                blockers.append(
                    f"{section_id}: fresh N3D room Tri authority is required"
                )
                blockers.extend(tri_authority_blockers)
                continue
            if tri_authority_blockers:
                blockers.extend(tri_authority_blockers)
                continue
            if room_id not in tri_by_room_id:
                blockers.append(
                    f"{section_id}: mapped room {room_id} has no exact N3D Tri"
                )
                continue
            ambient_C = tai_by_room_id[room_id]
            source = f"N3A room Tai — exact room {room_id}"
            mean_radiant_C = tri_by_room_id[room_id]
            mean_radiant_source = (
                f"N3D room Tri — exact room {room_id}; "
                f"{tri_source_by_room_id[room_id]}"
            )
            status = "Ready — exact mapped-room Tai and Tri resolved"
        elif effective.ambient_scope == ENVIRONMENT_AMBIENT_SCOPE_V1:
            room_id = None
            ambient_C = environment_C
            source = "Environment internal temperature — explicit general-space intent"
            mean_radiant_C = environment_C
            mean_radiant_source = (
                "Environment internal temperature — explicit general-space "
                "MRT proxy"
            )
            status = "Ready — explicit Environment ambient fallback resolved"
        elif effective.ambient_scope == NOT_SET_AMBIENT_SCOPE_V1:
            blockers.append(
                f"{section_id}: ambient location is Not set; explicitly choose "
                "Environment / general space or an exact room"
            )
            continue
        else:
            blockers.append(
                f"{section_id}: committed ambient scope is unsupported"
            )
            continue

        resolved.append(
            CommittedPipeSectionAmbientTaiRuntimeRowV1(
                section_id=section_id,
                ambient_scope=effective.ambient_scope,
                room_id=room_id,
                ambient_air_temperature_C=ambient_C,
                ambient_air_temperature_source=source,
                mean_radiant_temperature_C=mean_radiant_C,
                mean_radiant_temperature_source=mean_radiant_source,
                ready=True,
                status=status,
            )
        )

    if blockers or len(resolved) != len(sections):
        return _blocked_v1(*blockers)
    room_count = sum(
        row.ambient_scope == ROOM_AMBIENT_SCOPE_V1 for row in resolved
    )
    environment_count = len(resolved) - room_count
    return CommittedPipeSectionAmbientTaiRuntimeHandoffV1(
        ready=True,
        sections=tuple(resolved),
        section_count=len(resolved),
        room_mapped_section_count=room_count,
        environment_fallback_section_count=environment_count,
        status=(
            f"Ready — ambient Tai/MRT resolved for {len(resolved)} committed "
            f"section(s): {room_count} mapped room, {environment_count} "
            "Environment fallback"
        ),
        blockers=(),
    )


def ambient_temperature_mapping_from_handoff_v1(
        handoff: CommittedPipeSectionAmbientTaiRuntimeHandoffV1,
) -> dict[str, float]:
    if not isinstance(
        handoff, CommittedPipeSectionAmbientTaiRuntimeHandoffV1
    ) or not handoff.ready:
        raise ValueError("Ready committed pipe-section ambient Tai handoff required")
    return {
        row.section_id: row.ambient_air_temperature_C
        for row in handoff.sections
    }


def ambient_temperature_source_mapping_from_handoff_v1(
        handoff: CommittedPipeSectionAmbientTaiRuntimeHandoffV1,
) -> dict[str, str]:
    if not isinstance(
        handoff, CommittedPipeSectionAmbientTaiRuntimeHandoffV1
    ) or not handoff.ready:
        raise ValueError("Ready committed pipe-section ambient Tai handoff required")
    return {
        row.section_id: row.ambient_air_temperature_source
        for row in handoff.sections
    }


def mean_radiant_temperature_mapping_from_handoff_v1(
        handoff: CommittedPipeSectionAmbientTaiRuntimeHandoffV1,
) -> dict[str, float]:
    if not isinstance(
        handoff, CommittedPipeSectionAmbientTaiRuntimeHandoffV1
    ) or not handoff.ready:
        raise ValueError("Ready committed pipe-section ambient Tai handoff required")
    return {
        row.section_id: row.mean_radiant_temperature_C
        for row in handoff.sections
    }


def mean_radiant_temperature_source_mapping_from_handoff_v1(
        handoff: CommittedPipeSectionAmbientTaiRuntimeHandoffV1,
) -> dict[str, str]:
    if not isinstance(
        handoff, CommittedPipeSectionAmbientTaiRuntimeHandoffV1
    ) or not handoff.ready:
        raise ValueError("Ready committed pipe-section ambient Tai handoff required")
    return {
        row.section_id: row.mean_radiant_temperature_source
        for row in handoff.sections
    }


def _temperature_v1(value: object, label: str) -> tuple[float, str]:
    try:
        return _finite_v1(value, label), ""
    except ValueError as exc:
        return math.nan, str(exc)


def _finite_v1(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be numeric") from None
    if not math.isfinite(number) or number <= -273.15:
        raise ValueError(f"{label} must be finite and above absolute zero")
    return number


def _canonical_text_v1(value: object) -> str:
    return value if isinstance(value, str) and value and value == value.strip() else ""


def _blocked_v1(
        *blockers: str,
) -> CommittedPipeSectionAmbientTaiRuntimeHandoffV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedPipeSectionAmbientTaiRuntimeHandoffV1(
        ready=False,
        sections=(),
        section_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
