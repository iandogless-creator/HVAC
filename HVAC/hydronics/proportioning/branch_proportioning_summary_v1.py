# ======================================================================
# HVAC/hydronics/proportioning/branch_proportioning_summary_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

CP_WATER_J_KG_K = 4180.0
# ======================================================================
# DTO
# ======================================================================

@dataclass(frozen=True, slots=True)
class BranchProportioningRowV1:
    """
    Read-only hydronic branch/proportioning projection row.

    Authority
    ---------
    This is display/projection only.

    It does not:
    • mutate ProjectState
    • size pipework
    • calculate pressure loss
    • select pumps
    • balance branches
    • infer manufacturer emitter data
    """

    group: str
    role: str
    from_label: str
    to_label: str
    flow_label: str
    basis: str
    status: str


# ======================================================================
# Public builder
# ======================================================================

def build_branch_proportioning_summary_v1(project_state: Any) -> List[BranchProportioningRowV1]:
    """
    Build a read-only branch/proportioning summary.

    H-R1 scope:
    • selected index route
    • non-index branch terminals
    • common/main
    • no-emitter / unresolved rooms

    This intentionally avoids full hydraulic calculation.
    """

    rooms = getattr(project_state, "rooms", {}) or {}
    emitters = getattr(project_state, "emitters", {}) or {}

    rows: List[BranchProportioningRowV1] = []

    room_ids_with_emitters = _room_ids_with_emitters(emitters)

    # --------------------------------------------------
    # Selected index route
    # --------------------------------------------------
    # --------------------------------------------------
    # Selected index route
    # --------------------------------------------------
    index_route_room_ids = _resolve_index_route_room_ids(project_state)
    heat_source_room_id = _resolve_heat_source_room_id(project_state)

    if index_route_room_ids:
        index_leg_flow_map = _index_route_leg_flow_map(project_state)

        for from_room_id, to_room_id in zip(index_route_room_ids[:-1], index_route_room_ids[1:]):
            rows.append(
                BranchProportioningRowV1(
                    group="Selected index route",
                    role="Index route leg",
                    from_label=_room_label(rooms, from_room_id),
                    to_label=_room_label(rooms, to_room_id),
                    flow_label=_format_flow_kg_s(
                        index_leg_flow_map.get((str(from_room_id), str(to_room_id)))
                    ),
                    basis="Current index-route accumulator",
                    status="Projection only",
                )
            )
    else:
        rows.append(
            BranchProportioningRowV1(
                group="Selected index route",
                role="Index route",
                from_label="—",
                to_label="—",
                flow_label="—",
                basis="No explicit index route resolved",
                status="Unresolved",
            )
        )

    index_route_set = set(index_route_room_ids)

    # --------------------------------------------------
    # Non-index branch terminals
    # --------------------------------------------------
    # --------------------------------------------------
    # Non-index branch terminals
    # --------------------------------------------------
    for room_id in sorted(room_ids_with_emitters):
        if room_id in index_route_set:
            continue

        if heat_source_room_id and room_id == heat_source_room_id:
            continue

        rows.append(
            BranchProportioningRowV1(
                group="Common-side route",
                role="Common-side route node",
                from_label=_room_label(rooms, room_id),
                to_label="Selected route entry",
                flow_label=_room_flow_label(emitters, room_id),
                basis="Emitter demand before selected route",
                status="Projection only",
            )
        )

    # --------------------------------------------------
    # Common/main
    # --------------------------------------------------
    rows.append(
        BranchProportioningRowV1(
            group="Common/main",
            role="Common main",
            from_label="Boiler / Heat Source",
            to_label="Common main / first branch",
            flow_label=_total_flow_label(emitters),
            basis="Sum of active emitter design flows where available",
            status="Projection only",
        )
    )

    # --------------------------------------------------
    # No-emitter / unresolved
    # --------------------------------------------------
    for room_id in sorted(rooms.keys()):
        if room_id in room_ids_with_emitters:
            continue

        rows.append(
            BranchProportioningRowV1(
                group="No-emitter / unresolved",
                role="No emitter",
                from_label=_room_label(rooms, room_id),
                to_label="—",
                flow_label="—",
                basis="No emitter assigned to room",
                status="No branch terminal flow",
            )
        )

    return rows


# ======================================================================
# Helpers
# ======================================================================

def _room_ids_with_emitters(emitters: dict) -> set[str]:
    out: set[str] = set()

    for emitter in emitters.values():
        room_id = getattr(emitter, "room_id", None)
        if room_id:
            out.add(str(room_id))

    return out

def _resolve_heat_source_room_id(project_state: Any) -> Optional[str]:
    """
    Resolve the current boiler / heat-source room.

    DEV fallback:
    • reuse the existing basic index-route accumulator plant_room_id
    • in the current DEV project this is R1

    Meaning:
    • this is the room/enclosure containing the boiler or heat source
    • the user-facing room name may be Kitchen, Cupboard, Garage,
      Utility, Plant Room, etc.
    • do not infer this role from the room label

    Future authority:
    • project.hydronics.heat_source_room_id or equivalent
    """
    try:
        from HVAC.hydronics.routing.index_route_accumulator_v1 import (
            build_index_route_accumulator_v1,
        )

        route = build_index_route_accumulator_v1(project_state)
        heat_source_room_id = getattr(route, "plant_room_id", None)

        if heat_source_room_id:
            return str(heat_source_room_id)

    except Exception:
        pass

    return None

def _room_label(rooms: dict, room_id: str) -> str:
    room = rooms.get(room_id)

    if room is None:
        return str(room_id)

    name = (
        getattr(room, "name", None)
        or getattr(room, "room_name", None)
        or getattr(room, "label", None)
        or str(room_id)
    )

    return str(name)


def _resolve_index_route_room_ids(project_state: Any) -> List[str]:
    """
    Resolve the current selected index route.

    H-R1 rule:
    • Prefer the existing H-Q index-route accumulator.
    • Do not invent multiple visible index routes.
    • Keep this projection read-only.
    """

    # --------------------------------------------------
    # Preferred: reuse existing H-Q route accumulator
    # --------------------------------------------------
    try:
        from HVAC.hydronics.routing.index_route_accumulator_v1 import (
            build_index_route_accumulator_v1,
        )

        route = build_index_route_accumulator_v1(project_state)
        sections = list(getattr(route, "sections", []) or [])

        room_ids: list[str] = []

        for section in sections:
            from_room_id = getattr(section, "from_room_id", None)
            to_room_id = getattr(section, "to_room_id", None)

            if from_room_id and not room_ids:
                room_ids.append(str(from_room_id))

            if to_room_id:
                to_room_id = str(to_room_id)
                if not room_ids or room_ids[-1] != to_room_id:
                    room_ids.append(to_room_id)

        if room_ids:
            heat_source_room_id = getattr(route, "plant_room_id", None)

            if heat_source_room_id:
                room_ids = [
                    room_id
                    for room_id in room_ids
                    if room_id != str(heat_source_room_id)
                ]

            return room_ids

    except Exception:
        # H-R1 projection must not crash the GUI/backend if the existing
        # accumulator is unavailable during development.
        pass

    # --------------------------------------------------
    # Explicit future/project intent fallback
    # --------------------------------------------------
    explicit = getattr(project_state, "hydronic_index_route_room_ids", None)
    if explicit:
        return [str(x) for x in explicit]

    hydronics = getattr(project_state, "hydronics", None)
    explicit = getattr(hydronics, "index_route_room_ids", None) if hydronics is not None else None
    if explicit:
        return [str(x) for x in explicit]

    # --------------------------------------------------
    # Last-resort DEV fallback
    # --------------------------------------------------
    rooms = getattr(project_state, "rooms", {}) or {}

    # Keep the known 6-room DEV bathroom out of the selected route.
    # This is a fallback only; normal operation should come from the
    # index-route accumulator above.
    room_ids = list(reversed(list(rooms.keys())))
    return [room_id for room_id in room_ids if room_id != "room-006"]

def _room_flow_label(emitters: dict, room_id: str) -> str:
    total = 0.0
    found = False

    for emitter in emitters.values():
        if getattr(emitter, "room_id", None) != room_id:
            continue

        value = _emitter_flow_kg_s(emitter)
        if value is None:
            continue

        total += value
        found = True

    if not found:
        return "—"

    return f"{total:.4f} kg/s"


def _total_flow_label(emitters: dict) -> str:
    total = 0.0
    found = False

    for emitter in emitters.values():
        value = _emitter_flow_kg_s(emitter)
        if value is None:
            continue

        total += value
        found = True

    if not found:
        return "—"

    return f"{total:.4f} kg/s"


def _emitter_flow_kg_s(emitter: Any) -> Optional[float]:
    """
    Resolve projected emitter mass flow in kg/s.

    H-R1 display basis:
    • If a mass-flow field exists, use it.
    • Otherwise derive from emitter output and water ΔT.

    This is still projection only:
    • no pipe sizing
    • no pressure loss
    • no pump selection
    • no balancing
    """

    for attr in (
        "design_mass_flow_kg_s",
        "mass_flow_kg_s",
        "flow_kg_s",
        "design_flow_kg_s",
    ):
        value = getattr(emitter, attr, None)
        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    output_W = getattr(emitter, "design_output_W", None)
    flow_temp_C = getattr(emitter, "flow_temp_C", None)
    return_temp_C = getattr(emitter, "return_temp_C", None)

    if output_W is None or flow_temp_C is None or return_temp_C is None:
        return None

    try:
        output = float(output_W)
        delta_t = float(flow_temp_C) - float(return_temp_C)
    except (TypeError, ValueError):
        return None

    if output <= 0.0 or delta_t <= 0.0:
        return None

    return output / (CP_WATER_J_KG_K * delta_t)

def _index_route_leg_flow_map(project_state: Any) -> dict[tuple[str, str], Optional[float]]:
    """
    Return accumulated index-route flow by route leg.

    Read-only projection helper.

    Preferred:
    • use existing index-route accumulator section flow

    Fallback:
    • derive accumulated route flow from EmitterV1 design_output_W
      and water ΔT for the section's included rooms.

    This keeps H-R1 independent and avoids changing H-Q/H-N behaviour.
    """

    out: dict[tuple[str, str], Optional[float]] = {}

    try:
        from HVAC.hydronics.routing.index_route_accumulator_v1 import (
            build_index_route_accumulator_v1,
        )

        route = build_index_route_accumulator_v1(project_state)
        sections = list(getattr(route, "sections", []) or [])

        for section in sections:
            from_room_id = getattr(section, "from_room_id", None)
            to_room_id = getattr(section, "to_room_id", None)

            if not from_room_id or not to_room_id:
                continue

            flow = getattr(section, "accumulated_mass_flow_kg_s", None)

            try:
                flow_value = None if flow is None else float(flow)
            except (TypeError, ValueError):
                flow_value = None

            if flow_value is None:
                included_room_ids = getattr(section, "included_room_ids", tuple()) or tuple()
                flow_value = _accumulated_flow_for_room_ids(
                    project_state=project_state,
                    room_ids=included_room_ids,
                )

            out[(str(from_room_id), str(to_room_id))] = flow_value

    except Exception:
        return {}

    return out

def _accumulated_flow_for_room_ids(
    *,
    project_state: Any,
    room_ids: Iterable[str],
) -> Optional[float]:
    emitters = getattr(project_state, "emitters", {}) or {}
    wanted = {str(room_id) for room_id in room_ids}

    total = 0.0
    found = False

    for emitter in emitters.values():
        room_id = getattr(emitter, "room_id", None)

        if room_id is None or str(room_id) not in wanted:
            continue

        flow = _emitter_flow_kg_s(emitter)

        if flow is None:
            continue

        total += float(flow)
        found = True

    return total if found else None

def _format_flow_kg_s(value: Optional[float]) -> str:
    if value is None:
        return "—"

    try:
        flow = float(value)
    except (TypeError, ValueError):
        return "—"

    return f"{flow:.4f} kg/s"