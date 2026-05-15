# ======================================================================
# HVAC/hydronics/sizing/emitter_sizing_suggestion_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.project.project_state import ProjectState
from HVAC.core.room_identity import room_short_label


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class EmitterSizingSuggestionRowV1:
    """
    Read-only emitter sizing suggestion row.

    Authority
    ---------
    • Derived from ProjectState heat-loss results
    • Does not mutate ProjectState
    • Does not select catalogue radiators
    • Does not save emitter design output
    """

    room_id: str
    room_label: str

    heat_load_W: Optional[float]
    allowance_percent: float
    required_output_W: Optional[float]

    existing_emitter_output_W: Optional[float]
    suggested_rounded_output_W: Optional[float]

    status: str


@dataclass(frozen=True, slots=True)
class EmitterSizingSuggestionV1:
    """
    H-N6 read-only emitter sizing suggestion.

    selected/saved emitter output remains EmitterV1.design_output_W.
    """

    allowance_percent: float
    rows: list[EmitterSizingSuggestionRowV1]


# ======================================================================
# Builder
# ======================================================================

def build_emitter_sizing_suggestion_v1(
    project: ProjectState,
    *,
    allowance_percent: float = 12.0,
    rounding_step_W: float = 50.0,
) -> EmitterSizingSuggestionV1:
    """
    Build emitter output suggestions.

    Formula
    -------
        required_output_W = Qt × (1 + allowance_percent / 100)

    rounded suggestion
    ------------------
        round up to nearest rounding_step_W

    Rules
    -----
    • Read-only
    • No catalogue lookup
    • No ProjectState mutation
    • No hydronic pressure calculation
    """
    rows: list[EmitterSizingSuggestionRowV1] = []

    rooms = getattr(project, "rooms", {}) or {}

    for room_id, room in rooms.items():
        heat_load_W = _resolve_room_heat_load_W(project, room_id)
        existing_output_W = _sum_emitter_output_W(project, room_id)

        required_output_W = _required_output_W(
            heat_load_W=heat_load_W,
            allowance_percent=allowance_percent,
        )

        suggested_rounded_output_W = _round_up_to_step(
            required_output_W,
            rounding_step_W,
        )

        status = _status(
            heat_load_W=heat_load_W,
            existing_emitter_output_W=existing_output_W,
            required_output_W=required_output_W,
        )

        rows.append(
            EmitterSizingSuggestionRowV1(
                room_id=room_id,
                room_label=room_short_label(room_id, room),
                heat_load_W=heat_load_W,
                allowance_percent=float(allowance_percent),
                required_output_W=required_output_W,
                existing_emitter_output_W=existing_output_W,
                suggested_rounded_output_W=suggested_rounded_output_W,
                status=status,
            )
        )

    return EmitterSizingSuggestionV1(
        allowance_percent=float(allowance_percent),
        rows=rows,
    )


# ======================================================================
# Helpers
# ======================================================================

def _resolve_room_heat_load_W(
    project: ProjectState,
    room_id: str,
) -> Optional[float]:
    if not getattr(project, "heatloss_valid", False):
        return None

    heatloss_results = getattr(project, "heatloss_results", None) or {}
    room_totals = heatloss_results.get("room_totals", {}) or {}
    room_total = room_totals.get(room_id, {}) or {}

    qt = room_total.get("q_total_W")

    if qt is None:
        return None

    try:
        return float(qt)
    except (TypeError, ValueError):
        return None


def _required_output_W(
    *,
    heat_load_W: Optional[float],
    allowance_percent: float,
) -> Optional[float]:
    if heat_load_W is None:
        return None

    try:
        heat_load = float(heat_load_W)
        allowance = float(allowance_percent)
    except (TypeError, ValueError):
        return None

    if heat_load <= 0.0:
        return None

    return heat_load * (1.0 + allowance / 100.0)


def _round_up_to_step(
    value_W: Optional[float],
    step_W: float,
) -> Optional[float]:
    if value_W is None:
        return None

    try:
        value = float(value_W)
        step = float(step_W)
    except (TypeError, ValueError):
        return None

    if value <= 0.0 or step <= 0.0:
        return None

    import math

    return math.ceil(value / step) * step


def _sum_emitter_output_W(
    project: ProjectState,
    room_id: str,
) -> Optional[float]:
    emitters = getattr(project, "emitters", {}) or {}

    total = 0.0
    has_output = False

    for emitter in emitters.values():
        if getattr(emitter, "room_id", None) != room_id:
            continue

        output = getattr(emitter, "design_output_W", None)
        if output is None:
            continue

        try:
            total += float(output)
            has_output = True
        except (TypeError, ValueError):
            continue

    return total if has_output else None


def _status(
    *,
    heat_load_W: Optional[float],
    existing_emitter_output_W: Optional[float],
    required_output_W: Optional[float],
) -> str:
    if heat_load_W is None:
        return "NO_HEAT_LOSS_RESULT"

    if required_output_W is None:
        return "NO_REQUIRED_OUTPUT"

    if existing_emitter_output_W is None:
        return "NEEDS_EMITTER_SELECTION"

    if existing_emitter_output_W < required_output_W:
        return "EMITTER_BELOW_SUGGESTION"

    return "EMITTER_OK"