# ======================================================================
# HVAC/hydronics/proportioning/balancing_point_method_candidate_mapping_v1.py
# H-S44-C — Conserved balancing-point method candidates
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
    balancing_method_design_model_to_dict_v1,
    build_balancing_method_design_model_v1,
)
from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
)


@dataclass(frozen=True, slots=True)
class BalancingPointMethodCandidateV1:
    """One H-S44 point-scoped balancing-method candidate."""

    balancing_point_id: str
    point_scope: str
    point_role: str
    label: str
    parent_balancing_point_id: str
    anchor_section_id: str
    downstream_route_ids: tuple[str, ...]
    is_shared: bool
    is_route_exclusive: bool

    method_id: str
    method_label: str
    ready: bool
    point_flow_kg_s: float | None
    required_added_dp_pa: float | None
    resistance_pa_per_kg_s2: float | None
    status: str
    blockers: tuple[str, ...] = ()
    source_allocation_status: str = ""
    note: str = ""


@dataclass(frozen=True, slots=True)
class BalancingPointMethodCandidateMappingV1:
    """
    H-S44-C point-scoped candidate mapping.

    It consumes only a ready H-S44-B projection whose route burdens are
    conserved. It does not select a valve product, calculate Kv/Kvs, choose
    lockshield turns, select a pump, resize pipe, persist intent, perform
    final balancing, or mutate ProjectState.
    """

    schema: str = "balancing_point_method_candidate_mapping_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    candidates: tuple[BalancingPointMethodCandidateV1, ...] = ()
    design_model: dict[str, Any] | None = None
    exclusions: tuple[str, ...] = (
        "No valve product selected",
        "No Kv or Kvs selected",
        "No lockshield turn count",
        "No pump selected",
        "No final balancing",
        "No pipe resizing",
        "No persistence mutation",
        "No ProjectState mutation",
    )
    note: str = (
        "Point-scoped candidate evidence only; shared and route-exclusive "
        "topology remains explicit."
    )


def build_balancing_point_method_candidate_mapping_v1(
    allocation: BalancingPointResistanceAllocationProjectionV1 | None,
    *,
    dp_tolerance_pa: float = 0.05,
) -> BalancingPointMethodCandidateMappingV1:
    """Map conserved H-S44-B point allocations to method candidates."""

    design_model = balancing_method_design_model_to_dict_v1(
        build_balancing_method_design_model_v1()
    )
    if allocation is None:
        return _blocked_mapping(
            "H-S44-B balancing-point allocation required",
            design_model=design_model,
        )
    if not allocation.ready:
        return _blocked_mapping(
            "H-S44-B balancing-point allocation is not ready",
            *tuple(allocation.blockers or ()),
            design_model=design_model,
        )
    if dp_tolerance_pa < 0.0:
        return _blocked_mapping(
            "dp_tolerance_pa must be zero or greater",
            design_model=design_model,
        )

    conservation = tuple(allocation.route_conservation or ())
    unconserved = tuple(
        str(row.route_id or "")
        for row in conservation
        if not bool(row.conserved)
    )
    if not conservation:
        return _blocked_mapping(
            "H-S44-B route conservation evidence required",
            design_model=design_model,
        )
    if unconserved:
        return _blocked_mapping(
            "Unconserved H-S44-B route burdens: " + ", ".join(unconserved),
            design_model=design_model,
        )

    rows = tuple(allocation.rows or ())
    if not rows:
        return _blocked_mapping(
            "H-S44-B balancing-point allocation rows required",
            design_model=design_model,
        )
    point_ids = tuple(str(row.balancing_point_id or "") for row in rows)
    if any(not point_id for point_id in point_ids):
        return _blocked_mapping(
            "Every H-S44-B row requires balancing_point_id",
            design_model=design_model,
        )
    duplicates = sorted(
        {point_id for point_id in point_ids if point_ids.count(point_id) > 1}
    )
    if duplicates:
        return _blocked_mapping(
            "Duplicate H-S44-B balancing_point_id values: "
            + ", ".join(duplicates),
            design_model=design_model,
        )

    candidates = tuple(
        _candidate_from_allocation_v1(
            row,
            dp_tolerance_pa=dp_tolerance_pa,
        )
        for row in rows
    )
    blockers = tuple(
        f"{candidate.balancing_point_id}: {blocker}"
        for candidate in candidates
        for blocker in candidate.blockers
    )
    ready = not blockers
    return BalancingPointMethodCandidateMappingV1(
        ready=ready,
        status=(
            "Ready — conserved balancing-point method candidates mapped"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        candidates=candidates,
        design_model=design_model,
    )


def _candidate_from_allocation_v1(
    row: BalancingPointResistanceAllocationRowV1,
    *,
    dp_tolerance_pa: float,
) -> BalancingPointMethodCandidateV1:
    blockers: list[str] = []
    point_id = str(row.balancing_point_id or "")
    route_ids = tuple(str(value or "") for value in row.downstream_route_ids)
    flow = _float_or_none(row.point_flow_kg_s)
    added_dp = _float_or_none(row.allocated_added_dp_pa)
    resistance = _float_or_none(row.allocated_resistance_pa_per_kg_s2)

    if not row.point_scope:
        blockers.append("Point scope required")
    if not row.point_role:
        blockers.append("Point role required")
    if not route_ids or any(not route_id for route_id in route_ids):
        blockers.append("Governed route ids required")
    if bool(row.is_shared) == bool(row.is_route_exclusive):
        blockers.append("Point must be either shared or route-exclusive")
    if added_dp is None:
        blockers.append("Allocated added Δp required")
    elif added_dp < -dp_tolerance_pa:
        blockers.append("Allocated added Δp cannot be negative")

    if blockers:
        return _candidate(
            row,
            method_id=MANUAL_REVIEW_REQUIRED,
            method_label="Manual review required",
            ready=False,
            flow=flow,
            added_dp=added_dp,
            resistance=resistance,
            status="Blocked — " + "; ".join(blockers),
            blockers=tuple(blockers),
        )

    assert added_dp is not None
    if added_dp <= dp_tolerance_pa:
        if resistance is not None and resistance < -dp_tolerance_pa:
            blockers.append("Allocated resistance cannot be negative")
        return _candidate(
            row,
            method_id=(
                MANUAL_REVIEW_REQUIRED if blockers else NONE_REQUIRED
            ),
            method_label=(
                "Manual review required" if blockers else "None required"
            ),
            ready=not blockers,
            flow=flow,
            added_dp=max(0.0, added_dp),
            resistance=resistance,
            status=(
                "Blocked — " + "; ".join(blockers)
                if blockers
                else "None required — no residual burden at this point"
            ),
            blockers=tuple(blockers),
        )

    if flow is None or flow <= 0.0:
        blockers.append("Positive point flow kg/s required")
    if resistance is None or resistance <= 0.0:
        blockers.append("Positive point resistance Pa/(kg/s)² required")
    if not blockers and flow is not None and resistance is not None:
        expected_resistance = added_dp / (flow ** 2)
        if not math.isclose(
            resistance,
            expected_resistance,
            rel_tol=1e-6,
            abs_tol=0.1,
        ):
            blockers.append("Point resistance differs from allocated Δp / flow²")

    return _candidate(
        row,
        method_id=(
            MANUAL_REVIEW_REQUIRED
            if blockers
            else PROPORTIONAL_ADDED_RESISTANCE
        ),
        method_label=(
            "Manual review required"
            if blockers
            else "Proportional added resistance"
        ),
        ready=not blockers,
        flow=flow,
        added_dp=added_dp,
        resistance=resistance,
        status=(
            "Blocked — " + "; ".join(blockers)
            if blockers
            else "Candidate — shared proportional added resistance"
            if row.is_shared
            else "Candidate — route-exclusive proportional added resistance"
        ),
        blockers=tuple(blockers),
    )


def _candidate(
    row: BalancingPointResistanceAllocationRowV1,
    *,
    method_id: str,
    method_label: str,
    ready: bool,
    flow: float | None,
    added_dp: float | None,
    resistance: float | None,
    status: str,
    blockers: tuple[str, ...],
) -> BalancingPointMethodCandidateV1:
    return BalancingPointMethodCandidateV1(
        balancing_point_id=str(row.balancing_point_id or ""),
        point_scope=str(row.point_scope or ""),
        point_role=str(row.point_role or ""),
        label=str(row.label or ""),
        parent_balancing_point_id=str(row.parent_balancing_point_id or ""),
        anchor_section_id=str(row.anchor_section_id or ""),
        downstream_route_ids=tuple(row.downstream_route_ids or ()),
        is_shared=bool(row.is_shared),
        is_route_exclusive=bool(row.is_route_exclusive),
        method_id=method_id,
        method_label=method_label,
        ready=ready,
        point_flow_kg_s=flow,
        required_added_dp_pa=added_dp,
        resistance_pa_per_kg_s2=resistance,
        status=status,
        blockers=blockers,
        source_allocation_status=str(row.status or ""),
        note=(
            "Shared point governs multiple routes; candidate must remain "
            "group-scoped."
            if row.is_shared
            else "Route-exclusive point candidate."
        ),
    )


def balancing_point_method_candidate_mapping_to_dict_v1(
    mapping: BalancingPointMethodCandidateMappingV1 | None,
) -> dict[str, Any] | None:
    if mapping is None:
        return None
    return {
        "schema": mapping.schema,
        "ready": mapping.ready,
        "status": mapping.status,
        "blockers": tuple(mapping.blockers),
        "candidates": tuple(asdict(candidate) for candidate in mapping.candidates),
        "design_model": mapping.design_model,
        "exclusions": tuple(mapping.exclusions),
        "note": mapping.note,
    }


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _blocked_mapping(
    *blockers: str,
    design_model: dict[str, Any] | None,
) -> BalancingPointMethodCandidateMappingV1:
    clean = tuple(str(blocker) for blocker in blockers if str(blocker))
    return BalancingPointMethodCandidateMappingV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        candidates=(),
        design_model=design_model,
    )
