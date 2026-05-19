# ======================================================================
# HVAC/hydronics/pipes/pipe_authority_summary_v1.py
# ======================================================================

from __future__ import annotations

"""
HVACgooee — Hydronics H-Q1
Pipe Authority Summary V1

Purpose
-------
Classify hydronic pipework into authority categories so the UI can clearly
distinguish:

• terminal stubs
• index-route sections
• boiler/common-main pipework

This module is deliberately read-only.

It does not:
• mutate ProjectState
• size pipes
• calculate pressure loss
• select pumps
• infer manufacturer radiator data
"""

from dataclasses import dataclass
from typing import Any


# ======================================================================
# Constants
# ======================================================================

PIPE_ROLE_TERMINAL_STUB = "TERMINAL_STUB"
PIPE_ROLE_INDEX_ROUTE_SECTION = "INDEX_ROUTE_SECTION"
PIPE_ROLE_COMMON_MAIN = "COMMON_MAIN"

SIZING_SCOPE_DEFERRED = "DEFERRED"
SIZING_SCOPE_INDEX_ROUTE = "INDEX_ROUTE"
SIZING_SCOPE_NOT_SIZED = "NOT_SIZED"

STATUS_DEFERRED = "DEFERRED"
STATUS_SIZED_ELSEWHERE = "SIZED_ELSEWHERE"
STATUS_INFORMATIONAL = "INFORMATIONAL"
PIPE_ROLE_NON_INDEX_BRANCH_TERMINAL = "NON_INDEX_BRANCH_TERMINAL"

# ======================================================================
# DTO
# ======================================================================

@dataclass(frozen=True, slots=True)
class PipeAuthoritySummaryRowV1:
    """
    Read-only pipe authority row.

    Authority
    ---------
    This row explains what a pipe/section represents and what flow basis
    applies to it. It does not decide pipe size.
    """

    pipe_role: str
    from_label: str
    to_label: str
    flow_basis: str
    mass_flow_kg_s: float | None
    sizing_scope: str
    status: str


@dataclass(frozen=True, slots=True)
class PipeAuthoritySummaryV1:
    """
    Read-only pipe authority summary.
    """

    rows: tuple[PipeAuthoritySummaryRowV1, ...]


# ======================================================================
# Builder
# ======================================================================

def build_pipe_authority_summary_v1(
    *,
    project_state: Any,
    skeleton: Any,
    pipe_runs: list[Any],
    index_route: Any,
) -> PipeAuthoritySummaryV1:
    """
    Build a read-only pipe authority summary.

    Inputs
    ------
    project_state:
        Current ProjectState.

    skeleton:
        Hydronic skeleton produced by
        build_hydronic_skeleton_from_project_state_v1(...)

    pipe_runs:
        Pipe-run intent rows produced by
        build_pipe_run_intents_from_skeleton_v1(...)

    index_route:
        Index route accumulator produced by
        build_index_route_accumulator_v1(...)

    Returns
    -------
    PipeAuthoritySummaryV1

    H-Q1 rule
    ---------
    This first pass labels authority only. It does not size COMMON_MAIN or
    TERMINAL_STUB pipework.
    """

    rows: list[PipeAuthoritySummaryRowV1] = []

    # --------------------------------------------------
    # Common-main / boiler-side authority
    # --------------------------------------------------
    total_flow_kg_s = _sum_emitter_mass_flow_kg_s(project_state)

    rows.append(
        PipeAuthoritySummaryRowV1(
            pipe_role=PIPE_ROLE_COMMON_MAIN,
            from_label="Boiler / Heat Source",
            to_label="Common main / first branch",
            flow_basis="Total assigned emitter flow",
            mass_flow_kg_s=total_flow_kg_s,
            sizing_scope=SIZING_SCOPE_DEFERRED,
            status=STATUS_DEFERRED,
        )
    )

    # --------------------------------------------------
    # Index-route sections
    # --------------------------------------------------

    for section in getattr(index_route, "sections", []) or []:
        rows.append(
            PipeAuthoritySummaryRowV1(
                pipe_role=PIPE_ROLE_INDEX_ROUTE_SECTION,
                from_label=str(getattr(section, "from_room_label", "—")),
                to_label=str(getattr(section, "to_room_label", "—")),
                flow_basis="Accumulated route flow",
                mass_flow_kg_s=getattr(
                    section,
                    "accumulated_mass_flow_kg_s",
                    None,
                ),
                sizing_scope=SIZING_SCOPE_INDEX_ROUTE,
                status=STATUS_SIZED_ELSEWHERE,
            )
        )

    index_route_room_ids: set[str] = set()

    for section in getattr(index_route, "sections", []) or []:
        from_room_id = getattr(section, "from_room_id", None)
        to_room_id = getattr(section, "to_room_id", None)

        if from_room_id:
            index_route_room_ids.add(str(from_room_id))

        if to_room_id:
            index_route_room_ids.add(str(to_room_id))

    # --------------------------------------------------
    # Terminal stubs
    # --------------------------------------------------
    for pipe_run in pipe_runs or []:
        from_label = _node_label(skeleton, pipe_run.from_node_id)
        to_label = _node_label(skeleton, pipe_run.to_node_id)

        terminal_room_id = _terminal_room_id_for_pipe_run(
            skeleton=skeleton,
            pipe_run=pipe_run,
        )

        rows.append(
            PipeAuthoritySummaryRowV1(
                pipe_role=PIPE_ROLE_TERMINAL_STUB,
                from_label=from_label,
                to_label=to_label,
                flow_basis="Single terminal/emitter flow",
                mass_flow_kg_s=_room_emitter_mass_flow_kg_s(
                    project_state,
                    terminal_room_id,
                ),
                sizing_scope=SIZING_SCOPE_NOT_SIZED,
                status=STATUS_DEFERRED,
            )
        )

    return PipeAuthoritySummaryV1(rows=tuple(rows))


# ======================================================================
# Helpers
# ======================================================================

def _sum_emitter_mass_flow_kg_s(project_state: Any) -> float | None:
    """
    Sum emitter mass flow for assigned emitters.

    Current H-Q1 convention
    -----------------------
    If direct mass-flow values are unavailable, derive first-pass mass flow
    from:

        m_dot = Q / (4180 × ΔT_water)

    where Q is design_output_W and ΔT_water is flow_temp_C - return_temp_C.

    This is still projection-only; it does not store results.
    """

    total = 0.0
    found = False

    for emitter in (getattr(project_state, "emitters", {}) or {}).values():
        value = _emitter_mass_flow_kg_s(emitter)

        if value is None:
            continue

        total += value
        found = True

    return total if found else None


def _room_emitter_mass_flow_kg_s(
    project_state: Any,
    room_id: str | None,
) -> float | None:
    if not room_id:
        return None

    total = 0.0
    found = False

    for emitter in (getattr(project_state, "emitters", {}) or {}).values():
        if str(getattr(emitter, "room_id", "") or "") != str(room_id):
            continue

        value = _emitter_mass_flow_kg_s(emitter)

        if value is None:
            continue

        total += value
        found = True

    return total if found else None


def _emitter_mass_flow_kg_s(emitter: Any) -> float | None:
    output_W = getattr(emitter, "design_output_W", None)
    flow_temp_C = getattr(emitter, "flow_temp_C", None)
    return_temp_C = getattr(emitter, "return_temp_C", None)

    try:
        output_W = float(output_W)
        flow_temp_C = float(flow_temp_C)
        return_temp_C = float(return_temp_C)
    except (TypeError, ValueError):
        return None

    water_delta_t_K = flow_temp_C - return_temp_C

    if output_W <= 0.0:
        return None

    if water_delta_t_K <= 0.0:
        return None

    return output_W / (4180.0 * water_delta_t_K)


def _terminal_room_id_for_pipe_run(
    *,
    skeleton: Any,
    pipe_run: Any,
) -> str | None:
    """
    Resolve the terminal room_id for a pipe run.

    For v1 skeletons, one end of a terminal pipe run normally points to a
    terminal node. This helper checks both ends and returns the terminal's
    room_id where available.
    """

    for node_id in (
        getattr(pipe_run, "from_node_id", None),
        getattr(pipe_run, "to_node_id", None),
    ):
        terminal = getattr(skeleton, "terminals", {}).get(node_id)
        if terminal is None:
            continue

        room_id = getattr(terminal, "room_id", None)
        if room_id:
            return str(room_id)

    return None


def _node_label(skeleton: Any, node_id: str) -> str:
    boiler = getattr(skeleton, "boiler", None)

    if boiler is not None:
        boiler_id = getattr(boiler, "boiler_id", None)
        if node_id == boiler_id:
            return getattr(boiler, "name", None) or "Boiler / Heat Source"

    terminal = getattr(skeleton, "terminals", {}).get(node_id)

    if terminal is not None:
        room_name = getattr(terminal, "room_name", None)
        if room_name:
            return str(room_name)

        room_id = getattr(terminal, "room_id", None)
        if room_id:
            return str(room_id)

    return str(node_id)