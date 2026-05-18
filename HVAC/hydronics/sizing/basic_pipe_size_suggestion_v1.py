# ======================================================================
# HVAC/hydronics/sizing/basic_pipe_size_suggestion_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.routing.index_route_accumulator_v1 import (
    build_index_route_accumulator_v1,
)


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicPipeSizeCandidateV1:
    """
    First-pass pipe size candidate.

    Authority
    ---------
    • Static placeholder table for H-N8 proof only
    • Not a manufacturer/material authority
    • Not a Colebrook result
    """

    nominal_size_mm: float
    max_mass_flow_kg_s: float


@dataclass(frozen=True, slots=True)
class BasicPipeSizeSuggestionRowV1:
    """
    Read-only first-pass pipe size suggestion row.

    This is the early equivalent of the old BASIC:

        Ps = PipeSizefunc(AcFr)

    but does not perform exact hydraulic calculation.
    """

    section_index: int

    from_room_id: str
    from_room_label: str

    to_room_id: str
    to_room_label: str

    accumulated_mass_flow_kg_s: Optional[float]

    nominal_pressure_gradient_Pa_per_m: Optional[float]

    suggested_nominal_size_mm: Optional[float]
    capacity_mass_flow_kg_s: Optional[float]

    status: str


@dataclass(frozen=True, slots=True)
class BasicPipeSizeSuggestionV1:
    """
    H-N8 basic pipe size suggestion.

    Read-only.
    No ProjectState mutation.
    """

    basis: str
    nominal_pressure_gradient_Pa_per_m: Optional[float]
    rows: list[BasicPipeSizeSuggestionRowV1]


# ======================================================================
# Public builder
# ======================================================================

def build_basic_pipe_size_suggestion_v1(
    project: ProjectState,
) -> BasicPipeSizeSuggestionV1:
    """
    Build first-pass pipe size suggestions for the assumed index route.

    Rules
    -----
    • Uses IndexRouteAccumulatorV1 accumulated mass flow
    • Uses BasicHydronicSizingIntentV1 nominal pressure gradient
    • Uses placeholder pipe capacity table
    • Does not run Colebrook
    • Does not calculate pressure loss
    • Does not mutate ProjectState
    """
    route = build_index_route_accumulator_v1(project)
    nominal_gradient = _resolve_nominal_gradient(project)

    rows: list[BasicPipeSizeSuggestionRowV1] = []

    for section in route.sections:
        flow = section.accumulated_mass_flow_kg_s
        candidate = _select_candidate(flow)

        rows.append(
            BasicPipeSizeSuggestionRowV1(
                section_index=section.section_index,
                from_room_id=section.from_room_id,
                from_room_label=section.from_room_label,
                to_room_id=section.to_room_id,
                to_room_label=section.to_room_label,
                accumulated_mass_flow_kg_s=flow,
                nominal_pressure_gradient_Pa_per_m=nominal_gradient,
                suggested_nominal_size_mm=(
                    candidate.nominal_size_mm if candidate else None
                ),
                capacity_mass_flow_kg_s=(
                    candidate.max_mass_flow_kg_s if candidate else None
                ),
                status=_status(
                    flow=flow,
                    nominal_gradient=nominal_gradient,
                    candidate=candidate,
                ),
            )
        )

    return BasicPipeSizeSuggestionV1(
        basis="BASIC_CAPACITY_TABLE_WITH_DEFAULT_100_PA_PER_M",
        nominal_pressure_gradient_Pa_per_m=nominal_gradient,
        rows=rows,
    )


# ======================================================================
# Helpers
# ======================================================================

def _resolve_nominal_gradient(project: ProjectState) -> Optional[float]:
    """
    Resolve nominal pressure gradient for first-pass pipe sizing.

    H-Q default
    -----------
    If no BasicHydronicSizingIntentV1 exists, or if the value is unset/invalid,
    use a v1 default of 100 Pa/m.

    This is not a final hydraulic authority. It is a first-pass design basis
    so the pipe-size projection can produce a complete, honest row.
    """
    default_gradient_Pa_per_m = 100.0

    intent = getattr(project, "basic_hydronic_sizing_intent", None)

    if intent is None:
        return default_gradient_Pa_per_m

    value = getattr(intent, "nominal_pressure_gradient_Pa_per_m", None)

    if value is None:
        return default_gradient_Pa_per_m

    try:
        value = float(value)
    except (TypeError, ValueError):
        return default_gradient_Pa_per_m

    if value <= 0.0:
        return default_gradient_Pa_per_m

    return value


def _basic_capacity_table() -> list[BasicPipeSizeCandidateV1]:
    """
    H-N8 placeholder capacity table.

    Later replaced by material-specific pipe tables and hydraulic calculation.
    """
    return [
        BasicPipeSizeCandidateV1(10.0, 0.010),
        BasicPipeSizeCandidateV1(15.0, 0.030),
        BasicPipeSizeCandidateV1(22.0, 0.080),
        BasicPipeSizeCandidateV1(28.0, 0.160),
        BasicPipeSizeCandidateV1(35.0, 0.300),
        BasicPipeSizeCandidateV1(42.0, 0.500),
        BasicPipeSizeCandidateV1(54.0, 0.900),
    ]


def _select_candidate(
    flow_kg_s: Optional[float],
) -> Optional[BasicPipeSizeCandidateV1]:
    if flow_kg_s is None:
        return None

    try:
        flow = float(flow_kg_s)
    except (TypeError, ValueError):
        return None

    if flow <= 0.0:
        return None

    for candidate in _basic_capacity_table():
        if flow <= candidate.max_mass_flow_kg_s:
            return candidate

    return None


def _status(
    *,
    flow: Optional[float],
    nominal_gradient: Optional[float],
    candidate: Optional[BasicPipeSizeCandidateV1],
) -> str:
    if flow is None:
        return "NO_FLOW"

    if nominal_gradient is None:
        return "NO_NOMINAL_GRADIENT"

    if candidate is None:
        return "NO_SIZE_FOUND"

    return "SIZE_OK"