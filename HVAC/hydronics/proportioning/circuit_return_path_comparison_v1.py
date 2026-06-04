# HVAC/hydronics/proportioning/circuit_return_path_comparison_v1.py
#
# H-S19-A — Direct return vs reverse return circuit comparison
#
# Preview-only:
# - no balancing valve settings
# - no pump selection
# - no pipe resizing
# - no final system commit

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
)
from HVAC.hydronics.local_losses.local_k_pressure_preview_v1 import (
    build_local_k_pressure_preview_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    build_route_pressure_accumulator_v1,
)

@dataclass(frozen=True, slots=True)
class CircuitReturnPathComparisonRowV1:
    room_id: str
    emitter_id: str
    route_id: str
    route_label: str

    flow_section_ids: tuple[str, ...]
    direct_return_section_ids: tuple[str, ...]
    reverse_return_section_ids: tuple[str, ...]

    rr_suitability_code: str
    rr_suitability_status: str

    flow_dp_Pa: float | None
    direct_return_dp_Pa: float | None
    reverse_return_dp_Pa: float | None

    direct_total_dp_Pa: float | None
    reverse_return_total_dp_Pa: float | None

    direct_rank: int | None
    reverse_return_rank: int | None

    controlling_direct: bool
    controlling_reverse_return: bool

    status: str

@dataclass(frozen=True, slots=True)
class ReverseReturnSuitabilityV1:
    suitable: bool
    code: str
    status: str

@dataclass(frozen=True, slots=True)
class CircuitReturnPathComparisonProjectionV1:
    rows: tuple[CircuitReturnPathComparisonRowV1, ...]
    status: str = "Circuit return path comparison preview only"


def build_circuit_return_path_comparison_v1(
    project_state: Any,
) -> CircuitReturnPathComparisonProjectionV1:
    """
    H-S19-A shell.

    Future purpose:
    Compare each circuit/emitter under:
        F + R   direct return
        F + RR  reverse return

    Current shell deliberately does not invent return paths yet.
    It only confirms that topology/emitter traversal can produce
    comparison rows for future pressure calculations.
    """

    topology = getattr(project_state, "hydronic_topology", None)
    emitters = getattr(project_state, "emitters", {}) or {}

    if topology is None:
        return CircuitReturnPathComparisonProjectionV1(
            rows=(),
            status="No hydronic topology — cannot compare return paths",
        )

    rows: list[CircuitReturnPathComparisonRowV1] = []

    for leg in getattr(topology, "legs", []) or []:
        leg_id = str(getattr(leg, "leg_id", "") or "")

        for subleg in getattr(leg, "sublegs", []) or []:
            subleg_id = str(getattr(subleg, "subleg_id", "") or "")
            subleg_label = str(
                getattr(subleg, "label", None)
                or getattr(subleg, "name", None)
                or subleg_id
            )

            room_ids = _subleg_room_ids(subleg)

            flow_sections_by_room = _flow_section_ids_by_room(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            reverse_return_sections_by_room = _reverse_return_section_ids_by_room(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            section_dp_by_id = _section_total_dp_by_id(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            rr_suitability = _appraise_reverse_return_suitability_v1(
                subleg,
                room_ids=room_ids,
            )

            for room_id in room_ids:
                flow_section_ids = flow_sections_by_room.get(
                    str(room_id),
                    (),
                )

                direct_return_section_ids = tuple(
                    reversed(flow_section_ids)
                )

                reverse_return_section_ids = (
                    reverse_return_sections_by_room.get(str(room_id), ())
                    if rr_suitability.code == "ordered-subleg"
                    else ()
                )

                flow_dp_Pa = _sum_section_dp(
                    section_dp_by_id,
                    flow_section_ids,
                )

                direct_return_dp_Pa = _sum_section_dp(
                    section_dp_by_id,
                    direct_return_section_ids,
                )

                reverse_return_dp_Pa = _sum_section_dp(
                    section_dp_by_id,
                    reverse_return_section_ids,
                )

                direct_total_dp_Pa = _add_optional_dp(
                    flow_dp_Pa,
                    direct_return_dp_Pa,
                )

                reverse_return_total_dp_Pa = _add_optional_dp(
                    flow_dp_Pa,
                    reverse_return_dp_Pa,
                )

                emitter_id = _find_emitter_id_for_room(
                    emitters,
                    room_id=str(room_id),
                )

                rows.append(
                    CircuitReturnPathComparisonRowV1(
                        room_id=str(room_id),
                        emitter_id=emitter_id,
                        route_id=f"{leg_id}:{subleg_id}",
                        route_label=subleg_label,
                        flow_section_ids=flow_section_ids,
                        direct_return_section_ids=direct_return_section_ids,
                        reverse_return_section_ids=reverse_return_section_ids,
                        flow_dp_Pa=flow_dp_Pa,
                        direct_return_dp_Pa=direct_return_dp_Pa,
                        reverse_return_dp_Pa=reverse_return_dp_Pa,
                        direct_total_dp_Pa=direct_total_dp_Pa,
                        reverse_return_total_dp_Pa=reverse_return_total_dp_Pa,
                        direct_rank=None,
                        reverse_return_rank=None,
                        rr_suitability_code=rr_suitability.code,
                        rr_suitability_status=rr_suitability.status,
                        controlling_direct=False,
                        controlling_reverse_return=False,
                        status=(
                            "Flow + direct + reverse return paths ready"
                            if reverse_return_section_ids
                            else (
                                "Flow + direct return path ready — reverse return not generated"
                                if flow_section_ids
                                else "Missing flow path — return paths not modelled yet"
                            )
                        ),
                    )
                )

    ranked_rows = _rank_circuit_pressure_totals_v1(tuple(rows))

    return CircuitReturnPathComparisonProjectionV1(
        rows=ranked_rows,
        status=(
            "Circuit return path comparison ready"
            if ranked_rows
            else "No room-carrying hydronic circuits found"
        ),
    )


def _find_emitter_id_for_room(
    emitters: dict,
    *,
    room_id: str,
) -> str:
    for emitter_key, emitter in emitters.items():
        candidate_room_id = str(getattr(emitter, "room_id", "") or "")

        if candidate_room_id == room_id:
            return str(getattr(emitter, "emitter_id", "") or emitter_key)

    return ""

def _flow_section_ids_by_room(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, tuple[str, ...]]:
    """
    Build flow-side section paths for each room in a subleg.

    For a subleg route:
        room-001 -> section-001
        room-002 -> section-001, section-002
        room-003 -> section-001, section-002, section-003

    This is the F path only.
    Direct return and reverse return paths are deliberately deferred.
    """
    try:
        projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    sections = sorted(
        tuple(getattr(projection, "sections", ()) or ()),
        key=lambda section: int(getattr(section, "order", 0) or 0),
    )

    result: dict[str, tuple[str, ...]] = {}
    accumulated: list[str] = []

    for section in sections:
        section_id = str(getattr(section, "section_id", "") or "")
        to_room_id = str(getattr(section, "to_room_id", "") or "")

        if not section_id or not to_room_id:
            continue

        accumulated.append(section_id)
        result[to_room_id] = tuple(accumulated)

    return result

def _subleg_room_ids(subleg: Any) -> tuple[str, ...]:
    """
    Return room ids carried by a hydronic subleg.

    Current HydronicSublegV1 uses route_room_ids.
    Other names are tolerated to keep the projection resilient
    while topology DTOs settle.
    """
    for field_name in (
        "route_room_ids",
        "room_ids",
        "rooms",
        "room_sequence",
        "terminal_room_ids",
    ):
        value = getattr(subleg, field_name, None)

        if not value:
            continue

        result: list[str] = []

        for item in value:
            if isinstance(item, str):
                result.append(item)
            else:
                room_id = (
                    getattr(item, "room_id", None)
                    or getattr(item, "id", None)
                )
                if room_id:
                    result.append(str(room_id))

        if result:
            return tuple(result)

    return ()

def _appraise_reverse_return_suitability_v1(
    subleg: Any,
    *,
    room_ids: tuple[str, ...],
) -> ReverseReturnSuitabilityV1:
    """
    H-S19-D:
    Appraise whether reverse return is suitable for this ordered group.

    This does not generate reverse-return paths.
    It only classifies whether RR comparison is meaningful.

    v1 principle:
    - reverse return is valid for an appraised ordered group;
    - nested sublegs/branches are not automatically rejected;
    - nested/grouped routes require separate appraisal unless explicitly handled.
    """
    if len(room_ids) < 2:
        return ReverseReturnSuitabilityV1(
            suitable=False,
            code="single-emitter-not-useful",
            status="RR unavailable — single emitter group",
        )

    nested_sublegs = tuple(getattr(subleg, "sublegs", ()) or ())

    if nested_sublegs:
        return ReverseReturnSuitabilityV1(
            suitable=False,
            code="nested-subleg-requires-separate-appraisal",
            status="RR requires appraisal — nested subleg/grouped route",
        )

    return ReverseReturnSuitabilityV1(
        suitable=True,
        code="ordered-subleg",
        status="RR comparable — ordered subleg",
    )

def _reverse_return_section_ids_by_room(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, tuple[str, ...]]:
    """
    Build provisional reverse-return section paths for each room.

    For an ordered subleg route:
        room-001 -> section-001, section-002, section-003
        room-002 -> section-002, section-003
        room-003 -> section-003

    This is only a path-ID comparison scaffold.
    It does not yet create separate physical return pipe DTOs.
    It must only be used after RR suitability appraisal says the group is comparable.
    """
    try:
        projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    sections = sorted(
        tuple(getattr(projection, "sections", ()) or ()),
        key=lambda section: int(getattr(section, "order", 0) or 0),
    )

    result: dict[str, tuple[str, ...]] = {}

    for index, section in enumerate(sections):
        to_room_id = str(getattr(section, "to_room_id", "") or "")

        if not to_room_id:
            continue

        result[to_room_id] = tuple(
            str(getattr(item, "section_id", "") or "")
            for item in sections[index:]
            if str(getattr(item, "section_id", "") or "")
        )

    return result

def _section_total_dp_by_id(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, float | None]:
    """
    Build section_id -> section total Δp lookup.

    Uses the existing H-S17 route pressure accumulator because it already
    composes Basic PS + Local K pressure preview into per-section totals.

    Preview-only.
    """
    try:
        projection = build_route_pressure_accumulator_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    result: dict[str, float | None] = {}

    for route_row in getattr(projection, "rows", ()) or ():
        for section in getattr(route_row, "sections", ()) or ():
            section_id = str(getattr(section, "section_id", "") or "")

            if not section_id:
                continue

            value = getattr(section, "section_total_pressure_drop_Pa", None)

            if value is None:
                result[section_id] = None
                continue

            try:
                result[section_id] = float(value)
            except (TypeError, ValueError):
                result[section_id] = None

    return result

def _sum_section_dp(
        section_dp_by_id: dict[str, float | None],
        section_ids: tuple[str, ...],
) -> float | None:
    """
    Sum section Δp values for a path.

    Returns None if any required section Δp is missing.
    """
    total = 0.0

    for section_id in section_ids:
        value = section_dp_by_id.get(section_id)

        if value is None:
            return None

        total += float(value)

    return total

def _add_optional_dp(
        first: float | None,
        second: float | None,
) -> float | None:
    if first is None or second is None:
        return None

    return float(first) + float(second)

def _rank_circuit_pressure_totals_v1(
    rows: tuple[CircuitReturnPathComparisonRowV1, ...],
) -> tuple[CircuitReturnPathComparisonRowV1, ...]:
    """
    Rank direct-return and reverse-return circuit totals separately.

    Controlling circuit = highest total pressure drop.

    Preview-only:
    - no balancing
    - no valve authority
    - no pump selection
    - no committed return arrangement
    """
    direct_rank_by_key = _rank_rows_by_total_dp(
        rows,
        total_attr="direct_total_dp_Pa",
    )

    reverse_rank_by_key = _rank_rows_by_total_dp(
        rows,
        total_attr="reverse_return_total_dp_Pa",
    )

    ranked: list[CircuitReturnPathComparisonRowV1] = []

    for row in rows:
        row_key = _circuit_row_key(row)

        direct_rank = direct_rank_by_key.get(row_key)
        reverse_rank = reverse_rank_by_key.get(row_key)

        ranked.append(
            replace(
                row,
                direct_rank=direct_rank,
                reverse_return_rank=reverse_rank,
                controlling_direct=(direct_rank == 1),
                controlling_reverse_return=(reverse_rank == 1),
            )
        )

    return tuple(ranked)


def _rank_rows_by_total_dp(
    rows: tuple[CircuitReturnPathComparisonRowV1, ...],
    *,
    total_attr: str,
) -> dict[str, int]:
    complete_rows = [
        row
        for row in rows
        if getattr(row, total_attr, None) is not None
    ]

    sorted_rows = sorted(
        complete_rows,
        key=lambda row: float(getattr(row, total_attr) or 0.0),
        reverse=True,
    )

    return {
        _circuit_row_key(row): rank
        for rank, row in enumerate(sorted_rows, start=1)
    }


def _circuit_row_key(row: CircuitReturnPathComparisonRowV1) -> str:
    return "|".join(
        (
            str(row.route_id),
            str(row.room_id),
            str(row.emitter_id),
        )
    )