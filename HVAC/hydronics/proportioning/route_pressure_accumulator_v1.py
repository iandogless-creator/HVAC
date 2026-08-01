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
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.proportioning.common_main_leg_entry_sections_v1 import (
    COMMON_MAIN_SECTION_KIND,
    LEG_ENTRY_SECTION_KIND,
)
from HVAC.hydronics.proportioning.common_main_leg_entry_pressure_authority_v1 import (
    build_common_main_leg_entry_pressure_authority_v1,
)

@dataclass(frozen=True, slots=True)
class RoutePressureSectionContributionV1:
    section_id: str
    order: int
    from_label: str
    to_label: str

    pressure_gradient_Pa_per_m: float
    velocity_m_s: float
    reynolds_number: float
    friction_factor: float
    friction_method: str
    colebrook_iteration_count: int
    colebrook_converged: bool

    straight_pressure_drop_Pa: float | None
    local_pressure_drop_Pa: float
    section_total_pressure_drop_Pa: float | None
    status: str
    section_scope: str = "route_section"

    # H-S54-A — numeric source evidence copied into committed authority.
    carried_flow_kg_s: float | None = None
    pipe_size_label: str = ""
    dn: int | None = None
    length_m: float | None = None
    k_total: float | None = None
    # H-S63-B2B — exact material/bore evidence for later freezing.
    material_key: str = "copper"
    material_label: str = "Copper EN1057"
    internal_diameter_m: float | None = None
    material_roughness_m: float | None = None


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

    # H-S42-D — explicit pressure-scope evidence.
    common_main_pressure_drop_total_Pa: float | None = 0.0
    leg_entry_pressure_drop_total_Pa: float | None = 0.0
    route_section_pressure_drop_total_Pa: float | None = 0.0


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
                common_main_pressure_drop_total_Pa=(
                    row.common_main_pressure_drop_total_Pa
                ),
                leg_entry_pressure_drop_total_Pa=(
                    row.leg_entry_pressure_drop_total_Pa
                ),
                route_section_pressure_drop_total_Pa=(
                    row.route_section_pressure_drop_total_Pa
                ),
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

    # H-S42-C — select physical common-main rows by carried-leg
    # authority, then the one stable entry row for this leg.
    main_projection = (
        build_common_main_leg_entry_pressure_authority_v1(project_state)
    )
    applicable_main_rows = tuple(
        row
        for row in main_projection.rows
        if (
            row.section_kind == COMMON_MAIN_SECTION_KIND
            and str(leg_id) in tuple(row.carried_leg_ids)
        )
        or (
            row.section_kind == LEG_ENTRY_SECTION_KIND
            and row.takeoff_leg_id == str(leg_id)
        )
    )
    contributions: list[RoutePressureSectionContributionV1] = [
        _main_pressure_contribution_v1(row)
        for row in applicable_main_rows
    ]
    seen_section_ids = {row.section_id for row in contributions}

    straight_total = sum(
        float(row.straight_pressure_drop_Pa or 0.0)
        for row in contributions
    )
    local_total = sum(
        float(row.local_pressure_drop_Pa or 0.0)
        for row in contributions
    )
    route_total = sum(
        float(row.section_total_pressure_drop_Pa or 0.0)
        for row in contributions
    )
    complete = bool(main_projection.ready) and all(
        row.section_total_pressure_drop_Pa is not None
        for row in contributions
    )

    for result in basic_ps.pipe_sizing_projection.results:
        section_id = str(result.section_id)
        if section_id in seen_section_ids:
            continue
        seen_section_ids.add(section_id)

        section_length_m = _local_k_section_length_m_v1(
            project_state,
            section_id=section_id,
        )

        # H-S63-B2B — consume exact H-S63-B2A identity; display
        # wording is never parsed back into hydraulic authority.
        material_key, pipe_size_key = _basic_ps_result_pipe_identity_v1(result)
        pressure_basis = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
            mass_flow_kg_s=float(result.carried_flow_kg_s),
            material=material_key,
            dn=pipe_size_key,
            length_m=(
                float(section_length_m)
                if section_length_m is not None
                else 0.0
            ),
            friction_method="colebrook",
        )

        preview = build_local_k_pressure_preview_v1(
            project_state,
            section_id=section_id,
            velocity_m_s=float(pressure_basis.velocity_m_s),
            pressure_gradient_Pa_per_m=float(
                pressure_basis.pressure_gradient_pa_per_m
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
                section_id=section_id,
                order=int(result.order),
                from_label=str(result.from_label),
                to_label=str(result.to_room_label),
                pressure_gradient_Pa_per_m=float(
                    pressure_basis.pressure_gradient_pa_per_m
                ),
                velocity_m_s=float(pressure_basis.velocity_m_s),
                reynolds_number=float(pressure_basis.reynolds_number),
                friction_factor=float(
                    pressure_basis.selected_friction_factor
                ),
                friction_method=str(pressure_basis.friction_method),
                colebrook_iteration_count=int(
                    pressure_basis.colebrook_iteration_count
                ),
                colebrook_converged=bool(
                    pressure_basis.colebrook_converged
                ),
                straight_pressure_drop_Pa=preview.straight_pressure_drop_Pa,
                local_pressure_drop_Pa=float(
                    preview.local_pressure_drop_Pa or 0.0
                ),
                section_total_pressure_drop_Pa=(
                    preview.section_total_pressure_drop_Pa
                ),
                status=preview.status,
                section_scope="route_section",
                carried_flow_kg_s=float(result.carried_flow_kg_s),
                pipe_size_label=str(result.pipe_size_label),
                dn=pipe_size_key,
                length_m=section_length_m,
                k_total=float(preview.k_total),
                material_key=material_key,
                material_label=str(result.material_label),
                internal_diameter_m=float(
                    pressure_basis.internal_diameter_m
                ),
                material_roughness_m=float(pressure_basis.roughness_m),
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
        common_main_pressure_drop_total_Pa=_scope_pressure_total_v1(
            contributions, COMMON_MAIN_SECTION_KIND
        ),
        leg_entry_pressure_drop_total_Pa=_scope_pressure_total_v1(
            contributions, LEG_ENTRY_SECTION_KIND
        ),
        route_section_pressure_drop_total_Pa=_scope_pressure_total_v1(
            contributions, "route_section"
        ),
        status=(
            "Route Δp preview only — not final balancing"
            if complete
            else "Incomplete — one or more section lengths not set"
        ),
    )


def _scope_pressure_total_v1(
    contributions: list[RoutePressureSectionContributionV1],
    section_scope: str,
) -> float | None:
    # Sum one authoritative scope, failing closed when it is incomplete.
    scoped = tuple(
        row for row in contributions
        if str(row.section_scope) == str(section_scope)
    )
    if not scoped:
        return 0.0
    if any(row.section_total_pressure_drop_Pa is None for row in scoped):
        return None
    return sum(float(row.section_total_pressure_drop_Pa) for row in scoped)


def _main_pressure_contribution_v1(
    row: Any,
) -> RoutePressureSectionContributionV1:
    """Adapt one H-S42-A row without recalculating or persisting it."""
    return RoutePressureSectionContributionV1(
        section_id=str(row.section_id),
        order=int(row.order),
        from_label=str(row.from_label),
        to_label=str(row.to_label),
        pressure_gradient_Pa_per_m=float(row.pressure_gradient_Pa_per_m),
        velocity_m_s=float(row.velocity_m_s),
        reynolds_number=float(row.reynolds_number),
        friction_factor=float(row.friction_factor),
        friction_method=str(row.friction_method),
        colebrook_iteration_count=int(row.colebrook_iteration_count),
        colebrook_converged=bool(row.colebrook_converged),
        straight_pressure_drop_Pa=row.straight_pressure_drop_Pa,
        local_pressure_drop_Pa=float(row.local_pressure_drop_Pa or 0.0),
        section_total_pressure_drop_Pa=row.section_total_pressure_drop_Pa,
        status=str(row.status),
        section_scope=str(row.section_kind),
        carried_flow_kg_s=float(row.carried_flow_kg_s),
        pipe_size_label=str(row.pipe_size_label),
        dn=int(row.dn),
        length_m=row.length_m,
        k_total=float(row.k_total),
        material_key=str(getattr(row, "material", "copper") or "copper"),
        material_label=str(
            getattr(row, "material_label", "Copper EN1057")
            or "Copper EN1057"
        ),
        internal_diameter_m=getattr(row, "internal_diameter_m", None),
        material_roughness_m=getattr(row, "material_roughness_m", None),
    )


def _basic_ps_result_pipe_identity_v1(result: Any) -> tuple[str, int]:
    """H-S63-B2B — require exact family and catalogue-size evidence."""

    material_key = str(getattr(result, "material_key", "") or "").strip().lower()
    raw_size_key = getattr(result, "pipe_size_key", None)
    try:
        pipe_size_key = int(raw_size_key)
    except (TypeError, ValueError):
        pipe_size_key = 0
    if not material_key:
        raise ValueError("Basic PS pressure evidence requires material_key")
    if pipe_size_key <= 0:
        raise ValueError("Basic PS pressure evidence requires pipe_size_key")
    return material_key, pipe_size_key


def _local_k_section_length_m_v1(
        project_state: Any,
        *,
        section_id: str,
) -> float | None:
    """
    Read visible/persisted Local K section length.

    Local K remains the length authority for this preview layer.
    """
    intent = getattr(project_state, "hydronic_local_k_intent", None)

    if intent is None:
        return None

    section = getattr(intent, "sections", {}).get(str(section_id))

    if section is None:
        return None

    raw_length = getattr(section, "length_m", None)

    if raw_length is None:
        return None

    return float(raw_length)