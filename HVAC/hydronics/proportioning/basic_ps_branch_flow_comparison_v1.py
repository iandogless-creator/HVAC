# ======================================================================
# HVAC/hydronics/proportioning/basic_ps_branch_flow_comparison_v1.py
# H-S24-E — Compare Basic PS carried-flow basis with branch-aware basis
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    BranchAwareCarriedFlowSectionRowV1,
    build_branch_aware_carried_flow_basis_v1,
)
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
)


@dataclass(frozen=True, slots=True)
class BasicPSBranchFlowComparisonRowV1:
    """
    One section comparison between current Basic PS carried-flow basis
    and the branch-aware carried-flow basis.

    Projection only:
    • no pipe sizing change
    • no pressure-drop change
    • no balancing change
    • no GUI change
    • no ProjectState mutation
    """

    section_id: str
    leg_id: str
    subleg_id: str
    order: int
    from_label: str
    to_room_id: str
    to_room_label: str

    basic_carried_heat_W: float
    branch_aware_carried_heat_W: float | None
    heat_delta_W: float | None

    basic_carried_flow_kg_s: float
    branch_aware_carried_flow_kg_s: float | None
    flow_delta_kg_s: float | None

    basic_downstream_room_ids: tuple[str, ...]
    branch_aware_carried_room_ids: tuple[str, ...]
    branch_aware_rolled_up_room_ids: tuple[str, ...]
    branch_aware_status: str

    differs: bool
    status: str


@dataclass(frozen=True, slots=True)
class BasicPSBranchFlowComparisonV1:
    """
    H-S24-E comparison projection.
    """

    ready: bool = False
    status: str = "Basic PS / branch-aware carried-flow comparison not ready"
    rows: tuple[BasicPSBranchFlowComparisonRowV1, ...] = ()
    blockers: tuple[str, ...] = ()


def _float_delta(
    left: float | None,
    right: float | None,
) -> float | None:
    if left is None or right is None:
        return None

    return float(right) - float(left)


def _differs(
    *,
    heat_delta_W: float | None,
    flow_delta_kg_s: float | None,
) -> bool:
    if heat_delta_W is not None and abs(heat_delta_W) > 1e-9:
        return True

    if flow_delta_kg_s is not None and abs(flow_delta_kg_s) > 1e-12:
        return True

    return False


def _status(
    *,
    branch_row: BranchAwareCarriedFlowSectionRowV1 | None,
    differs: bool,
) -> str:
    if branch_row is None:
        return "No matching branch-aware section"

    if differs:
        return "Branch-aware carried flow differs from Basic PS"

    return "Basic PS carried flow matches branch-aware basis"


def build_basic_ps_branch_flow_comparison_v1(
    project_state: Any,
    *,
    leg_id: str = "leg-001",
    subleg_id: str | None = None,
) -> BasicPSBranchFlowComparisonV1:
    """
    Compare current Basic PS carried-flow rows against the H-S24-C
    branch-aware carried-flow basis.

    This is deliberately diagnostic only. It does not replace the Basic PS
    basis yet.
    """

    if project_state is None:
        return BasicPSBranchFlowComparisonV1(
            ready=False,
            blockers=("No project_state is available",),
        )

    try:
        basic_projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception as exc:
        return BasicPSBranchFlowComparisonV1(
            ready=False,
            blockers=(f"Basic PS topology sections unavailable: {exc}",),
        )

    branch_basis = build_branch_aware_carried_flow_basis_v1(project_state)

    if not branch_basis.ready:
        return BasicPSBranchFlowComparisonV1(
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

    rows: list[BasicPSBranchFlowComparisonRowV1] = []
    blockers: list[str] = []

    for basic_row in basic_projection.sections:
        section_id = str(basic_row.section_id)
        branch_row = branch_by_section_id.get(section_id)

        branch_heat = (
            branch_row.carried_heat_W
            if branch_row is not None
            else None
        )
        branch_flow = (
            branch_row.carried_flow_kg_s
            if branch_row is not None
            else None
        )

        heat_delta = _float_delta(
            basic_row.carried_heat_W,
            branch_heat,
        )
        flow_delta = _float_delta(
            basic_row.carried_flow_kg_s,
            branch_flow,
        )

        differs = _differs(
            heat_delta_W=heat_delta,
            flow_delta_kg_s=flow_delta,
        )

        if branch_row is None:
            blockers.append(f"{section_id}: no matching branch-aware section")

        rows.append(
            BasicPSBranchFlowComparisonRowV1(
                section_id=section_id,
                leg_id=basic_row.leg_id,
                subleg_id=basic_row.subleg_id,
                order=basic_row.order,
                from_label=basic_row.from_label,
                to_room_id=basic_row.to_room_id,
                to_room_label=basic_row.to_room_label,
                basic_carried_heat_W=basic_row.carried_heat_W,
                branch_aware_carried_heat_W=branch_heat,
                heat_delta_W=heat_delta,
                basic_carried_flow_kg_s=basic_row.carried_flow_kg_s,
                branch_aware_carried_flow_kg_s=branch_flow,
                flow_delta_kg_s=flow_delta,
                basic_downstream_room_ids=tuple(basic_row.downstream_room_ids),
                branch_aware_carried_room_ids=(
                    branch_row.carried_room_ids
                    if branch_row is not None
                    else ()
                ),
                branch_aware_rolled_up_room_ids=(
                    branch_row.rolled_up_room_ids
                    if branch_row is not None
                    else ()
                ),
                branch_aware_status=(
                    branch_row.status
                    if branch_row is not None
                    else ""
                ),
                differs=differs,
                status=_status(
                    branch_row=branch_row,
                    differs=differs,
                ),
            )
        )

    ready = bool(rows) and not blockers

    differing_count = sum(1 for row in rows if row.differs)

    if not rows:
        status = "Basic PS / branch-aware comparison has no rows"
    elif differing_count:
        status = (
            "Basic PS / branch-aware comparison ready "
            f"— {differing_count} differing section(s)"
        )
    else:
        status = "Basic PS / branch-aware comparison ready — no differences"

    return BasicPSBranchFlowComparisonV1(
        ready=ready,
        status=status,
        rows=tuple(rows),
        blockers=tuple(blockers),
    )
