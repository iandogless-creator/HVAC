from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_size_candidate_evaluation_v1 import (
    ProportionedPipeSizeCandidateEvaluationResultV1,
    ProportionedPipeSizeSectionCandidateResultV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    ProportionedPipeSizingAuthorityV1,
    ProportionedPipeSizingCandidateV1,
    ProportionedPipeSizingSectionAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class ProportionedResizedSectionHydraulicProjectionV1:
    """Read-only hydraulic projection for one recommended section DN."""

    section_id: str
    section_scope: str
    route_ids: tuple[str, ...]
    order: int
    from_label: str
    to_label: str

    carried_flow_kg_s: float
    length_m: float
    k_total: float

    current_dn: int
    current_pipe_size_label: str
    projected_dn: int
    projected_pipe_size_label: str
    recommendation: str

    internal_diameter_m: float
    velocity_m_s: float
    maximum_velocity_m_s: float
    velocity_within_limit: bool
    pressure_gradient_Pa_per_m: float
    maximum_pressure_gradient_Pa_per_m: float
    pressure_gradient_within_limit: bool

    straight_pressure_drop_Pa: float
    local_pressure_drop_Pa: float
    section_total_pressure_drop_Pa: float

    reynolds_number: float
    friction_factor: float
    friction_method: str
    colebrook_iteration_count: int
    colebrook_converged: bool
    status: str
    current_material_key: str = "copper"
    current_material_label: str = "Copper EN1057"
    current_internal_diameter_m: float = 0.0
    projected_material_key: str = "copper"
    projected_material_label: str = "Copper EN1057"


@dataclass(frozen=True, slots=True)
class ProportionedResizedRouteHydraulicProjectionV1:
    """Raw resized pipe/local-K route result before point reconciliation."""

    route_id: str
    section_ids: tuple[str, ...]
    section_count: int
    straight_pressure_drop_total_Pa: float
    local_pressure_drop_total_Pa: float
    route_pressure_drop_total_Pa: float
    controlling_target_Pa: float
    required_added_dp_Pa: float
    rank: int
    is_controlling: bool
    status: str


@dataclass(frozen=True, slots=True)
class ProportionedPipeResizingHydraulicProjectionV1:
    """
    H-S61-C resized section and route hydraulic projection.

    The projection applies H-S61-B recommended DNs only in this immutable
    result.  It does not replace the committed DN evidence.
    """

    schema: str = "proportioned_pipe_resizing_hydraulic_projection_v1"
    ready: bool = False
    sections: tuple[
        ProportionedResizedSectionHydraulicProjectionV1,
        ...,
    ] = ()
    routes: tuple[
        ProportionedResizedRouteHydraulicProjectionV1,
        ...,
    ] = ()
    section_count: int = 0
    route_count: int = 0
    controlling_route_id: Optional[str] = None
    controlling_target_Pa: Optional[float] = None
    status: str = ""
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No ProjectState mutation",
        "No committed material or DN replacement",
        "No committed DN replacement",
        "No committed balancing-point allocation reuse",
        "No point-level valve-duty reconciliation",
        "No pump selection",
        "No valve product selection",
        "No final balancing",
    )
    note: str = (
        "Read-only resized hydraulic projection — straight-pipe and local-K "
        "losses are recalculated before later point-level reconciliation."
    )


def _blocked_v1(
        status: str,
        *blockers: str,
) -> ProportionedPipeResizingHydraulicProjectionV1:
    return ProportionedPipeResizingHydraulicProjectionV1(
        status=status,
        blockers=tuple(blockers),
    )


def _normalise_near_zero_v1(value: float) -> float:
    return 0.0 if abs(float(value)) < 0.05 else float(value)


def _candidate_by_dn_v1(
        authority: ProportionedPipeSizingAuthorityV1,
) -> dict[int, ProportionedPipeSizingCandidateV1]:
    result: dict[int, ProportionedPipeSizingCandidateV1] = {}
    for candidate in tuple(authority.candidates or ()):
        dn = int(candidate.dn)
        if dn in result:
            raise ValueError(f"Duplicate accepted candidate DN: {dn}")
        result[dn] = candidate
    return result


def _sections_by_id_v1(
        authority: ProportionedPipeSizingAuthorityV1,
) -> dict[str, ProportionedPipeSizingSectionAuthorityV1]:
    result: dict[str, ProportionedPipeSizingSectionAuthorityV1] = {}
    for section in tuple(authority.sections or ()):
        section_id = str(section.section_id or "").strip()
        if not section_id:
            raise ValueError("Committed sizing section requires section_id")
        if section_id in result:
            raise ValueError(f"Duplicate committed section_id: {section_id}")
        result[section_id] = section
    return result


def _recommendations_by_id_v1(
        candidate_evaluation: (
            ProportionedPipeSizeCandidateEvaluationResultV1
        ),
) -> dict[str, ProportionedPipeSizeSectionCandidateResultV1]:
    result: dict[str, ProportionedPipeSizeSectionCandidateResultV1] = {}
    for section in tuple(candidate_evaluation.sections or ()):
        section_id = str(section.section_id or "").strip()
        if not section_id:
            raise ValueError("Candidate result requires section_id")
        if section_id in result:
            raise ValueError(f"Duplicate candidate section_id: {section_id}")
        result[section_id] = section
    return result


def _project_section_v1(
        *,
        authority: ProportionedPipeSizingAuthorityV1,
        section: ProportionedPipeSizingSectionAuthorityV1,
        recommendation: ProportionedPipeSizeSectionCandidateResultV1,
        candidate_by_dn: dict[int, ProportionedPipeSizingCandidateV1],
) -> ProportionedResizedSectionHydraulicProjectionV1:
    if not recommendation.complete or recommendation.recommended_dn is None:
        raise ValueError(
            f"{section.section_id}: complete H-S61-B recommendation required"
        )

    projected_dn = int(recommendation.recommended_dn)
    candidate = candidate_by_dn.get(projected_dn)
    if candidate is None:
        raise ValueError(
            f"{section.section_id}: recommended DN{projected_dn} is not in "
            "the accepted candidate family"
        )

    route_ids = tuple(
        dict.fromkeys(
            str(route_id or "").strip()
            for route_id in tuple(section.route_ids or ())
            if str(route_id or "").strip()
        )
    )
    if not route_ids:
        raise ValueError(
            f"{section.section_id}: committed route membership required"
        )

    criteria = authority.criteria
    hydraulic = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=float(section.carried_flow_kg_s),
        material=str(candidate.material_key),
        dn=projected_dn,
        length_m=float(section.length_m),
        density_kg_m3=float(criteria.density_kg_m3),
        dynamic_viscosity_pa_s=float(criteria.dynamic_viscosity_Pa_s),
        friction_method=str(criteria.friction_method),
        colebrook_tolerance=float(criteria.colebrook_tolerance),
        colebrook_max_iterations=int(criteria.colebrook_max_iterations),
    )

    if not hydraulic.colebrook_converged:
        raise ValueError(
            f"{section.section_id}: projected Colebrook calculation "
            "did not converge"
        )

    current_material_key = str(
        getattr(section, "current_material_key", "")
        or getattr(criteria, "current_material_key", "")
        or "copper"
    ).strip().lower()
    current_material = get_material(current_material_key)
    current_size = (
        current_material.sizes.get(int(section.current_dn))
        if current_material is not None
        else None
    )
    if current_size is None:
        raise ValueError(
            f"{section.section_id}: current material/size evidence required"
        )
    current_internal_diameter_m = float(
        getattr(section, "current_internal_diameter_m", 0.0)
        or (float(current_size.id_mm) / 1000.0)
    )

    density = float(criteria.density_kg_m3)
    k_total = float(section.k_total)
    local_pressure_drop = (
        k_total * density * float(hydraulic.velocity_m_s) ** 2 / 2.0
    )
    straight_pressure_drop = float(hydraulic.pressure_drop_pa)
    section_total = straight_pressure_drop + local_pressure_drop

    max_velocity = float(section.effective_max_velocity_m_s)
    max_gradient = float(
        section.effective_max_pressure_gradient_Pa_per_m
    )
    tolerance = 1.0e-9
    velocity_ok = (
        float(hydraulic.velocity_m_s) <= max_velocity + tolerance
    )
    gradient_ok = (
        float(hydraulic.pressure_gradient_pa_per_m)
        <= max_gradient + tolerance
    )
    if not velocity_ok or not gradient_ok:
        raise ValueError(
            f"{section.section_id}: recommended DN no longer passes both "
            "accepted limits"
        )

    for value, label in (
        (straight_pressure_drop, "straight pressure drop"),
        (local_pressure_drop, "local pressure drop"),
        (section_total, "section total pressure drop"),
    ):
        if not isfinite(value) or value < 0.0:
            raise ValueError(
                f"{section.section_id}: invalid projected {label}"
            )

    return ProportionedResizedSectionHydraulicProjectionV1(
        section_id=str(section.section_id),
        section_scope=str(section.section_scope),
        route_ids=route_ids,
        order=int(section.order),
        from_label=str(section.from_label),
        to_label=str(section.to_label),
        carried_flow_kg_s=float(section.carried_flow_kg_s),
        length_m=float(section.length_m),
        k_total=k_total,
        current_dn=int(section.current_dn),
        current_pipe_size_label=str(section.current_pipe_size_label),
        projected_dn=projected_dn,
        projected_pipe_size_label=str(
            recommendation.recommended_pipe_size_label
        ),
        recommendation=str(recommendation.recommendation),
        internal_diameter_m=float(hydraulic.internal_diameter_m),
        velocity_m_s=float(hydraulic.velocity_m_s),
        maximum_velocity_m_s=max_velocity,
        velocity_within_limit=velocity_ok,
        pressure_gradient_Pa_per_m=float(
            hydraulic.pressure_gradient_pa_per_m
        ),
        maximum_pressure_gradient_Pa_per_m=max_gradient,
        pressure_gradient_within_limit=gradient_ok,
        straight_pressure_drop_Pa=straight_pressure_drop,
        local_pressure_drop_Pa=local_pressure_drop,
        section_total_pressure_drop_Pa=section_total,
        reynolds_number=float(hydraulic.reynolds_number),
        friction_factor=float(hydraulic.selected_friction_factor),
        friction_method=str(hydraulic.friction_method),
        colebrook_iteration_count=int(
            hydraulic.colebrook_iteration_count
        ),
        colebrook_converged=bool(hydraulic.colebrook_converged),
        status=(
            "Projected — recommended material/size passes both limits; "
            "straight-pipe and local-K Δp recalculated"
        ),
        current_material_key=current_material_key,
        current_material_label=str(current_material.name),
        current_internal_diameter_m=current_internal_diameter_m,
        projected_material_key=str(candidate.material_key),
        projected_material_label=str(candidate.material_label),
    )


def _build_routes_v1(
        sections: tuple[
            ProportionedResizedSectionHydraulicProjectionV1,
            ...,
        ],
) -> tuple[ProportionedResizedRouteHydraulicProjectionV1, ...]:
    route_ids = sorted(
        {
            route_id
            for section in sections
            for route_id in section.route_ids
        }
    )
    raw: list[tuple[str, tuple[
        ProportionedResizedSectionHydraulicProjectionV1,
        ...,
    ], float, float, float]] = []

    for route_id in route_ids:
        route_sections = tuple(
            section
            for section in sections
            if route_id in section.route_ids
        )
        straight_total = sum(
            section.straight_pressure_drop_Pa
            for section in route_sections
        )
        local_total = sum(
            section.local_pressure_drop_Pa
            for section in route_sections
        )
        total = sum(
            section.section_total_pressure_drop_Pa
            for section in route_sections
        )
        raw.append(
            (
                route_id,
                route_sections,
                straight_total,
                local_total,
                total,
            )
        )

    if not raw:
        return ()

    target = max(row[4] for row in raw)
    ranked_ids = {
        row[0]: rank
        for rank, row in enumerate(
            sorted(raw, key=lambda value: (-value[4], value[0])),
            start=1,
        )
    }
    controlling_route_id = min(
        row[0] for row in raw if abs(row[4] - target) < 1.0e-9
    )

    routes: list[ProportionedResizedRouteHydraulicProjectionV1] = []
    for route_id, route_sections, straight, local, total in raw:
        is_controlling = route_id == controlling_route_id
        required_added = _normalise_near_zero_v1(target - total)
        if is_controlling:
            status = (
                "Projected controlling route — no added Δp required"
            )
        else:
            status = (
                "Projected below controlling route — point-level "
                "reconciliation required"
            )

        routes.append(
            ProportionedResizedRouteHydraulicProjectionV1(
                route_id=route_id,
                section_ids=tuple(
                    section.section_id for section in route_sections
                ),
                section_count=len(route_sections),
                straight_pressure_drop_total_Pa=straight,
                local_pressure_drop_total_Pa=local,
                route_pressure_drop_total_Pa=total,
                controlling_target_Pa=target,
                required_added_dp_Pa=required_added,
                rank=ranked_ids[route_id],
                is_controlling=is_controlling,
                status=status,
            )
        )

    return tuple(sorted(routes, key=lambda row: row.route_id))


def build_proportioned_pipe_resizing_hydraulic_projection_v1(
        *,
        authority: ProportionedPipeSizingAuthorityV1 | None,
        candidate_evaluation: (
            ProportionedPipeSizeCandidateEvaluationResultV1 | None
        ),
) -> ProportionedPipeResizingHydraulicProjectionV1:
    """
    Apply recommended DNs in an immutable projection and rebuild hydraulics.

    Section Δp:
        Colebrook/Darcy straight-pipe loss
        + K × ρv²/2 local loss

    Route Δp:
        sum each physical section once for every route listed in that
        section's committed route membership.

    The returned route shortfall is evidence for H-S61-D.  Existing committed
    balancing-point allocations are deliberately not added here because a DN
    change makes their former duty stale.
    """
    if not isinstance(authority, ProportionedPipeSizingAuthorityV1):
        return _blocked_v1(
            "Blocked — H-S61-A pipe-sizing authority required",
            "H-S61-A pipe-sizing authority required",
        )
    if not authority.ready:
        return _blocked_v1(
            "Blocked — H-S61-A pipe-sizing authority is not ready",
            *(tuple(authority.blockers or ()) or (
                "H-S61-A pipe-sizing authority is not ready",
            )),
        )
    if not isinstance(
            candidate_evaluation,
            ProportionedPipeSizeCandidateEvaluationResultV1,
    ):
        return _blocked_v1(
            "Blocked — H-S61-B candidate evaluation required",
            "H-S61-B candidate evaluation required",
        )
    if not candidate_evaluation.ready:
        return _blocked_v1(
            "Blocked — H-S61-B candidate evaluation is not ready",
            *(tuple(candidate_evaluation.blockers or ()) or (
                "H-S61-B candidate evaluation is not ready",
            )),
        )

    try:
        authority_sections = _sections_by_id_v1(authority)
        recommendations = _recommendations_by_id_v1(candidate_evaluation)
        candidate_by_dn = _candidate_by_dn_v1(authority)

        if set(authority_sections) != set(recommendations):
            raise ValueError(
                "H-S61-A section identities must match H-S61-B "
                "recommendation identities"
            )

        projected_sections = tuple(
            _project_section_v1(
                authority=authority,
                section=authority_sections[section_id],
                recommendation=recommendations[section_id],
                candidate_by_dn=candidate_by_dn,
            )
            for section_id in sorted(
                authority_sections,
                key=lambda value: (
                    int(authority_sections[value].order),
                    value,
                ),
            )
        )
        routes = _build_routes_v1(projected_sections)
        if not routes:
            raise ValueError("Projected route membership required")
    except (TypeError, ValueError) as exc:
        return _blocked_v1(
            f"Blocked — resized hydraulic projection failed: {exc}",
            str(exc),
        )

    controlling = next(row for row in routes if row.is_controlling)
    return ProportionedPipeResizingHydraulicProjectionV1(
        ready=True,
        sections=projected_sections,
        routes=routes,
        section_count=len(projected_sections),
        route_count=len(routes),
        controlling_route_id=controlling.route_id,
        controlling_target_Pa=controlling.controlling_target_Pa,
        status=(
            f"Ready — recalculated {len(projected_sections)} resized "
            f"sections across {len(routes)} routes including local-K losses"
        ),
    )
