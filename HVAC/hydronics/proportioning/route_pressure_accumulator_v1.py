# ======================================================================
# HVAC/hydronics/proportioning/route_pressure_accumulator_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.local_losses.local_k_pressure_preview_v1 import (
    build_local_k_pressure_preview_v1,
)


@dataclass(frozen=True, slots=True)
class RoutePressureSectionContributionV1:
    section_id: str
    order: int
    from_label: str
    to_label: str
    straight_pressure_drop_Pa: float | None
    local_pressure_drop_Pa: float
    section_total_pressure_drop_Pa: float | None
    status: str


@dataclass(frozen=True, slots=True)
class RoutePressureAccumulatorRowV1:
    route_id: str
    route_label: str
    leg_id: str
    subleg_id: str
    section_count: int
    straight_pressure_drop_total_Pa: float | None
    local_pressure_drop_total_Pa: float
    route_pressure_drop_total_Pa: float | None
    complete: bool
    rank: int | None
    is_controlling_candidate: bool
    sections: tuple[RoutePressureSectionContributionV1, ...]
    status: str


@dataclass(frozen=True, slots=True)
class RoutePressureAccumulatorProjectionV1:
    rows: tuple[RoutePressureAccumulatorRowV1, ...]
    status: str = "Route Δp preview only"


def build_route_pressure_accumulator_v1(
    project_state: Any,
    *,
    leg_id: str | None = None,
    subleg_id: str | None = None,
) -> RoutePressureAccumulatorProjectionV1:
    """
    Accumulate section Δp into route totals across all requested sublegs.

    If leg_id/subleg_id are omitted, all legs/sublegs are accumulated.

    Preview only:
    - no final balancing
    - no pump selection
    - no pipe resizing
    - no ProjectState mutation
    """
    topology = getattr(project_state, "hydronic_topology", None)

    if topology is None:
        raise ValueError("ProjectState has no hydronic_topology")

    route_targets: list[tuple[str, str]] = []

    for leg in getattr(topology, "legs", []) or []:
        current_leg_id = str(getattr(leg, "leg_id", "") or "")

        if leg_id is not None and current_leg_id != str(leg_id):
            continue

        for subleg in getattr(leg, "sublegs", []) or []:
            current_subleg_id = str(getattr(subleg, "subleg_id", "") or "")

            if subleg_id is not None and current_subleg_id != str(subleg_id):
                continue

            if current_leg_id and current_subleg_id:
                route_targets.append((current_leg_id, current_subleg_id))

    rows = [
        _build_single_route_pressure_row_v1(
            project_state,
            leg_id=current_leg_id,
            subleg_id=current_subleg_id,
        )
        for current_leg_id, current_subleg_id in route_targets
    ]

    complete_rows = [
        row for row in rows
        if row.route_pressure_drop_total_Pa is not None
    ]

    complete_rows_sorted = sorted(
        complete_rows,
        key=lambda row: float(row.route_pressure_drop_total_Pa or 0.0),
        reverse=True,
    )

    controlling_route_id = (
        complete_rows_sorted[0].route_id
        if complete_rows_sorted
        else None
    )

    ranked_by_id = {
        row.route_id: index
        for index, row in enumerate(complete_rows_sorted, start=1)
    }

    final_rows: list[RoutePressureAccumulatorRowV1] = []

    for row in rows:
        rank = ranked_by_id.get(row.route_id)
        is_controlling = bool(
            controlling_route_id and row.route_id == controlling_route_id
        )

        final_rows.append(
            RoutePressureAccumulatorRowV1(
                route_id=row.route_id,
                route_label=row.route_label,
                leg_id=row.leg_id,
                subleg_id=row.subleg_id,
                section_count=row.section_count,
                straight_pressure_drop_total_Pa=(
                    row.straight_pressure_drop_total_Pa
                ),
                local_pressure_drop_total_Pa=(
                    row.local_pressure_drop_total_Pa
                ),
                route_pressure_drop_total_Pa=(
                    row.route_pressure_drop_total_Pa
                ),
                complete=row.complete,
                rank=rank,
                is_controlling_candidate=is_controlling,
                sections=row.sections,
                status=(
                    "Controlling route candidate — preview only"
                    if is_controlling
                    else (
                        "Ranked route candidate — preview only"
                        if rank is not None
                        else "Incomplete — one or more section lengths not set"
                    )
                ),
            )
        )

    return RoutePressureAccumulatorProjectionV1(
        rows=tuple(final_rows),
        status=(
            "Route Δp preview incomplete — one or more routes missing lengths"
            if any(not row.complete for row in final_rows)
            else "Route Δp preview only"
        ),
    )


def _build_single_route_pressure_row_v1(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> RoutePressureAccumulatorRowV1:
    basic_ps = build_basic_ps_readonly_projection_v1(
        project_state,
        leg_id=leg_id,
        subleg_id=subleg_id,
    )

    route_id = (
        f"{basic_ps.sections_projection.leg_id}:"
        f"{basic_ps.sections_projection.subleg_id}"
    )
    route_label = (
        f"{basic_ps.sections_projection.leg_label} / "
        f"{basic_ps.sections_projection.subleg_label}"
    )

    contributions: list[RoutePressureSectionContributionV1] = []

    straight_total = 0.0
    local_total = 0.0
    route_total = 0.0
    complete = True

    for result in basic_ps.pipe_sizing_projection.results:
        preview = build_local_k_pressure_preview_v1(
            project_state,
            section_id=str(result.section_id),
            velocity_m_s=float(result.velocity_m_s),
            pressure_gradient_Pa_per_m=float(
                result.pressure_gradient_Pa_per_m
            ),
        )

        local_total += float(preview.local_pressure_drop_Pa or 0.0)

        if preview.straight_pressure_drop_Pa is None:
            complete = False
        else:
            straight_total += float(preview.straight_pressure_drop_Pa)

        if preview.section_total_pressure_drop_Pa is None:
            complete = False
        else:
            route_total += float(preview.section_total_pressure_drop_Pa)

        contributions.append(
            RoutePressureSectionContributionV1(
                section_id=str(result.section_id),
                order=int(result.order),
                from_label=str(result.from_label),
                to_label=str(result.to_room_label),
                straight_pressure_drop_Pa=preview.straight_pressure_drop_Pa,
                local_pressure_drop_Pa=float(
                    preview.local_pressure_drop_Pa or 0.0
                ),
                section_total_pressure_drop_Pa=(
                    preview.section_total_pressure_drop_Pa
                ),
                status=preview.status,
            )
        )

    return RoutePressureAccumulatorRowV1(
        route_id=route_id,
        route_label=route_label,
        leg_id=str(basic_ps.sections_projection.leg_id),
        subleg_id=str(basic_ps.sections_projection.subleg_id),
        section_count=len(contributions),
        straight_pressure_drop_total_Pa=straight_total if complete else None,
        local_pressure_drop_total_Pa=local_total,
        route_pressure_drop_total_Pa=route_total if complete else None,
        complete=complete,
        rank=None,
        is_controlling_candidate=False,
        sections=tuple(contributions),
        status=(
            "Route Δp preview only — not final balancing"
            if complete
            else "Incomplete — one or more section lengths not set"
        ),
    )