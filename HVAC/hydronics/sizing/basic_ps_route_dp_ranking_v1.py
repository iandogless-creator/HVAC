# ======================================================================
# HVAC/hydronics/sizing/basic_ps_route_dp_ranking_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from HVAC.hydronics.sizing.basic_ps_pressure_preview_v1 import (
    BasicPSPressurePreviewProjectionV1,
)


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicPSRoutePressureCandidateV1:
    """
    Candidate route/circuit for Basic PS pressure ranking.

    H-S8-I:
    Wraps a pressure-preview projection with route identity.

    This is not final balancing or true proportioning.
    """

    route_id: str
    route_label: str
    pressure_preview: BasicPSPressurePreviewProjectionV1

    leg_id: str = ""
    subleg_id: str = ""


@dataclass(frozen=True, slots=True)
class BasicPSRoutePressureRankRowV1:
    """
    Read-only Basic PS route Δp ranking row.

    A route is rankable only when its pressure preview has a complete
    total_pressure_drop_Pa.
    """

    route_id: str
    route_label: str

    leg_id: str
    subleg_id: str

    total_length_m: float | None
    total_pressure_drop_Pa: float | None

    rank: int | None
    is_complete: bool
    is_controlling_index: bool = False

    status: str = "Projection only"


@dataclass(frozen=True, slots=True)
class BasicPSRoutePressureRankingProjectionV1:
    """
    Read-only Basic PS route pressure ranking projection.

    Does not:
    - mutate ProjectState
    - select pumps
    - balance branches
    - account for fittings, tees, or valves
    - overwrite topology authority
    """

    rows: tuple[BasicPSRoutePressureRankRowV1, ...]
    controlling_route_id: str | None
    status: str = "Projection only"


# ======================================================================
# Public builder
# ======================================================================

def build_basic_ps_route_dp_ranking_v1(
    candidates: Iterable[BasicPSRoutePressureCandidateV1],
) -> BasicPSRoutePressureRankingProjectionV1:
    """
    Rank complete Basic PS routes by total Δp.

    Ranking rule:
        highest total_pressure_drop_Pa = rank 1

    Incomplete routes:
        total_pressure_drop_Pa is None
        rank is None
        placed after ranked routes
    """

    candidate_tuple = tuple(candidates)

    complete: list[tuple[BasicPSRoutePressureCandidateV1, float]] = []
    incomplete: list[BasicPSRoutePressureCandidateV1] = []

    for candidate in candidate_tuple:
        total_dp = candidate.pressure_preview.total_pressure_drop_Pa

        if total_dp is None:
            incomplete.append(candidate)
        else:
            complete.append((candidate, float(total_dp)))

    complete.sort(key=lambda item: item[1], reverse=True)

    controlling_route_id = complete[0][0].route_id if complete else None

    rows: list[BasicPSRoutePressureRankRowV1] = []

    for index, (candidate, total_dp) in enumerate(complete, start=1):
        rows.append(
            BasicPSRoutePressureRankRowV1(
                route_id=candidate.route_id,
                route_label=candidate.route_label,
                leg_id=candidate.leg_id,
                subleg_id=candidate.subleg_id,
                total_length_m=_total_length_or_none(candidate.pressure_preview),
                total_pressure_drop_Pa=total_dp,
                rank=index,
                is_complete=True,
                is_controlling_index=(
                    candidate.route_id == controlling_route_id
                ),
                status="Ranked by total Δp",
            )
        )

    for candidate in incomplete:
        rows.append(
            BasicPSRoutePressureRankRowV1(
                route_id=candidate.route_id,
                route_label=candidate.route_label,
                leg_id=candidate.leg_id,
                subleg_id=candidate.subleg_id,
                total_length_m=None,
                total_pressure_drop_Pa=None,
                rank=None,
                is_complete=False,
                is_controlling_index=False,
                status="Incomplete — section length missing",
            )
        )

    return BasicPSRoutePressureRankingProjectionV1(
        rows=tuple(rows),
        controlling_route_id=controlling_route_id,
        status=(
            "Projection incomplete — some routes missing section lengths"
            if incomplete
            else "Projection only"
        ),
    )


# ======================================================================
# Helpers
# ======================================================================

def _total_length_or_none(
    preview: BasicPSPressurePreviewProjectionV1,
) -> float | None:
    total = 0.0

    for row in preview.rows:
        if row.section_length_m is None:
            return None
        total += row.section_length_m

    return total