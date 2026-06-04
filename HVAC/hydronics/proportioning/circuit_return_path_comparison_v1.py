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

from dataclasses import dataclass
from typing import Any
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
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

            for room_id in room_ids:
                flow_section_ids = flow_sections_by_room.get(
                    str(room_id),
                    (),
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
                        direct_return_section_ids=(),
                        reverse_return_section_ids=(),
                        flow_dp_Pa=None,
                        direct_return_dp_Pa=None,
                        reverse_return_dp_Pa=None,
                        direct_total_dp_Pa=None,
                        reverse_return_total_dp_Pa=None,
                        direct_rank=None,
                        reverse_return_rank=None,
                        controlling_direct=False,
                        controlling_reverse_return=False,
                        status=(
                            "Flow path ready — return paths not modelled yet"
                            if flow_section_ids
                            else "Missing flow path — return paths not modelled yet"
                        ),
                    )
                )

    return CircuitReturnPathComparisonProjectionV1(
        rows=tuple(rows),
        status=(
            "Circuit return path comparison shell ready"
            if rows
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