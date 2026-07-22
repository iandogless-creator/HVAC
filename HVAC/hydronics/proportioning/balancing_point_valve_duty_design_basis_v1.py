# ======================================================================
# H-S46-A — Point-scoped valve-duty design basis
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_low_authority_design_disposition_v1 import (
    AUTHORITY_ACCEPTABLE_FOR_REVIEW,
    EVIDENCE_UNAVAILABLE,
    HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED,
    LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED,
    NO_VALVE_REQUIRED,
    BalancingPointLowAuthorityDesignDispositionRowV1,
    BalancingPointLowAuthorityDesignDispositionV1,
)


NO_VALVE_DUTY_REQUIRED = "no_valve_duty_required"
POINT_VALVE_DUTY_BASIS_AVAILABLE = "point_valve_duty_basis_available"
POINT_VALVE_DUTY_EVIDENCE_UNAVAILABLE = (
    "point_valve_duty_evidence_unavailable"
)
MANUAL_ENGINEERING_APPROVAL_PENDING = "manual_engineering_approval_pending"
ENGINEERING_APPROVAL_NOT_APPLICABLE = "not_applicable"
POINT_VALVE_DUTY_BASIS_V1 = (
    "hs44d_point_flow_design_dp_candidate_resistance"
)

_VALVE_REQUIRED_DISPOSITIONS = {
    AUTHORITY_ACCEPTABLE_FOR_REVIEW,
    LOW_AUTHORITY_MANUAL_REVIEW_REQUIRED,
    HIGH_THROTTLING_MANUAL_REVIEW_REQUIRED,
}


@dataclass(frozen=True, slots=True)
class BalancingPointValveDutyDesignBasisRowV1(
    BalancingPointLowAuthorityDesignDispositionRowV1
):
    """H-S45-C point evidence plus a candidate valve-duty design basis."""

    valve_duty_state_id: str = ""
    valve_duty_required: bool = False
    valve_duty_basis_available: bool = False
    valve_duty_basis_id: str = ""
    manual_engineering_approval_required: bool = False
    engineering_approval_state: str = ""


@dataclass(frozen=True, slots=True)
class BalancingPointValveDutyDesignBasisV1:
    """
    H-S46-A point-scoped valve-duty design-basis evidence.

    Existing H-S44-D point flow, design valve pressure drop and candidate
    resistance are retained for points that require valve duty. Nothing is
    approved, selected, recalculated, persisted or applied automatically.
    """

    schema: str = "balancing_point_valve_duty_design_basis_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointValveDutyDesignBasisRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No engineering approval granted",
        "No valve selected",
        "No Kv or Kvs calculated or selected",
        "No valve product selected",
        "No design valve pressure changed",
        "No pipe restriction added",
        "No pipe resizing",
        "No pump selected",
        "No hydraulic recalculation",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Valve-duty basis is preview evidence only; manual engineering "
        "approval remains pending."
    )


def build_balancing_point_valve_duty_design_basis_v1(
    disposition: BalancingPointLowAuthorityDesignDispositionV1 | None,
) -> BalancingPointValveDutyDesignBasisV1:
    """Release existing point duty values only where H-S45-C requires a valve."""

    if disposition is None:
        return _blocked_projection("H-S45-C point disposition evidence required")
    if not isinstance(
        disposition,
        BalancingPointLowAuthorityDesignDispositionV1,
    ):
        return _blocked_projection(
            "disposition is not BalancingPointLowAuthorityDesignDispositionV1"
        )

    input_rows = tuple(disposition.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S45-C point disposition rows required",
            *tuple(disposition.blockers or ()),
        )

    point_ids = tuple(str(row.balancing_point_id or "") for row in input_rows)
    if any(not point_id for point_id in point_ids):
        return _blocked_projection("Every H-S45-C row requires balancing_point_id")
    duplicates = sorted(
        {point_id for point_id in point_ids if point_ids.count(point_id) > 1}
    )
    if duplicates:
        return _blocked_projection(
            "Duplicate H-S45-C balancing_point_id values: "
            + ", ".join(duplicates)
        )

    rows = tuple(_resolve_row_v1(row) for row in input_rows)
    upstream_blockers = tuple(
        f"H-S45-C: {value}" for value in tuple(disposition.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(disposition.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not disposition.ready and not blockers:
        blockers = ("H-S45-C point disposition evidence is not ready",)
        ready = False

    required_count = sum(1 for row in rows if row.valve_duty_required)
    return BalancingPointValveDutyDesignBasisV1(
        ready=ready,
        status=(
            f"Ready — {required_count} point valve-duty basis row(s) available; "
            "manual engineering approval pending"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(
    input_row: BalancingPointLowAuthorityDesignDispositionRowV1,
) -> BalancingPointValveDutyDesignBasisRowV1:
    common = asdict(input_row)
    disposition_id = str(input_row.design_disposition_id or "")
    existing_blockers = _unique_v1(tuple(input_row.blockers or ()))

    if (
        not input_row.ready
        or existing_blockers
        or not input_row.evidence_available
        or disposition_id == EVIDENCE_UNAVAILABLE
    ):
        blockers = existing_blockers or (
            "Required H-S45-C point evidence is unavailable",
        )
        common.update(
            ready=False,
            status="Blocked — point valve-duty evidence unavailable",
            blockers=blockers,
            note="No point valve-duty design basis released.",
        )
        return BalancingPointValveDutyDesignBasisRowV1(
            **common,
            valve_duty_state_id=POINT_VALVE_DUTY_EVIDENCE_UNAVAILABLE,
            valve_duty_required=False,
            valve_duty_basis_available=False,
            valve_duty_basis_id="",
            manual_engineering_approval_required=False,
            engineering_approval_state="",
        )

    if disposition_id == NO_VALVE_REQUIRED:
        common.update(
            ready=True,
            status="No valve duty required",
            blockers=(),
            note=(
                str(input_row.note or "")
                + " H-S46-A releases no valve-duty basis for this point."
            ).strip(),
        )
        return BalancingPointValveDutyDesignBasisRowV1(
            **common,
            valve_duty_state_id=NO_VALVE_DUTY_REQUIRED,
            valve_duty_required=False,
            valve_duty_basis_available=False,
            valve_duty_basis_id="",
            manual_engineering_approval_required=False,
            engineering_approval_state=ENGINEERING_APPROVAL_NOT_APPLICABLE,
        )

    if disposition_id not in _VALVE_REQUIRED_DISPOSITIONS:
        blocker = f"Unsupported H-S45-C disposition: {disposition_id or 'missing'}"
        common.update(
            ready=False,
            status="Blocked — point valve-duty evidence unavailable",
            blockers=(blocker,),
            note="No point valve-duty design basis released.",
        )
        return BalancingPointValveDutyDesignBasisRowV1(
            **common,
            valve_duty_state_id=POINT_VALVE_DUTY_EVIDENCE_UNAVAILABLE,
            valve_duty_required=False,
            valve_duty_basis_available=False,
            valve_duty_basis_id="",
            manual_engineering_approval_required=False,
            engineering_approval_state="",
        )

    blockers: list[str] = []
    if _positive_finite_v1(input_row.point_flow_kg_s) is None:
        blockers.append("Positive finite point flow required")
    if _positive_finite_v1(input_row.design_valve_dp_pa) is None:
        blockers.append("Positive finite design valve Δp required")
    if _positive_finite_v1(
        input_row.candidate_resistance_pa_per_kg_s2
    ) is None:
        blockers.append("Positive finite candidate resistance required")

    if blockers:
        clean = _unique_v1(tuple(blockers))
        common.update(
            ready=False,
            status="Blocked — " + "; ".join(clean),
            blockers=clean,
            note="No point valve-duty design basis released.",
        )
        return BalancingPointValveDutyDesignBasisRowV1(
            **common,
            valve_duty_state_id=POINT_VALVE_DUTY_EVIDENCE_UNAVAILABLE,
            valve_duty_required=True,
            valve_duty_basis_available=False,
            valve_duty_basis_id="",
            manual_engineering_approval_required=True,
            engineering_approval_state=MANUAL_ENGINEERING_APPROVAL_PENDING,
        )

    common.update(
        ready=True,
        status="Valve-duty design basis available — manual approval pending",
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S46-A retains existing point flow, design valve Δp and "
            "candidate resistance without recalculation or approval."
        ).strip(),
    )
    return BalancingPointValveDutyDesignBasisRowV1(
        **common,
        valve_duty_state_id=POINT_VALVE_DUTY_BASIS_AVAILABLE,
        valve_duty_required=True,
        valve_duty_basis_available=True,
        valve_duty_basis_id=POINT_VALVE_DUTY_BASIS_V1,
        manual_engineering_approval_required=True,
        engineering_approval_state=MANUAL_ENGINEERING_APPROVAL_PENDING,
    )


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0.0:
        return None
    return number


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(*blockers: str) -> BalancingPointValveDutyDesignBasisV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointValveDutyDesignBasisV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
