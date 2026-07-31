# ======================================================================
# H-S61-F — Manual acceptance authority for the proposed DN schedule
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from math import isfinite
from typing import Any

from HVAC.hydronics.proportioning.proportioned_pipe_resizing_hydraulic_projection_v1 import (
    ProportionedPipeResizingHydraulicProjectionV1,
)
from HVAC.hydronics.proportioning.resized_balancing_point_reconciliation_v1 import (
    ResizedBalancingPointReconciliationV1,
)


@dataclass(frozen=True, slots=True)
class AcceptedProportionedPipeSectionDNV1:
    """One manually accepted section DN, keyed by stable section identity."""

    section_id: str
    current_dn: int
    accepted_dn: int


@dataclass(frozen=True, slots=True)
class AcceptedProportionedPipeResizingScheduleV1:
    """Frozen user acceptance of one exact H-S61-C/D evidence package."""

    schedule_fingerprint: str
    sections: tuple[AcceptedProportionedPipeSectionDNV1, ...]


@dataclass(slots=True)
class ProportionedPipeResizingScheduleAcceptanceIntentV1:
    """
    Persisted manual intent for the complete proposed DN schedule.

    Acceptance is atomic because changing one physical section can change
    route pressure totals and downstream balancing-point duties.  This intent
    does not replace any committed DN or hydraulic result.
    """

    schema: str = (
        "proportioned_pipe_resizing_schedule_acceptance_intent_v1"
    )
    accepted_schedule: (
        AcceptedProportionedPipeResizingScheduleV1 | None
    ) = None

    def accept_current_schedule(
            self,
            *,
            resized_hydraulics: (
                ProportionedPipeResizingHydraulicProjectionV1 | None
            ),
            resized_point_reconciliation: (
                ResizedBalancingPointReconciliationV1 | None
            ),
    ) -> AcceptedProportionedPipeResizingScheduleV1:
        sections = _validated_current_evidence_v1(
            resized_hydraulics=resized_hydraulics,
            resized_point_reconciliation=resized_point_reconciliation,
        )
        accepted = AcceptedProportionedPipeResizingScheduleV1(
            schedule_fingerprint=(
                build_proportioned_pipe_resizing_schedule_fingerprint_v1(
                    resized_hydraulics=resized_hydraulics,
                    resized_point_reconciliation=(
                        resized_point_reconciliation
                    ),
                )
            ),
            sections=tuple(
                AcceptedProportionedPipeSectionDNV1(
                    section_id=str(row.section_id),
                    current_dn=int(row.current_dn),
                    accepted_dn=int(row.projected_dn),
                )
                for row in sections
            ),
        )
        self.accepted_schedule = accepted
        return accepted

    def clear_acceptance(self) -> bool:
        existed = self.accepted_schedule is not None
        self.accepted_schedule = None
        return existed

    def to_dict(self) -> dict:
        return (
            proportioned_pipe_resizing_schedule_acceptance_intent_to_dict_v1(
                self
            )
        )

    @classmethod
    def from_dict(
            cls,
            data: dict | None,
    ) -> "ProportionedPipeResizingScheduleAcceptanceIntentV1":
        return (
            proportioned_pipe_resizing_schedule_acceptance_intent_from_dict_v1(
                data
            )
        )


@dataclass(frozen=True, slots=True)
class ResolvedProportionedPipeSectionDNAcceptanceV1:
    section_id: str
    current_dn: int
    proposed_dn: int
    accepted_dn: int | None = None
    matches_current_schedule: bool = False
    status: str = ""


@dataclass(frozen=True, slots=True)
class ResolvedProportionedPipeResizingScheduleAcceptanceV1:
    """
    Current authority resolved from persisted intent and H-S61-C/D evidence.
    """

    schema: str = (
        "resolved_proportioned_pipe_resizing_schedule_acceptance_v1"
    )
    ready: bool = False
    accepted: bool = False
    schedule_fingerprint: str = ""
    accepted_schedule_fingerprint: str = ""
    rows: tuple[ResolvedProportionedPipeSectionDNAcceptanceV1, ...] = ()
    status: str = ""
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic DN acceptance",
        "No ProjectState pipe-size mutation",
        "No committed DN replacement",
        "No hydraulic result replacement",
        "No balancing-point allocation replacement",
        "No pump selection",
        "No valve product or setting selection",
        "No final balancing",
    )
    note: str = (
        "Manual acceptance authority only — a later explicit commit stage "
        "must apply an accepted DN schedule."
    )


def build_proportioned_pipe_resizing_schedule_fingerprint_v1(
        *,
        resized_hydraulics: (
            ProportionedPipeResizingHydraulicProjectionV1 | None
        ),
        resized_point_reconciliation: (
            ResizedBalancingPointReconciliationV1 | None
        ),
) -> str:
    """
    Build a deterministic SHA-256 identity for the reviewed engineering result.

    Wording/status fields are excluded.  Stable identities, hydraulic inputs,
    proposed DNs, recalculated losses, route shortfalls and reconciled point
    duties are included.
    """
    _validated_current_evidence_v1(
        resized_hydraulics=resized_hydraulics,
        resized_point_reconciliation=resized_point_reconciliation,
    )
    assert resized_hydraulics is not None
    assert resized_point_reconciliation is not None

    payload = {
        "projection_schema": str(resized_hydraulics.schema),
        "sections": [
            {
                "section_id": _text_v1(row.section_id),
                "section_scope": _text_v1(row.section_scope),
                "route_ids": sorted(
                    _text_v1(value) for value in tuple(row.route_ids)
                ),
                "order": int(row.order),
                "carried_flow_kg_s": _number_v1(row.carried_flow_kg_s),
                "length_m": _number_v1(row.length_m),
                "k_total": _number_v1(row.k_total),
                "current_dn": int(row.current_dn),
                "projected_dn": int(row.projected_dn),
                "internal_diameter_m": _number_v1(
                    row.internal_diameter_m
                ),
                "velocity_m_s": _number_v1(row.velocity_m_s),
                "maximum_velocity_m_s": _number_v1(
                    row.maximum_velocity_m_s
                ),
                "pressure_gradient_Pa_per_m": _number_v1(
                    row.pressure_gradient_Pa_per_m
                ),
                "maximum_pressure_gradient_Pa_per_m": _number_v1(
                    row.maximum_pressure_gradient_Pa_per_m
                ),
                "straight_pressure_drop_Pa": _number_v1(
                    row.straight_pressure_drop_Pa
                ),
                "local_pressure_drop_Pa": _number_v1(
                    row.local_pressure_drop_Pa
                ),
                "section_total_pressure_drop_Pa": _number_v1(
                    row.section_total_pressure_drop_Pa
                ),
                "reynolds_number": _number_v1(row.reynolds_number),
                "friction_factor": _number_v1(row.friction_factor),
                "friction_method": _text_v1(row.friction_method),
                "colebrook_iteration_count": int(
                    row.colebrook_iteration_count
                ),
                "colebrook_converged": bool(row.colebrook_converged),
            }
            for row in sorted(
                tuple(resized_hydraulics.sections),
                key=lambda value: _text_v1(value.section_id),
            )
        ],
        "routes": [
            {
                "route_id": _text_v1(row.route_id),
                "section_ids": sorted(
                    _text_v1(value) for value in tuple(row.section_ids)
                ),
                "straight_pressure_drop_total_Pa": _number_v1(
                    row.straight_pressure_drop_total_Pa
                ),
                "local_pressure_drop_total_Pa": _number_v1(
                    row.local_pressure_drop_total_Pa
                ),
                "route_pressure_drop_total_Pa": _number_v1(
                    row.route_pressure_drop_total_Pa
                ),
                "controlling_target_Pa": _number_v1(
                    row.controlling_target_Pa
                ),
                "required_added_dp_Pa": _number_v1(
                    row.required_added_dp_Pa
                ),
                "rank": int(row.rank),
                "is_controlling": bool(row.is_controlling),
            }
            for row in sorted(
                tuple(resized_hydraulics.routes),
                key=lambda value: _text_v1(value.route_id),
            )
        ],
        "reconciliation_schema": str(
            resized_point_reconciliation.schema
        ),
        "point_rows": [
            {
                "balancing_point_id": _text_v1(
                    row.balancing_point_id
                ),
                "point_scope": _text_v1(row.point_scope),
                "parent_balancing_point_id": _text_v1(
                    row.parent_balancing_point_id
                ),
                "anchor_section_id": _text_v1(row.anchor_section_id),
                "projected_route_ids": sorted(
                    _text_v1(value)
                    for value in tuple(row.projected_route_ids)
                ),
                "point_flow_kg_s": _number_v1(row.point_flow_kg_s),
                "reconciled_allocated_dp_Pa": _number_v1(
                    row.reconciled_allocated_dp_Pa
                ),
                "reconciled_resistance_Pa_per_kg_s2": _number_v1(
                    row.reconciled_resistance_Pa_per_kg_s2
                ),
                "valve_duty_required": bool(row.valve_duty_required),
            }
            for row in sorted(
                tuple(resized_point_reconciliation.point_rows),
                key=lambda value: _text_v1(value.balancing_point_id),
            )
        ],
        "route_rows": [
            {
                "projected_route_id": _text_v1(
                    row.projected_route_id
                ),
                "resized_hydraulic_dp_Pa": _number_v1(
                    row.resized_hydraulic_dp_Pa
                ),
                "controlling_target_Pa": _number_v1(
                    row.controlling_target_Pa
                ),
                "required_added_dp_Pa": _number_v1(
                    row.required_added_dp_Pa
                ),
                "allocated_path_dp_Pa": _number_v1(
                    row.allocated_path_dp_Pa
                ),
                "residual_Pa": _number_v1(row.residual_Pa),
                "contributing_balancing_point_ids": sorted(
                    _text_v1(value)
                    for value in tuple(
                        row.contributing_balancing_point_ids
                    )
                ),
                "conserved": bool(row.conserved),
            }
            for row in sorted(
                tuple(resized_point_reconciliation.route_rows),
                key=lambda value: _text_v1(value.projected_route_id),
            )
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resolve_proportioned_pipe_resizing_schedule_acceptance_v1(
        intent: ProportionedPipeResizingScheduleAcceptanceIntentV1 | None,
        *,
        resized_hydraulics: (
            ProportionedPipeResizingHydraulicProjectionV1 | None
        ),
        resized_point_reconciliation: (
            ResizedBalancingPointReconciliationV1 | None
        ),
) -> ResolvedProportionedPipeResizingScheduleAcceptanceV1:
    """Resolve stored manual intent against the current H-S61-C/D result."""
    try:
        sections = _validated_current_evidence_v1(
            resized_hydraulics=resized_hydraulics,
            resized_point_reconciliation=resized_point_reconciliation,
        )
        current_fingerprint = (
            build_proportioned_pipe_resizing_schedule_fingerprint_v1(
                resized_hydraulics=resized_hydraulics,
                resized_point_reconciliation=(
                    resized_point_reconciliation
                ),
            )
        )
    except (TypeError, ValueError) as exc:
        return _blocked_resolution_v1(str(exc))

    accepted = (
        intent.accepted_schedule
        if isinstance(
            intent,
            ProportionedPipeResizingScheduleAcceptanceIntentV1,
        )
        else None
    )
    if accepted is None:
        return ResolvedProportionedPipeResizingScheduleAcceptanceV1(
            schedule_fingerprint=current_fingerprint,
            rows=tuple(
                ResolvedProportionedPipeSectionDNAcceptanceV1(
                    section_id=str(row.section_id),
                    current_dn=int(row.current_dn),
                    proposed_dn=int(row.projected_dn),
                    status="Manual DN schedule acceptance pending",
                )
                for row in sections
            ),
            status="Pending — manual proposed DN schedule acceptance required",
            blockers=("Manual proposed DN schedule acceptance required",),
        )

    accepted_by_id = {
        row.section_id: row for row in tuple(accepted.sections)
    }
    current_ids = {str(row.section_id) for row in sections}
    stored_ids = set(accepted_by_id)
    blockers: list[str] = []
    if stored_ids != current_ids:
        blockers.append(
            "Accepted section identities do not match the current schedule"
        )
    if accepted.schedule_fingerprint != current_fingerprint:
        blockers.append(
            "Accepted DN schedule fingerprint does not match current "
            "H-S61-C/D evidence"
        )

    rows: list[ResolvedProportionedPipeSectionDNAcceptanceV1] = []
    for current in sections:
        section_id = str(current.section_id)
        stored = accepted_by_id.get(section_id)
        matches = bool(
            stored is not None
            and int(stored.current_dn) == int(current.current_dn)
            and int(stored.accepted_dn) == int(current.projected_dn)
        )
        if stored is not None and not matches:
            blockers.append(
                f"{section_id}: accepted current/proposed DN no longer "
                "matches"
            )
        rows.append(
            ResolvedProportionedPipeSectionDNAcceptanceV1(
                section_id=section_id,
                current_dn=int(current.current_dn),
                proposed_dn=int(current.projected_dn),
                accepted_dn=(
                    int(stored.accepted_dn)
                    if stored is not None
                    else None
                ),
                matches_current_schedule=matches,
                status=(
                    "Accepted — current proposed DN matches"
                    if matches
                    else "Blocked — stale or missing DN acceptance"
                ),
            )
        )

    clean_blockers = _unique_v1(tuple(blockers))
    ready = not clean_blockers and all(
        row.matches_current_schedule for row in rows
    )
    return ResolvedProportionedPipeResizingScheduleAcceptanceV1(
        ready=ready,
        accepted=ready,
        schedule_fingerprint=current_fingerprint,
        accepted_schedule_fingerprint=accepted.schedule_fingerprint,
        rows=tuple(rows),
        status=(
            f"Ready — manually accepted proposed DN schedule for "
            f"{len(rows)} sections"
            if ready
            else "Blocked — stale manual DN schedule acceptance: "
            + "; ".join(clean_blockers)
        ),
        blockers=clean_blockers,
    )


def proportioned_pipe_resizing_schedule_acceptance_intent_to_dict_v1(
        intent: (
            ProportionedPipeResizingScheduleAcceptanceIntentV1 | None
        ),
) -> dict:
    source = (
        intent
        if isinstance(
            intent,
            ProportionedPipeResizingScheduleAcceptanceIntentV1,
        )
        else ProportionedPipeResizingScheduleAcceptanceIntentV1()
    )
    accepted = source.accepted_schedule
    return {
        "schema": source.schema,
        "accepted_schedule": (
            {
                "schedule_fingerprint": accepted.schedule_fingerprint,
                "sections": [
                    {
                        "section_id": row.section_id,
                        "current_dn": int(row.current_dn),
                        "accepted_dn": int(row.accepted_dn),
                    }
                    for row in sorted(
                        tuple(accepted.sections),
                        key=lambda value: value.section_id,
                    )
                ],
            }
            if accepted is not None
            else None
        ),
    }


def proportioned_pipe_resizing_schedule_acceptance_intent_from_dict_v1(
        data: dict | None,
) -> ProportionedPipeResizingScheduleAcceptanceIntentV1:
    intent = ProportionedPipeResizingScheduleAcceptanceIntentV1()
    if not isinstance(data, dict):
        return intent
    raw_schedule = data.get("accepted_schedule")
    if not isinstance(raw_schedule, dict):
        return intent
    fingerprint = _fingerprint_v1(
        raw_schedule.get("schedule_fingerprint")
    )
    raw_sections = raw_schedule.get("sections")
    if not fingerprint or not isinstance(raw_sections, list):
        return intent

    rows: list[AcceptedProportionedPipeSectionDNV1] = []
    seen: set[str] = set()
    for raw in raw_sections:
        if not isinstance(raw, dict):
            return intent
        section_id = _text_v1(raw.get("section_id"))
        current_dn = _positive_int_v1(raw.get("current_dn"))
        accepted_dn = _positive_int_v1(raw.get("accepted_dn"))
        if (
                not section_id
                or section_id in seen
                or current_dn is None
                or accepted_dn is None
        ):
            return intent
        seen.add(section_id)
        rows.append(
            AcceptedProportionedPipeSectionDNV1(
                section_id=section_id,
                current_dn=current_dn,
                accepted_dn=accepted_dn,
            )
        )
    if not rows:
        return intent
    intent.accepted_schedule = AcceptedProportionedPipeResizingScheduleV1(
        schedule_fingerprint=fingerprint,
        sections=tuple(sorted(rows, key=lambda value: value.section_id)),
    )
    return intent


def _validated_current_evidence_v1(
        *,
        resized_hydraulics: (
            ProportionedPipeResizingHydraulicProjectionV1 | None
        ),
        resized_point_reconciliation: (
            ResizedBalancingPointReconciliationV1 | None
        ),
) -> tuple[Any, ...]:
    if not isinstance(
            resized_hydraulics,
            ProportionedPipeResizingHydraulicProjectionV1,
    ):
        raise ValueError("H-S61-C resized hydraulic projection required")
    if not resized_hydraulics.ready:
        raise ValueError(
            "H-S61-C resized hydraulic projection is not ready"
        )
    if not isinstance(
            resized_point_reconciliation,
            ResizedBalancingPointReconciliationV1,
    ):
        raise ValueError("H-S61-D resized point reconciliation required")
    if not resized_point_reconciliation.ready:
        raise ValueError(
            "H-S61-D resized point reconciliation is not ready"
        )

    sections = tuple(resized_hydraulics.sections or ())
    routes = tuple(resized_hydraulics.routes or ())
    if not sections:
        raise ValueError("At least one proposed DN section required")
    if not routes:
        raise ValueError("At least one resized route required")
    ids = [_text_v1(row.section_id) for row in sections]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Unique stable section identities required")
    for row in sections:
        if int(row.current_dn) <= 0 or int(row.projected_dn) <= 0:
            raise ValueError(
                f"{row.section_id}: positive current and proposed DN required"
            )

    projected_route_ids = {
        _text_v1(row.route_id) for row in routes
    }
    reconciliation_rows = tuple(
        resized_point_reconciliation.route_rows or ()
    )
    reconciled_route_ids = {
        _text_v1(row.projected_route_id)
        for row in reconciliation_rows
    }
    if projected_route_ids != reconciled_route_ids:
        raise ValueError(
            "H-S61-C route identities must match H-S61-D reconciliation"
        )
    if not all(bool(row.conserved) for row in reconciliation_rows):
        raise ValueError(
            "Every resized route must conserve before manual acceptance"
        )
    return tuple(
        sorted(sections, key=lambda value: _text_v1(value.section_id))
    )


def _number_v1(value: object) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError("Finite numeric schedule evidence required")
    number = float(value)
    if not isfinite(number):
        raise ValueError("Finite numeric schedule evidence required")
    return 0.0 if abs(number) < 1.0e-12 else number


def _positive_int_v1(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _fingerprint_v1(value: object) -> str:
    text = _text_v1(value).lower()
    if len(text) != 64:
        return ""
    return text if all(char in "0123456789abcdef" for char in text) else ""


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in output:
            output.append(text)
    return tuple(output)


def _blocked_resolution_v1(
        *blockers: str,
) -> ResolvedProportionedPipeResizingScheduleAcceptanceV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedProportionedPipeResizingScheduleAcceptanceV1(
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
