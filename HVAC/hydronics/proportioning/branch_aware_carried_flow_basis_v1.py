# ======================================================================
# HVAC/hydronics/proportioning/branch_aware_carried_flow_basis_v1.py
# H-S24-C — Branch-aware carried-flow basis
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from HVAC.hydronics.design_conditions.hydronic_design_temperature_basis_v1 import (
    resolve_hydronic_design_temperature_basis_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)


CP_WATER_J_KG_K = 4180.0


@dataclass(frozen=True, slots=True)
class BranchAwareCarriedFlowSectionRowV1:
    """
    Branch-aware carried-flow section basis.

    This is a topology/flow-basis projection only.

    It does not:
    • size pipes
    • calculate pressure drop
    • select valves
    • select pumps
    • commit balancing
    • mutate ProjectState
    """

    leg_id: str
    leg_label: str

    subleg_id: str
    subleg_label: str
    subleg_kind: str
    parent_subleg_id: str

    section_id: str
    order: int
    from_label: str
    to_room_id: str
    to_room_label: str

    own_downstream_room_ids: tuple[str, ...]
    rolled_up_subleg_ids: tuple[str, ...]
    rolled_up_room_ids: tuple[str, ...]
    carried_room_ids: tuple[str, ...]

    own_heat_W: float
    rolled_up_heat_W: float
    carried_heat_W: float

    own_flow_kg_s: float | None
    rolled_up_flow_kg_s: float | None
    carried_flow_kg_s: float | None

    status: str


@dataclass(frozen=True, slots=True)
class BranchAwareCarriedFlowBasisV1:
    """
    Preview-only branch-aware carried-flow basis.
    """

    ready: bool = False
    status: str = "Branch-aware carried-flow basis not ready"
    rows: tuple[BranchAwareCarriedFlowSectionRowV1, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _SublegInfo:
    leg: HydronicLegV1
    subleg: HydronicSublegV1
    parent_subleg_id: str


def _room_label(project_state: Any, room_id: str) -> str:
    room = (getattr(project_state, "rooms", {}) or {}).get(room_id)
    if room is None:
        return room_id

    return str(
        getattr(room, "name", None)
        or getattr(room, "room_name", None)
        or getattr(room, "label", None)
        or room_id
    )


def _direct_emitter_flow_kg_s(emitter: Any) -> float | None:
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
            flow = float(value)
        except (TypeError, ValueError):
            continue

        if flow > 0.0:
            return flow

    return None


def _emitter_output_W(emitter: Any) -> float:
    value = getattr(emitter, "design_output_W", None)

    try:
        output = float(value)
    except (TypeError, ValueError):
        return 0.0

    return output if output > 0.0 else 0.0


def _emitter_legacy_delta_t_K(emitter: Any) -> float | None:
    flow_temp = getattr(emitter, "flow_temp_C", None)
    return_temp = getattr(emitter, "return_temp_C", None)

    try:
        delta_t = float(flow_temp) - float(return_temp)
    except (TypeError, ValueError):
        return None

    return delta_t if delta_t > 0.0 else None


def _room_heat_W(project_state: Any, room_id: str) -> float:
    total = 0.0

    for emitter in (getattr(project_state, "emitters", {}) or {}).values():
        if str(getattr(emitter, "room_id", "") or "") != str(room_id):
            continue

        total += _emitter_output_W(emitter)

    return total


def _room_flow_kg_s(project_state: Any, room_id: str) -> float | None:
    """
    Resolve room emitter flow for carried-flow preview.

    Precedence:
    1. explicit emitter mass-flow fields
    2. Environment ΔT and design_output_W
    3. legacy emitter flow/return fallback
    """

    basis = resolve_hydronic_design_temperature_basis_v1(project_state)
    environment_delta_t = basis.delta_t_k

    total = 0.0
    found = False

    for emitter in (getattr(project_state, "emitters", {}) or {}).values():
        if str(getattr(emitter, "room_id", "") or "") != str(room_id):
            continue

        direct_flow = _direct_emitter_flow_kg_s(emitter)
        if direct_flow is not None:
            total += direct_flow
            found = True
            continue

        output = _emitter_output_W(emitter)
        if output <= 0.0:
            continue

        delta_t = environment_delta_t
        if delta_t is None:
            delta_t = _emitter_legacy_delta_t_K(emitter)

        if delta_t is None or delta_t <= 0.0:
            continue

        total += output / (CP_WATER_J_KG_K * delta_t)
        found = True

    return total if found else None


def _rooms_heat_W(project_state: Any, room_ids: tuple[str, ...]) -> float:
    return sum(_room_heat_W(project_state, room_id) for room_id in room_ids)


def _rooms_flow_kg_s(
    project_state: Any,
    room_ids: tuple[str, ...],
) -> float | None:
    total = 0.0
    found = False

    for room_id in room_ids:
        value = _room_flow_kg_s(project_state, room_id)
        if value is None:
            continue

        total += value
        found = True

    return total if found else None


def _flatten_leg_sublegs(leg: HydronicLegV1) -> list[_SublegInfo]:
    """
    Flatten leg sublegs and infer top-level non-primary sublegs as children
    of the primary subleg where possible.

    This keeps existing DEV topologies usable where branch sublegs may be
    stored as siblings rather than nested children.
    """

    primary_id = primary_subleg_id_for_leg(leg.leg_id)
    has_primary = any(subleg.subleg_id == primary_id for subleg in leg.sublegs)

    out: list[_SublegInfo] = []

    def walk(subleg: HydronicSublegV1, parent_subleg_id: str) -> None:
        out.append(
            _SublegInfo(
                leg=leg,
                subleg=subleg,
                parent_subleg_id=parent_subleg_id,
            )
        )

        for child in subleg.sublegs:
            walk(child, subleg.subleg_id)

    for subleg in leg.sublegs:
        if subleg.subleg_id == primary_id:
            parent = ""
        elif has_primary:
            parent = primary_id
        else:
            parent = ""

        walk(subleg, parent)

    return out


def _subleg_total_room_ids(
    *,
    subleg_id: str,
    sublegs_by_id: dict[str, HydronicSublegV1],
    children_by_parent: dict[str, list[str]],
) -> tuple[str, ...]:
    subleg = sublegs_by_id[subleg_id]
    room_ids: list[str] = [str(room_id) for room_id in subleg.route_room_ids]

    for child_id in children_by_parent.get(subleg_id, []):
        room_ids.extend(
            _subleg_total_room_ids(
                subleg_id=child_id,
                sublegs_by_id=sublegs_by_id,
                children_by_parent=children_by_parent,
            )
        )

    return tuple(room_ids)


def _takeoff_position_classification(
    *,
    parent_rooms: list[str],
    origin_room_id: str,
) -> str:
    """
    Classify a child subleg origin within its parent route.

    H-S24-D:
    This is descriptive classification only. It does not change carried-flow
    maths.
    """

    if not origin_room_id or origin_room_id not in parent_rooms:
        return "unresolved_takeoff"

    origin_index = parent_rooms.index(origin_room_id)
    terminal_index = len(parent_rooms) - 1

    if origin_index == terminal_index:
        return "terminal_continuation"

    if origin_index == 0:
        return "early_takeoff"

    if origin_index == terminal_index - 1:
        return "late_terminal_takeoff"

    return "true_branch_takeoff"


def _takeoff_classification_label(classification: str) -> str:
    if classification == "early_takeoff":
        return "Early take-off / riser-capable branch"

    if classification == "late_terminal_takeoff":
        return "Late take-off — parent downstream terminal emitter only"

    if classification == "terminal_continuation":
        return "Continuation from parent terminal"

    if classification == "unresolved_takeoff":
        return "Branch take-off unresolved — origin not in parent route"

    return "Branch roll-up to take-off"


def _child_rollup_for_section(
    *,
    parent_rooms: list[str],
    section_index: int,
    child: HydronicSublegV1,
    child_total_room_ids: tuple[str, ...],
) -> tuple[bool, str]:
    """
    Decide whether a child subleg contributes to this parent section.

    Rule:
    - true branch: origin is before parent terminal, contributes up to take-off
    - continuation: origin is parent terminal, contributes through all parent
      sections to the terminal, but should be labelled as continuation
    - unresolved: origin not found, do not add to section
    """

    origin_room_id = str(child.origin_room_id or "").strip()

    classification = _takeoff_position_classification(
        parent_rooms=parent_rooms,
        origin_room_id=origin_room_id,
    )

    if classification == "unresolved_takeoff":
        return False, _takeoff_classification_label(classification)

    origin_index = parent_rooms.index(origin_room_id)

    if classification == "terminal_continuation":
        if section_index <= origin_index:
            return True, _takeoff_classification_label(classification)
        return False, "Continuation after parent terminal"

    if section_index <= origin_index:
        return True, _takeoff_classification_label(classification)

    return False, "Downstream of branch take-off"


def _subleg_kind(
    *,
    leg: HydronicLegV1,
    subleg: HydronicSublegV1,
    parent_subleg_id: str,
    sublegs_by_id: dict[str, HydronicSublegV1],
) -> str:
    primary_id = primary_subleg_id_for_leg(leg.leg_id)

    if subleg.subleg_id == primary_id:
        return "primary/common subleg"

    parent = sublegs_by_id.get(parent_subleg_id)
    if parent is not None:
        parent_rooms = list(parent.route_room_ids)
        origin = str(subleg.origin_room_id or "").strip()
        classification = _takeoff_position_classification(
            parent_rooms=parent_rooms,
            origin_room_id=origin,
        )

        if classification == "terminal_continuation":
            return "continuation subleg"

    if parent_subleg_id:
        return "branch subleg"

    return "subleg"


def build_branch_aware_carried_flow_basis_v1(
    project_state: Any,
) -> BranchAwareCarriedFlowBasisV1:
    """
    Build H-S24-C branch-aware carried-flow basis.

    This makes branch/continuation room allocation visible before route
    pressure or balancing duty figures are trusted.
    """

    if project_state is None:
        return BranchAwareCarriedFlowBasisV1(
            ready=False,
            blockers=("No project_state is available",),
        )

    topology = getattr(project_state, "hydronic_topology", None)

    if topology is None:
        return BranchAwareCarriedFlowBasisV1(
            ready=False,
            blockers=("No hydronic topology is available",),
        )

    if not isinstance(topology, HydronicTopologyV1):
        return BranchAwareCarriedFlowBasisV1(
            ready=False,
            blockers=("project_state.hydronic_topology is not HydronicTopologyV1",),
        )

    infos: list[_SublegInfo] = []
    for leg in topology.legs:
        infos.extend(_flatten_leg_sublegs(leg))

    sublegs_by_id = {
        info.subleg.subleg_id: info.subleg
        for info in infos
    }

    children_by_parent: dict[str, list[str]] = {}
    for info in infos:
        if not info.parent_subleg_id:
            continue

        children_by_parent.setdefault(info.parent_subleg_id, []).append(
            info.subleg.subleg_id
        )

    rows: list[BranchAwareCarriedFlowSectionRowV1] = []
    blockers: list[str] = []

    for info in infos:
        leg = info.leg
        subleg = info.subleg
        parent_subleg_id = info.parent_subleg_id
        parent_rooms = [str(room_id) for room_id in subleg.route_room_ids]

        kind = _subleg_kind(
            leg=leg,
            subleg=subleg,
            parent_subleg_id=parent_subleg_id,
            sublegs_by_id=sublegs_by_id,
        )

        if not parent_rooms:
            blockers.append(f"{subleg.label}: no rooms allocated")
            continue

        for index, to_room_id in enumerate(parent_rooms):
            order = index + 1

            if index == 0:
                from_label = (
                    "Common main / leg entry"
                    if kind == "primary/common subleg"
                    else f"Take-off from {subleg.origin_room_id or 'TBD'}"
                )
            else:
                from_label = _room_label(project_state, parent_rooms[index - 1])

            own_downstream_room_ids = tuple(parent_rooms[index:])

            rolled_up_subleg_ids: list[str] = []
            rolled_up_room_ids: list[str] = []
            rollup_statuses: list[str] = []

            for child_id in children_by_parent.get(subleg.subleg_id, []):
                child = sublegs_by_id[child_id]
                child_total_rooms = _subleg_total_room_ids(
                    subleg_id=child_id,
                    sublegs_by_id=sublegs_by_id,
                    children_by_parent=children_by_parent,
                )

                include_child, rollup_status = _child_rollup_for_section(
                    parent_rooms=parent_rooms,
                    section_index=index,
                    child=child,
                    child_total_room_ids=child_total_rooms,
                )

                if include_child:
                    rolled_up_subleg_ids.append(child_id)
                    rolled_up_room_ids.extend(child_total_rooms)

                rollup_statuses.append(f"{child_id}: {rollup_status}")

            carried_room_ids = tuple(
                list(own_downstream_room_ids) + rolled_up_room_ids
            )

            own_heat = _rooms_heat_W(project_state, own_downstream_room_ids)
            rolled_up_heat = _rooms_heat_W(
                project_state,
                tuple(rolled_up_room_ids),
            )
            carried_heat = own_heat + rolled_up_heat

            own_flow = _rooms_flow_kg_s(project_state, own_downstream_room_ids)
            rolled_up_flow = _rooms_flow_kg_s(
                project_state,
                tuple(rolled_up_room_ids),
            )

            if own_flow is None and rolled_up_flow is None:
                carried_flow = None
            else:
                carried_flow = (own_flow or 0.0) + (rolled_up_flow or 0.0)

            if not rollup_statuses:
                status = "Carried-flow basis ready"
            else:
                status = "; ".join(rollup_statuses)

            rows.append(
                BranchAwareCarriedFlowSectionRowV1(
                    leg_id=leg.leg_id,
                    leg_label=leg.label,
                    subleg_id=subleg.subleg_id,
                    subleg_label=subleg.label,
                    subleg_kind=kind,
                    parent_subleg_id=parent_subleg_id,
                    section_id=f"{subleg.subleg_id}-section-{order:03d}",
                    order=order,
                    from_label=from_label,
                    to_room_id=to_room_id,
                    to_room_label=_room_label(project_state, to_room_id),
                    own_downstream_room_ids=own_downstream_room_ids,
                    rolled_up_subleg_ids=tuple(rolled_up_subleg_ids),
                    rolled_up_room_ids=tuple(rolled_up_room_ids),
                    carried_room_ids=carried_room_ids,
                    own_heat_W=own_heat,
                    rolled_up_heat_W=rolled_up_heat,
                    carried_heat_W=carried_heat,
                    own_flow_kg_s=own_flow,
                    rolled_up_flow_kg_s=rolled_up_flow,
                    carried_flow_kg_s=carried_flow,
                    status=status,
                )
            )

    ready = bool(rows) and not blockers

    return BranchAwareCarriedFlowBasisV1(
        ready=ready,
        status=(
            "Branch-aware carried-flow basis ready"
            if ready
            else "Branch-aware carried-flow basis incomplete"
        ),
        rows=tuple(rows),
        blockers=tuple(blockers),
    )
