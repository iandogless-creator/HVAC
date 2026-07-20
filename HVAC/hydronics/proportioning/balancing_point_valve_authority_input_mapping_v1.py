# ======================================================================
# HVAC/hydronics/proportioning/
# balancing_point_valve_authority_input_mapping_v1.py
# H-S44-D — Point-scoped valve-authority inputs
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED as BALANCING_MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.balancing_point_method_candidate_mapping_v1 import (
    BalancingPointMethodCandidateMappingV1,
    BalancingPointMethodCandidateV1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
)


@dataclass(frozen=True, slots=True)
class BalancingPointValveAuthorityInputRowV1:
    """One valve-authority input retaining its H-S44 point identity."""

    balancing_point_id: str
    point_scope: str
    point_role: str
    label: str
    parent_balancing_point_id: str
    anchor_section_id: str
    downstream_route_ids: tuple[str, ...]
    is_shared: bool
    is_route_exclusive: bool

    balancing_method_id: str
    balancing_method_label: str
    authority_band_id: str
    authority_label: str
    ready: bool
    design_valve_dp_pa: float | None
    point_flow_kg_s: float | None
    candidate_resistance_pa_per_kg_s2: float | None
    controlled_circuit_dp_pa: float | None = None
    authority: float | None = None
    status: str = ""
    blockers: tuple[str, ...] = ()
    source_candidate_status: str = ""
    note: str = ""


@dataclass(frozen=True, slots=True)
class BalancingPointValveAuthorityInputMappingV1:
    """
    H-S44-D point-scoped valve-authority input mapping.

    This is a pure evidence mapping. It does not classify final valve
    authority, select a valve product, calculate or select Kv/Kvs, choose
    lockshield turns, select a pump, resize pipe, persist intent, perform
    final balancing, or mutate ProjectState.
    """

    schema: str = "balancing_point_valve_authority_input_mapping_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointValveAuthorityInputRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No controlled-circuit pressure selected",
        "No final valve-authority classification",
        "No valve product selected",
        "No Kv or Kvs calculated or selected",
        "No lockshield turn count",
        "No manufacturer catalogue data",
        "No pump selected",
        "No final balancing",
        "No pipe resizing",
        "No persistence mutation",
        "No ProjectState mutation",
    )
    note: str = (
        "Point-scoped input evidence only; shared and route-exclusive "
        "topology remains explicit."
    )


def build_balancing_point_valve_authority_input_mapping_v1(
    candidate_mapping: BalancingPointMethodCandidateMappingV1 | None,
    *,
    dp_tolerance_pa: float = 0.05,
) -> BalancingPointValveAuthorityInputMappingV1:
    """Consume H-S44-C candidates as point-scoped authority inputs."""

    if candidate_mapping is None:
        return _blocked_mapping("H-S44-C point candidate mapping required")
    if dp_tolerance_pa < 0.0:
        return _blocked_mapping("dp_tolerance_pa must be zero or greater")

    candidates = tuple(candidate_mapping.candidates or ())
    if not candidates:
        return _blocked_mapping(
            "H-S44-C point candidate rows required",
            *tuple(candidate_mapping.blockers or ()),
        )

    point_ids = tuple(
        str(candidate.balancing_point_id or "") for candidate in candidates
    )
    if any(not point_id for point_id in point_ids):
        return _blocked_mapping(
            "Every H-S44-C candidate requires balancing_point_id"
        )
    duplicates = sorted(
        {point_id for point_id in point_ids if point_ids.count(point_id) > 1}
    )
    if duplicates:
        return _blocked_mapping(
            "Duplicate H-S44-C balancing_point_id values: "
            + ", ".join(duplicates)
        )

    rows = tuple(
        _input_row_from_candidate_v1(
            candidate,
            dp_tolerance_pa=dp_tolerance_pa,
        )
        for candidate in candidates
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    upstream_blockers = tuple(
        f"H-S44-C: {blocker}"
        for blocker in tuple(candidate_mapping.blockers or ())
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = bool(candidate_mapping.ready) and not blockers and all(
        row.ready for row in rows
    )
    if not candidate_mapping.ready and not blockers:
        blockers = ("H-S44-C point candidate mapping is not ready",)
        ready = False

    return BalancingPointValveAuthorityInputMappingV1(
        ready=ready,
        status=(
            "Ready — point-scoped valve-authority inputs available"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _input_row_from_candidate_v1(
    candidate: BalancingPointMethodCandidateV1,
    *,
    dp_tolerance_pa: float,
) -> BalancingPointValveAuthorityInputRowV1:
    blockers: list[str] = list(candidate.blockers or ())
    route_ids = tuple(str(value or "") for value in candidate.downstream_route_ids)
    flow = _float_or_none(candidate.point_flow_kg_s)
    added_dp = _float_or_none(candidate.required_added_dp_pa)
    resistance = _float_or_none(candidate.resistance_pa_per_kg_s2)

    if not candidate.point_scope:
        blockers.append("Point scope required")
    if not candidate.point_role:
        blockers.append("Point role required")
    if not route_ids or any(not route_id for route_id in route_ids):
        blockers.append("Governed route ids required")
    if bool(candidate.is_shared) == bool(candidate.is_route_exclusive):
        blockers.append("Point must be either shared or route-exclusive")

    common = dict(
        balancing_point_id=str(candidate.balancing_point_id or ""),
        point_scope=str(candidate.point_scope or ""),
        point_role=str(candidate.point_role or ""),
        label=str(candidate.label or ""),
        parent_balancing_point_id=str(
            candidate.parent_balancing_point_id or ""
        ),
        anchor_section_id=str(candidate.anchor_section_id or ""),
        downstream_route_ids=route_ids,
        is_shared=bool(candidate.is_shared),
        is_route_exclusive=bool(candidate.is_route_exclusive),
        balancing_method_id=str(candidate.method_id or ""),
        balancing_method_label=str(candidate.method_label or ""),
        design_valve_dp_pa=added_dp,
        point_flow_kg_s=flow,
        candidate_resistance_pa_per_kg_s2=resistance,
        source_candidate_status=str(candidate.status or ""),
    )

    if not candidate.ready and not blockers:
        blockers.append("H-S44-C point candidate is not ready")

    if candidate.method_id == NONE_REQUIRED:
        if added_dp is None:
            blockers.append("Allocated added Δp required")
        elif added_dp > dp_tolerance_pa:
            blockers.append("None-required point has positive added Δp")
        if blockers:
            return _manual_row(common, blockers)
        return BalancingPointValveAuthorityInputRowV1(
            **common,
            authority_band_id=VALVE_AUTHORITY_NONE_REQUIRED,
            authority_label="No valve authority required",
            ready=True,
            status="No valve authority required — no point burden",
            blockers=(),
            note=_scope_note_v1(candidate),
        )

    if candidate.method_id == PROPORTIONAL_ADDED_RESISTANCE:
        if added_dp is None or added_dp <= dp_tolerance_pa:
            blockers.append("Positive design valve/throttling Δp required")
        if flow is None or flow <= 0.0:
            blockers.append("Positive point flow kg/s required")
        if resistance is None or resistance <= 0.0:
            blockers.append("Positive candidate resistance required")
        if not blockers and added_dp is not None and flow is not None:
            expected = added_dp / (flow ** 2)
            if not math.isclose(
                resistance,
                expected,
                rel_tol=1e-6,
                abs_tol=0.1,
            ):
                blockers.append(
                    "Candidate resistance differs from design Δp / point flow²"
                )
        if blockers:
            return _manual_row(common, blockers)
        return BalancingPointValveAuthorityInputRowV1(
            **common,
            authority_band_id=VALVE_AUTHORITY_INPUT_AVAILABLE,
            authority_label="Valve authority input available",
            ready=True,
            controlled_circuit_dp_pa=None,
            authority=None,
            status=(
                "Input available — shared point duty"
                if candidate.is_shared
                else "Input available — route-exclusive point duty"
            ),
            blockers=(),
            note=(
                _scope_note_v1(candidate)
                + " Required added Δp is theoretical valve/throttling Δp; "
                "controlled-circuit Δp is not yet mapped."
            ),
        )

    if candidate.method_id != BALANCING_MANUAL_REVIEW_REQUIRED:
        blockers.append(
            "Unsupported balancing method: " + str(candidate.method_id or "—")
        )
    if not blockers:
        blockers.append("Balancing method requires manual review")
    return _manual_row(common, blockers)


def _manual_row(
    common: dict[str, Any],
    blockers: list[str],
) -> BalancingPointValveAuthorityInputRowV1:
    clean = _unique_v1(tuple(str(value) for value in blockers if str(value)))
    return BalancingPointValveAuthorityInputRowV1(
        **common,
        authority_band_id=MANUAL_REVIEW_REQUIRED,
        authority_label="Manual review required",
        ready=False,
        controlled_circuit_dp_pa=None,
        authority=None,
        status="Manual review required — " + "; ".join(clean),
        blockers=clean,
        note="No valve-authority input is released for this point.",
    )


def _scope_note_v1(candidate: BalancingPointMethodCandidateV1) -> str:
    if candidate.is_shared:
        return (
            "Shared point governs multiple downstream routes; any future "
            "selection must remain group-scoped."
        )
    return "Route-exclusive point duty."


def balancing_point_valve_authority_input_mapping_to_dict_v1(
    mapping: BalancingPointValveAuthorityInputMappingV1 | None,
) -> dict[str, Any] | None:
    if mapping is None:
        return None
    return {
        "schema": mapping.schema,
        "ready": mapping.ready,
        "status": mapping.status,
        "blockers": tuple(mapping.blockers),
        "rows": tuple(asdict(row) for row in mapping.rows),
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


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _blocked_mapping(
    *blockers: str,
) -> BalancingPointValveAuthorityInputMappingV1:
    clean = _unique_v1(tuple(str(value) for value in blockers if str(value)))
    return BalancingPointValveAuthorityInputMappingV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
