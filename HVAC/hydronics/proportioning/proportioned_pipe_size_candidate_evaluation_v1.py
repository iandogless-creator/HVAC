from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    ProportionedPipeSizingAuthorityV1,
    ProportionedPipeSizingCandidateV1,
    ProportionedPipeSizingSectionAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizeCandidateEvaluationV1:
    """
    One deterministic H-S61-B Colebrook evaluation.

    This is candidate evidence only.  It does not alter the committed DN.
    """

    section_id: str
    candidate_dn: int
    candidate_pipe_size_label: str
    material_key: str
    internal_diameter_m: Optional[float]
    carried_flow_kg_s: float

    velocity_m_s: Optional[float]
    maximum_velocity_m_s: float
    velocity_within_limit: bool

    pressure_gradient_Pa_per_m: Optional[float]
    maximum_pressure_gradient_Pa_per_m: float
    pressure_gradient_within_limit: bool

    reynolds_number: Optional[float]
    friction_factor: Optional[float]
    friction_method: str
    colebrook_iteration_count: int
    colebrook_converged: bool

    eligible: bool
    status: str


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizeSectionCandidateResultV1:
    """Smallest acceptable candidate recommendation for one section."""

    section_id: str
    section_scope: str
    route_ids: tuple[str, ...]
    order: int
    from_label: str
    to_label: str
    carried_flow_kg_s: float

    current_dn: int
    current_pipe_size_label: str
    recommended_dn: Optional[int]
    recommended_pipe_size_label: str
    recommendation: str

    candidate_evaluations: tuple[
        ProportionedPipeSizeCandidateEvaluationV1,
        ...,
    ]
    complete: bool
    status: str
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizeCandidateEvaluationResultV1:
    """
    H-S61-B candidate-DN evaluation result.

    `ready` means every committed section has a smallest candidate that passes
    both the accepted velocity and pressure-gradient limits.  It does not mean
    that any committed pipe size has been changed.
    """

    schema: str = "proportioned_pipe_size_candidate_evaluation_v1"
    ready: bool = False
    sections: tuple[ProportionedPipeSizeSectionCandidateResultV1, ...] = ()
    section_count: int = 0
    evaluated_candidate_count: int = 0
    recommended_change_count: int = 0
    status: str = ""
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No ProjectState mutation",
        "No committed DN change",
        "No local-K or route-total pressure recalculation",
        "No pump selection",
        "No valve product selection",
        "No final balancing",
    )
    note: str = (
        "Candidate preview only — the smallest accepted DN passing both "
        "maximum velocity and maximum Δp/m is recommended."
    )


def _candidate_status_v1(
        *,
        converged: bool,
        velocity_within_limit: bool,
        pressure_gradient_within_limit: bool,
) -> str:
    if not converged:
        return "Blocked — Colebrook did not converge"
    if velocity_within_limit and pressure_gradient_within_limit:
        return "Eligible — passes maximum velocity and maximum Δp/m"
    if not velocity_within_limit and not pressure_gradient_within_limit:
        return "Review — exceeds maximum velocity and maximum Δp/m"
    if not velocity_within_limit:
        return "Review — exceeds maximum velocity"
    return "Review — exceeds maximum Δp/m"


def _evaluate_candidate_v1(
        *,
        section: ProportionedPipeSizingSectionAuthorityV1,
        candidate: ProportionedPipeSizingCandidateV1,
        authority: ProportionedPipeSizingAuthorityV1,
) -> ProportionedPipeSizeCandidateEvaluationV1:
    criteria = authority.criteria
    max_velocity = float(section.effective_max_velocity_m_s)
    max_gradient = float(
        section.effective_max_pressure_gradient_Pa_per_m
    )

    try:
        hydraulic = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
            mass_flow_kg_s=float(section.carried_flow_kg_s),
            material=str(candidate.material_key),
            dn=int(candidate.dn),
            length_m=float(section.length_m),
            density_kg_m3=float(criteria.density_kg_m3),
            dynamic_viscosity_pa_s=float(criteria.dynamic_viscosity_Pa_s),
            friction_method=str(criteria.friction_method),
            colebrook_tolerance=float(criteria.colebrook_tolerance),
            colebrook_max_iterations=int(criteria.colebrook_max_iterations),
        )
    except (TypeError, ValueError) as exc:
        return ProportionedPipeSizeCandidateEvaluationV1(
            section_id=str(section.section_id),
            candidate_dn=int(candidate.dn),
            candidate_pipe_size_label=str(candidate.pipe_size_label),
            material_key=str(candidate.material_key),
            internal_diameter_m=None,
            carried_flow_kg_s=float(section.carried_flow_kg_s),
            velocity_m_s=None,
            maximum_velocity_m_s=max_velocity,
            velocity_within_limit=False,
            pressure_gradient_Pa_per_m=None,
            maximum_pressure_gradient_Pa_per_m=max_gradient,
            pressure_gradient_within_limit=False,
            reynolds_number=None,
            friction_factor=None,
            friction_method=str(criteria.friction_method),
            colebrook_iteration_count=0,
            colebrook_converged=False,
            eligible=False,
            status=f"Blocked — candidate hydraulic calculation failed: {exc}",
        )

    tolerance = 1.0e-9
    velocity_within_limit = (
        float(hydraulic.velocity_m_s) <= max_velocity + tolerance
    )
    gradient_within_limit = (
        float(hydraulic.pressure_gradient_pa_per_m)
        <= max_gradient + tolerance
    )
    converged = bool(hydraulic.colebrook_converged)
    eligible = (
        converged
        and velocity_within_limit
        and gradient_within_limit
    )

    return ProportionedPipeSizeCandidateEvaluationV1(
        section_id=str(section.section_id),
        candidate_dn=int(candidate.dn),
        candidate_pipe_size_label=str(candidate.pipe_size_label),
        material_key=str(candidate.material_key),
        internal_diameter_m=float(hydraulic.internal_diameter_m),
        carried_flow_kg_s=float(section.carried_flow_kg_s),
        velocity_m_s=float(hydraulic.velocity_m_s),
        maximum_velocity_m_s=max_velocity,
        velocity_within_limit=velocity_within_limit,
        pressure_gradient_Pa_per_m=float(
            hydraulic.pressure_gradient_pa_per_m
        ),
        maximum_pressure_gradient_Pa_per_m=max_gradient,
        pressure_gradient_within_limit=gradient_within_limit,
        reynolds_number=float(hydraulic.reynolds_number),
        friction_factor=float(hydraulic.selected_friction_factor),
        friction_method=str(hydraulic.friction_method),
        colebrook_iteration_count=int(
            hydraulic.colebrook_iteration_count
        ),
        colebrook_converged=converged,
        eligible=eligible,
        status=_candidate_status_v1(
            converged=converged,
            velocity_within_limit=velocity_within_limit,
            pressure_gradient_within_limit=gradient_within_limit,
        ),
    )


def _section_result_v1(
        *,
        section: ProportionedPipeSizingSectionAuthorityV1,
        authority: ProportionedPipeSizingAuthorityV1,
) -> ProportionedPipeSizeSectionCandidateResultV1:
    candidates = tuple(
        sorted(
            tuple(authority.candidates or ()),
            key=lambda row: (
                int(row.dn),
                str(row.material_key),
                str(row.pipe_size_label),
            ),
        )
    )
    evaluations = tuple(
        _evaluate_candidate_v1(
            section=section,
            candidate=candidate,
            authority=authority,
        )
        for candidate in candidates
    )

    recommended = next(
        (row for row in evaluations if row.eligible),
        None,
    )
    blockers: list[str] = []

    if recommended is None:
        recommendation = "BLOCKED"
        recommended_dn = None
        recommended_label = "—"
        complete = False
        status = (
            "Blocked — no accepted candidate DN passes both maximum "
            "velocity and maximum Δp/m"
        )
        blockers.append(
            f"{section.section_id}: no candidate passes both accepted limits"
        )
    else:
        recommended_dn = int(recommended.candidate_dn)
        recommended_label = str(recommended.candidate_pipe_size_label)
        current_dn = int(section.current_dn)

        if recommended_dn > current_dn:
            recommendation = "INCREASE"
            direction = "increase"
        elif recommended_dn < current_dn:
            recommendation = "DECREASE"
            direction = "decrease"
        else:
            recommendation = "RETAIN"
            direction = "retain"

        complete = True
        status = (
            f"Recommended preview — {direction} at "
            f"{recommended_label}; smallest candidate passing both limits"
        )

    return ProportionedPipeSizeSectionCandidateResultV1(
        section_id=str(section.section_id),
        section_scope=str(section.section_scope),
        route_ids=tuple(str(value) for value in section.route_ids),
        order=int(section.order),
        from_label=str(section.from_label),
        to_label=str(section.to_label),
        carried_flow_kg_s=float(section.carried_flow_kg_s),
        current_dn=int(section.current_dn),
        current_pipe_size_label=str(section.current_pipe_size_label),
        recommended_dn=recommended_dn,
        recommended_pipe_size_label=recommended_label,
        recommendation=recommendation,
        candidate_evaluations=evaluations,
        complete=complete,
        status=status,
        blockers=tuple(blockers),
    )


def build_proportioned_pipe_size_candidate_evaluation_v1(
        authority: ProportionedPipeSizingAuthorityV1 | None,
) -> ProportionedPipeSizeCandidateEvaluationResultV1:
    """
    Evaluate every accepted DN for every committed section using Colebrook.

    Selection rule:
        recommend the smallest candidate DN whose calculated velocity is not
        greater than the section's accepted maximum velocity and whose
        calculated Darcy pressure gradient is not greater than the accepted
        maximum Δp/m.

    This function is deterministic and read-only.  Applying a recommendation
    and recalculating committed section/route results are later stages.
    """
    if not isinstance(authority, ProportionedPipeSizingAuthorityV1):
        return ProportionedPipeSizeCandidateEvaluationResultV1(
            status="Blocked — H-S61-A pipe-sizing authority required",
            blockers=("H-S61-A pipe-sizing authority required",),
        )

    if not authority.ready:
        blockers = tuple(authority.blockers or ()) or (
            "H-S61-A pipe-sizing authority is not ready",
        )
        return ProportionedPipeSizeCandidateEvaluationResultV1(
            status="Blocked — H-S61-A pipe-sizing authority is not ready",
            blockers=blockers,
        )

    if str(authority.criteria.friction_method).strip().lower() != "colebrook":
        return ProportionedPipeSizeCandidateEvaluationResultV1(
            status="Blocked — H-S61-B requires Colebrook friction method",
            blockers=("Colebrook friction method required",),
        )

    if not authority.candidates:
        return ProportionedPipeSizeCandidateEvaluationResultV1(
            status="Blocked — no accepted pipe-size candidates",
            blockers=("Accepted pipe-size candidate family required",),
        )

    if not authority.sections:
        return ProportionedPipeSizeCandidateEvaluationResultV1(
            status="Blocked — no committed section sizing authority",
            blockers=("Committed section sizing authority required",),
        )

    ordered_sections = tuple(
        sorted(
            tuple(authority.sections),
            key=lambda row: (int(row.order), str(row.section_id)),
        )
    )
    section_results = tuple(
        _section_result_v1(section=section, authority=authority)
        for section in ordered_sections
    )
    blockers = tuple(
        blocker
        for section in section_results
        for blocker in section.blockers
    )
    candidate_count = sum(
        len(section.candidate_evaluations)
        for section in section_results
    )
    change_count = sum(
        section.recommendation in {"INCREASE", "DECREASE"}
        for section in section_results
    )
    ready = not blockers and all(
        section.complete for section in section_results
    )

    if ready:
        status = (
            f"Ready — evaluated {candidate_count} Colebrook candidates "
            f"across {len(section_results)} committed sections; "
            f"{change_count} DN changes recommended"
        )
    else:
        blocked_count = sum(
            not section.complete for section in section_results
        )
        status = (
            f"Blocked — {blocked_count} of {len(section_results)} committed "
            "sections have no candidate passing both accepted limits"
        )

    return ProportionedPipeSizeCandidateEvaluationResultV1(
        ready=ready,
        sections=section_results,
        section_count=len(section_results),
        evaluated_candidate_count=candidate_count,
        recommended_change_count=change_count,
        status=status,
        blockers=blockers,
    )
