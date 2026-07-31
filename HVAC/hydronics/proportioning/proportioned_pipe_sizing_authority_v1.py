# ======================================================================
# H-S61-A — Proportioned pipe-sizing authority and criteria
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


DEFAULT_PROPORTIONED_PIPE_MATERIAL_V1 = "copper"
DEFAULT_PROPORTIONED_MAX_VELOCITY_M_S_V1 = 1.0
DEFAULT_PROPORTIONED_MAX_PRESSURE_GRADIENT_PA_PER_M_V1 = 200.0
DEFAULT_PROPORTIONED_MIN_DN_V1 = 10
DEFAULT_PROPORTIONED_MAX_DN_V1 = 54


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizingCriteriaV1:
    """
    Accepted design criteria for later Proportioned pipe-size selection.

    H-S61-A stores and validates criteria only. H-S61-B will apply these
    limits to candidate sizes.
    """

    schema: str = "proportioned_pipe_sizing_criteria_v1"
    # Current family describes committed section evidence. `material_key`
    # remains the proposed candidate family for API compatibility.
    current_material_key: str = DEFAULT_PROPORTIONED_PIPE_MATERIAL_V1
    current_material_source: str = "H-S61-B2A current family"
    material_key: str = DEFAULT_PROPORTIONED_PIPE_MATERIAL_V1
    material_source: str = "H-S61-B2A proposed family"
    default_max_velocity_m_s: float = (
        DEFAULT_PROPORTIONED_MAX_VELOCITY_M_S_V1
    )
    max_velocity_source: str = "Environment design criterion"
    max_pressure_gradient_Pa_per_m: float = (
        DEFAULT_PROPORTIONED_MAX_PRESSURE_GRADIENT_PA_PER_M_V1
    )
    max_pressure_gradient_source: str = "H-S61-A accepted default"
    minimum_dn: int = DEFAULT_PROPORTIONED_MIN_DN_V1
    maximum_dn: int = DEFAULT_PROPORTIONED_MAX_DN_V1
    density_kg_m3: float = 998.0
    dynamic_viscosity_Pa_s: float = 0.001
    friction_method: str = "colebrook"
    colebrook_tolerance: float = 1.0e-6
    colebrook_max_iterations: int = 100


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizingCandidateV1:
    material_key: str
    material_label: str
    dn: int
    pipe_size_label: str
    outside_diameter_m: float
    internal_diameter_m: float
    roughness_m: float


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizingSectionAuthorityV1:
    """One unique committed section with resolved future sizing limits."""

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
    current_velocity_m_s: float
    current_pressure_gradient_Pa_per_m: float
    effective_max_velocity_m_s: float
    max_velocity_source: str
    effective_max_pressure_gradient_Pa_per_m: float
    max_pressure_gradient_source: str
    current_dn_in_candidate_family: bool
    current_velocity_within_limit: bool
    current_pressure_gradient_within_limit: bool
    status: str
    current_material_key: str = DEFAULT_PROPORTIONED_PIPE_MATERIAL_V1
    current_material_label: str = "Copper EN1057"
    current_internal_diameter_m: float = 0.0


@dataclass(frozen=True, slots=True)
class ProportionedPipeSizingAuthorityV1:
    """
    Read-only sizing authority derived from frozen committed sections.

    This is not a sizing result. It freezes the candidate family and the
    criteria H-S61-B may apply later.
    """

    schema: str = "proportioned_pipe_sizing_authority_v1"
    ready: bool = False
    criteria: ProportionedPipeSizingCriteriaV1 | None = None
    candidates: tuple[ProportionedPipeSizingCandidateV1, ...] = ()
    sections: tuple[ProportionedPipeSizingSectionAuthorityV1, ...] = ()
    section_count: int = 0
    status: str = "Proportioned pipe-sizing authority not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No candidate pipe size selected",
        "No committed or ProjectState pipe size changed",
        "No friction or pressure-drop recalculation",
        "No route pressure total recalculated",
        "No balancing-point duty recalculated",
        "No pump or valve product selected",
        "No ProjectState mutation or persistence",
    )
    note: str = (
        "Frozen criteria and committed section input authority only; "
        "H-S61-B remains responsible for candidate evaluation."
    )


def build_proportioned_pipe_sizing_authority_v1(
        snapshot: ProportionedBasisSnapshotV1 | None,
        *,
        criteria: ProportionedPipeSizingCriteriaV1 | None,
        section_max_velocity_overrides_m_s: (
            Mapping[str, float] | None
        ) = None,
) -> ProportionedPipeSizingAuthorityV1:
    """
    Validate and freeze the criteria available to later pipe sizing.

    Existing committed velocity and pressure-gradient values are classified
    against the accepted limits only; they are never recalculated here.
    """
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        return _blocked_v1(
            "H-S26-G committed proportioning snapshot required",
            criteria=criteria,
        )
    if not isinstance(criteria, ProportionedPipeSizingCriteriaV1):
        return _blocked_v1(
            "H-S61-A Proportioned pipe-sizing criteria required"
        )

    authority = snapshot.hydraulic_input_authority
    if not isinstance(
            authority,
            CommittedProportioningHydraulicInputAuthorityV1,
    ):
        return _blocked_v1(
            "H-S54-A committed hydraulic-input authority required",
            criteria=criteria,
        )
    if not authority.ready:
        return _blocked_v1(
            "H-S54-A committed hydraulic-input authority is not ready",
            *tuple(authority.blockers or ()),
            criteria=criteria,
        )

    blockers = _criteria_blockers_v1(criteria)
    candidates, candidate_blockers = _candidate_family_v1(criteria)
    blockers.extend(candidate_blockers)

    current_material_key = _text_v1(
        criteria.current_material_key
    ).lower()
    current_material = get_material(current_material_key)
    if current_material is None:
        blockers.append(
            f"Unknown current pipe material: "
            f"{current_material_key or '—'}"
        )
        current_material_dns: set[int] = set()
    else:
        current_material_dns = {
            int(value) for value in current_material.sizes
        }

    raw_overrides = section_max_velocity_overrides_m_s or {}
    if not isinstance(raw_overrides, Mapping):
        blockers.append(
            "Section maximum-velocity overrides must be a mapping"
        )
        raw_overrides = {}

    sections = tuple(authority.sections or ())
    if not sections:
        blockers.append("At least one committed hydraulic section required")

    section_ids: set[str] = set()
    for source in sections:
        section_id = _text_v1(getattr(source, "section_id", ""))
        if not section_id:
            blockers.append("Every committed section requires section_id")
            continue
        if section_id in section_ids:
            blockers.append(f"Duplicate committed section: {section_id}")
            continue
        section_ids.add(section_id)

    clean_overrides: dict[str, float] = {}
    for raw_section_id, raw_value in raw_overrides.items():
        section_id = _text_v1(raw_section_id)
        if not section_id:
            blockers.append("Section velocity override requires section_id")
            continue
        if section_id not in section_ids:
            blockers.append(
                f"{section_id}: velocity override has no committed section"
            )
            continue
        value = _positive_v1(
            raw_value,
            label=f"{section_id}: maximum velocity override",
            blockers=blockers,
        )
        if value is not None:
            clean_overrides[section_id] = value

    output: list[ProportionedPipeSizingSectionAuthorityV1] = []
    for source in sections:
        section_id = _text_v1(getattr(source, "section_id", ""))
        if not section_id or section_id not in section_ids:
            continue
        try:
            current_dn = int(getattr(source, "dn"))
        except (TypeError, ValueError):
            blockers.append(f"{section_id}: numeric current DN required")
            continue

        current_in_family = current_dn in current_material_dns
        if not current_in_family:
            blockers.append(
                f"{section_id}: current DN{current_dn} is outside the "
                f"current {current_material_key or '—'} material family"
            )

        carried_flow = _positive_v1(
            getattr(source, "carried_flow_kg_s", None),
            label=f"{section_id}: carried flow",
            blockers=blockers,
        )
        length = _positive_v1(
            getattr(source, "length_m", None),
            label=f"{section_id}: length",
            blockers=blockers,
        )
        k_total = _non_negative_v1(
            getattr(source, "k_total", None),
            label=f"{section_id}: Local K total",
            blockers=blockers,
        )
        current_velocity = _positive_v1(
            getattr(source, "velocity_m_s", None),
            label=f"{section_id}: current velocity",
            blockers=blockers,
        )
        current_gradient = _positive_v1(
            getattr(source, "pressure_gradient_Pa_per_m", None),
            label=f"{section_id}: current pressure gradient",
            blockers=blockers,
        )
        if None in (
                carried_flow,
                length,
                k_total,
                current_velocity,
                current_gradient,
        ):
            continue

        local_velocity = clean_overrides.get(section_id)
        max_velocity = (
            local_velocity
            if local_velocity is not None
            else float(criteria.default_max_velocity_m_s)
        )
        velocity_source = (
            "Local section override"
            if local_velocity is not None
            else criteria.max_velocity_source
        )
        velocity_ok = current_velocity <= max_velocity
        gradient_ok = (
            current_gradient
            <= float(criteria.max_pressure_gradient_Pa_per_m)
        )

        if velocity_ok and gradient_ok:
            status = "Ready — current DN satisfies accepted criteria"
        else:
            reasons: list[str] = []
            if not velocity_ok:
                reasons.append("velocity exceeds accepted maximum")
            if not gradient_ok:
                reasons.append("Δp/m exceeds accepted maximum")
            status = "Review — " + "; ".join(reasons)

        current_size = (
            current_material.sizes.get(current_dn)
            if current_material is not None
            else None
        )
        current_material_label = (
            str(current_material.name)
            if current_material is not None
            else "—"
        )
        current_internal_diameter_m = (
            float(current_size.id_mm) / 1000.0
            if current_size is not None
            else 0.0
        )

        output.append(
            ProportionedPipeSizingSectionAuthorityV1(
                section_id=section_id,
                section_scope=_text_v1(
                    getattr(source, "section_scope", "")
                ),
                route_ids=tuple(
                    _text_v1(value)
                    for value in tuple(
                        getattr(source, "route_ids", ()) or ()
                    )
                    if _text_v1(value)
                ),
                order=int(getattr(source, "order", 0)),
                from_label=_text_v1(getattr(source, "from_label", "")),
                to_label=_text_v1(getattr(source, "to_label", "")),
                carried_flow_kg_s=carried_flow,
                length_m=length,
                k_total=k_total,
                current_dn=current_dn,
                current_pipe_size_label=_text_v1(
                    getattr(source, "pipe_size_label", "")
                ),
                current_velocity_m_s=current_velocity,
                current_pressure_gradient_Pa_per_m=current_gradient,
                effective_max_velocity_m_s=max_velocity,
                max_velocity_source=velocity_source,
                effective_max_pressure_gradient_Pa_per_m=float(
                    criteria.max_pressure_gradient_Pa_per_m
                ),
                max_pressure_gradient_source=(
                    criteria.max_pressure_gradient_source
                ),
                current_dn_in_candidate_family=current_in_family,
                current_velocity_within_limit=velocity_ok,
                current_pressure_gradient_within_limit=gradient_ok,
                status=status,
                current_material_key=current_material_key,
                current_material_label=current_material_label,
                current_internal_diameter_m=current_internal_diameter_m,
            )
        )

    clean = _unique_v1(blockers)
    if clean:
        return _blocked_v1(
            *clean,
            criteria=criteria,
            candidates=candidates,
        )

    output.sort(key=lambda row: (row.order, row.section_id))
    review_count = sum(
        1
        for row in output
        if not (
            row.current_velocity_within_limit
            and row.current_pressure_gradient_within_limit
        )
    )
    return ProportionedPipeSizingAuthorityV1(
        ready=True,
        criteria=criteria,
        candidates=candidates,
        sections=tuple(output),
        section_count=len(output),
        status=(
            f"Ready — {len(output)} committed section(s), "
            f"{len(candidates)} candidate size(s); "
            f"{review_count} current section(s) require resizing review"
        ),
    )


def _criteria_blockers_v1(
        criteria: ProportionedPipeSizingCriteriaV1,
) -> list[str]:
    blockers: list[str] = []
    if not _text_v1(criteria.current_material_key):
        blockers.append("Current pipe material key required")
    if not _text_v1(criteria.current_material_source):
        blockers.append("Current pipe material source required")
    if not _text_v1(criteria.material_key):
        blockers.append("Proposed pipe material key required")
    if not _text_v1(criteria.material_source):
        blockers.append("Proposed pipe material source required")
    if not _text_v1(criteria.max_velocity_source):
        blockers.append("Maximum-velocity source required")
    if not _text_v1(criteria.max_pressure_gradient_source):
        blockers.append("Maximum-pressure-gradient source required")
    if _text_v1(criteria.friction_method).lower() != "colebrook":
        blockers.append("Proportioned pipe sizing requires Colebrook")

    _positive_v1(
        criteria.default_max_velocity_m_s,
        label="Default maximum velocity",
        blockers=blockers,
    )
    _positive_v1(
        criteria.max_pressure_gradient_Pa_per_m,
        label="Maximum pressure gradient",
        blockers=blockers,
    )
    _positive_v1(
        criteria.density_kg_m3,
        label="Fluid density",
        blockers=blockers,
    )
    _positive_v1(
        criteria.dynamic_viscosity_Pa_s,
        label="Dynamic viscosity",
        blockers=blockers,
    )
    _positive_v1(
        criteria.colebrook_tolerance,
        label="Colebrook tolerance",
        blockers=blockers,
    )
    try:
        maximum_iterations = int(criteria.colebrook_max_iterations)
    except (TypeError, ValueError):
        maximum_iterations = 0
    if maximum_iterations <= 0:
        blockers.append("Positive Colebrook maximum iterations required")

    try:
        minimum_dn = int(criteria.minimum_dn)
        maximum_dn = int(criteria.maximum_dn)
    except (TypeError, ValueError):
        minimum_dn = 0
        maximum_dn = -1
        blockers.append("Numeric minimum and maximum DN required")
    if minimum_dn <= 0:
        blockers.append("Positive minimum DN required")
    if maximum_dn < minimum_dn:
        blockers.append("Maximum DN must not be below minimum DN")
    return blockers


def _candidate_family_v1(
        criteria: ProportionedPipeSizingCriteriaV1,
) -> tuple[
    tuple[ProportionedPipeSizingCandidateV1, ...],
    list[str],
]:
    blockers: list[str] = []
    material_key = _text_v1(criteria.material_key).lower()
    material = get_material(material_key)
    if material is None:
        return (), [f"Unknown pipe material: {material_key or '—'}"]

    try:
        minimum_dn = int(criteria.minimum_dn)
        maximum_dn = int(criteria.maximum_dn)
    except (TypeError, ValueError):
        return (), ["Numeric minimum and maximum DN required"]

    roughness_m = float(material.roughness_mm) / 1000.0
    candidates: list[ProportionedPipeSizingCandidateV1] = []
    for dn, size in sorted(material.sizes.items()):
        if not (
                minimum_dn
                <= int(dn)
                <= maximum_dn
        ):
            continue
        if float(size.id_mm) <= 0.0:
            blockers.append(f"DN{dn}: positive internal diameter required")
            continue
        candidates.append(
            ProportionedPipeSizingCandidateV1(
                material_key=material_key,
                material_label=str(material.name),
                dn=int(dn),
                pipe_size_label=_candidate_pipe_size_label_v1(
                    material_key=material_key,
                    dn=int(dn),
                    outside_diameter_mm=float(size.od_mm),
                    thickness_mm=float(size.thickness_mm),
                ),
                outside_diameter_m=float(size.od_mm) / 1000.0,
                internal_diameter_m=float(size.id_mm) / 1000.0,
                roughness_m=roughness_m,
            )
        )
    if not candidates:
        blockers.append("Accepted pipe candidate family is empty")
    return tuple(candidates), blockers


def _candidate_pipe_size_label_v1(
        *,
        material_key: str,
        dn: int,
        outside_diameter_mm: float,
        thickness_mm: float,
) -> str:
    if material_key in {"mlcp", "pex"}:
        return (
            f"{outside_diameter_mm:g}×{thickness_mm:g} mm"
        )
    return f"{dn} mm"


def _blocked_v1(
        *blockers: str,
        criteria: ProportionedPipeSizingCriteriaV1 | None = None,
        candidates: tuple[ProportionedPipeSizingCandidateV1, ...] = (),
) -> ProportionedPipeSizingAuthorityV1:
    clean = _unique_v1(blockers)
    return ProportionedPipeSizingAuthorityV1(
        ready=False,
        criteria=criteria,
        candidates=candidates,
        blockers=clean,
        status="Blocked — " + "; ".join(clean),
    )


def _positive_v1(
        value: object,
        *,
        label: str,
        blockers: list[str],
) -> float | None:
    result = _finite_v1(value)
    if result is None or result <= 0.0:
        blockers.append(f"{label} must be finite and greater than zero")
        return None
    return result


def _non_negative_v1(
        value: object,
        *,
        label: str,
        blockers: list[str],
) -> float | None:
    result = _finite_v1(value)
    if result is None or result < 0.0:
        blockers.append(f"{label} must be finite and non-negative")
        return None
    return result


def _finite_v1(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in output:
            output.append(text)
    return tuple(output)
