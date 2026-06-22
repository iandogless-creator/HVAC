# ======================================================================
# HVAC/hydronics/proportioning/branch_aware_route_summary_audit_v1.py
# H-S25-A — Branch-aware route summary / topology authority audit
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    build_branch_aware_carried_flow_basis_v1,
)
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_id_for_leg,
)


@dataclass(frozen=True, slots=True)
class BranchAwareRouteSummaryAuditRowV1:
    leg_id: str
    leg_label: str
    subleg_id: str
    subleg_label: str
    role: str
    parent_subleg_id: str
    origin_room_id: str
    takeoff_classification: str
    route_room_ids: tuple[str, ...]
    entry_carried_room_ids: tuple[str, ...]
    entry_carried_heat_W: float | None
    entry_carried_flow_kg_s: float | None
    basic_ps_entry_heat_W: float | None
    basic_ps_entry_flow_kg_s: float | None
    basic_ps_matches_branch_aware: bool
    status: str


@dataclass(frozen=True, slots=True)
class BranchAwareRouteSummaryAuditV1:
    ready: bool = False
    status: str = "Branch-aware route summary audit not ready"
    rows: tuple[BranchAwareRouteSummaryAuditRowV1, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _SublegInfo:
    leg: HydronicLegV1
    subleg: HydronicSublegV1
    parent_subleg_id: str


def _flatten_leg_sublegs(leg: HydronicLegV1) -> list[_SublegInfo]:
    primary_id = primary_subleg_id_for_leg(leg.leg_id)
    has_primary = any(subleg.subleg_id == primary_id for subleg in leg.sublegs)
    out: list[_SublegInfo] = []

    def walk(subleg: HydronicSublegV1, parent_subleg_id: str) -> None:
        out.append(_SublegInfo(leg=leg, subleg=subleg, parent_subleg_id=parent_subleg_id))
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


def _takeoff_classification(
    *,
    subleg: HydronicSublegV1,
    parent_subleg: HydronicSublegV1 | None,
    is_primary: bool,
) -> str:
    if is_primary:
        return "Primary/common subleg from common main / leg entry"

    if parent_subleg is None:
        return "Parent subleg unresolved"

    parent_rooms = [str(room_id) for room_id in parent_subleg.route_room_ids]
    origin = str(subleg.origin_room_id or "").strip()

    if not origin or origin not in parent_rooms:
        return "Branch take-off unresolved — origin not in parent route"

    origin_index = parent_rooms.index(origin)
    terminal_index = len(parent_rooms) - 1

    if origin_index == terminal_index:
        return "Continuation from parent terminal"

    if origin_index == 0:
        return "Early take-off / riser-capable branch"

    if origin_index == terminal_index - 1:
        return "Late take-off — parent downstream terminal emitter only"

    return "Branch roll-up to take-off"


def _role(
    *,
    subleg: HydronicSublegV1,
    parent_subleg: HydronicSublegV1 | None,
    is_primary: bool,
) -> str:
    if is_primary:
        return "primary/common subleg"

    classification = _takeoff_classification(
        subleg=subleg,
        parent_subleg=parent_subleg,
        is_primary=False,
    )

    if classification == "Continuation from parent terminal":
        return "continuation subleg"

    if parent_subleg is not None:
        return "branch subleg"

    return "subleg"


def _section_001_id(subleg_id: str) -> str:
    return f"{subleg_id}-section-001"


def _basic_ps_entry_by_subleg(
    *,
    project_state: Any,
    leg_id: str,
    subleg_id: str,
) -> tuple[float | None, float | None]:
    try:
        projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return None, None

    if not projection.sections:
        return None, None

    first = projection.sections[0]
    return first.carried_heat_W, first.carried_flow_kg_s


def _floats_match(left: float | None, right: float | None) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return abs(float(left) - float(right)) < 1e-9


def _status(
    *,
    entry_carried_heat_W: float | None,
    entry_carried_flow_kg_s: float | None,
    basic_ps_matches: bool,
) -> str:
    if entry_carried_heat_W is None or entry_carried_flow_kg_s is None:
        return "Branch-aware entry basis unavailable"

    if not basic_ps_matches:
        return "Basic PS entry basis differs from branch-aware authority"

    return "Topology and Basic PS agree with branch-aware authority"


def build_branch_aware_route_summary_audit_v1(
    project_state: Any,
) -> BranchAwareRouteSummaryAuditV1:
    if project_state is None:
        return BranchAwareRouteSummaryAuditV1(
            ready=False,
            blockers=("No project_state is available",),
        )

    topology = getattr(project_state, "hydronic_topology", None)

    if topology is None:
        return BranchAwareRouteSummaryAuditV1(
            ready=False,
            blockers=("No hydronic topology is available",),
        )

    if not isinstance(topology, HydronicTopologyV1):
        return BranchAwareRouteSummaryAuditV1(
            ready=False,
            blockers=("project_state.hydronic_topology is not HydronicTopologyV1",),
        )

    branch_basis = build_branch_aware_carried_flow_basis_v1(project_state)

    if not branch_basis.ready:
        return BranchAwareRouteSummaryAuditV1(
            ready=False,
            blockers=(
                "Branch-aware carried-flow basis unavailable",
                *branch_basis.blockers,
            ),
        )

    branch_by_section_id = {
        row.section_id: row
        for row in branch_basis.rows
    }

    infos: list[_SublegInfo] = []
    sublegs_by_id: dict[str, HydronicSublegV1] = {}

    for leg in topology.legs:
        leg_infos = _flatten_leg_sublegs(leg)
        infos.extend(leg_infos)

        for info in leg_infos:
            sublegs_by_id[info.subleg.subleg_id] = info.subleg

    rows: list[BranchAwareRouteSummaryAuditRowV1] = []
    blockers: list[str] = []

    for info in infos:
        leg = info.leg
        subleg = info.subleg
        is_primary = subleg.subleg_id == primary_subleg_id_for_leg(leg.leg_id)
        parent_subleg = sublegs_by_id.get(info.parent_subleg_id)

        entry_section_id = _section_001_id(subleg.subleg_id)
        entry_basis = branch_by_section_id.get(entry_section_id)

        entry_heat = entry_basis.carried_heat_W if entry_basis is not None else None
        entry_flow = entry_basis.carried_flow_kg_s if entry_basis is not None else None

        basic_heat, basic_flow = _basic_ps_entry_by_subleg(
            project_state=project_state,
            leg_id=leg.leg_id,
            subleg_id=subleg.subleg_id,
        )

        matches = (
            _floats_match(entry_heat, basic_heat)
            and _floats_match(entry_flow, basic_flow)
        )

        status = _status(
            entry_carried_heat_W=entry_heat,
            entry_carried_flow_kg_s=entry_flow,
            basic_ps_matches=matches,
        )

        if "unavailable" in status or "differs" in status:
            blockers.append(f"{subleg.label}: {status}")

        rows.append(
            BranchAwareRouteSummaryAuditRowV1(
                leg_id=leg.leg_id,
                leg_label=leg.label,
                subleg_id=subleg.subleg_id,
                subleg_label=subleg.label,
                role=_role(
                    subleg=subleg,
                    parent_subleg=parent_subleg,
                    is_primary=is_primary,
                ),
                parent_subleg_id=info.parent_subleg_id,
                origin_room_id=str(subleg.origin_room_id or ""),
                takeoff_classification=_takeoff_classification(
                    subleg=subleg,
                    parent_subleg=parent_subleg,
                    is_primary=is_primary,
                ),
                route_room_ids=tuple(str(x) for x in subleg.route_room_ids),
                entry_carried_room_ids=(
                    entry_basis.carried_room_ids if entry_basis is not None else ()
                ),
                entry_carried_heat_W=entry_heat,
                entry_carried_flow_kg_s=entry_flow,
                basic_ps_entry_heat_W=basic_heat,
                basic_ps_entry_flow_kg_s=basic_flow,
                basic_ps_matches_branch_aware=matches,
                status=status,
            )
        )

    ready = bool(rows) and not blockers

    return BranchAwareRouteSummaryAuditV1(
        ready=ready,
        status=(
            "Branch-aware route summary audit ready"
            if ready
            else "Branch-aware route summary audit incomplete"
        ),
        rows=tuple(rows),
        blockers=tuple(blockers),
    )
