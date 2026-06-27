# HVAC/hydronics/proportioning/return_arrangement_basis_acceptance_summary_v1.py

"""
H-S26-B — Proportioning readiness / accepted return arrangement basis.

Read-only summary only:
- no ProjectState persistence
- no valve selection
- no pump sizing
- no pipe resizing
- no final Proportioned commit

The F+R / F+RR comparison table is evidence only.
It must not silently choose the accepted return arrangement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    DIRECT_RETURN,
    REVERSE_RETURN,
    UNDECIDED,
    ReturnArrangementIntentV1,
    resolve_system_return_arrangement_v1,
    resolve_leg_return_arrangement_v1,
    resolve_subleg_return_arrangement_v1,
)


@dataclass(slots=True, frozen=True)
class ReturnArrangementBasisAcceptanceSummaryRowV1:
    scope: str = ""
    target: str = ""

    leg_id: str = ""
    subleg_id: str = ""
    parent_subleg_id: str = ""

    effective_return_basis: str = UNDECIDED
    acceptance_source: str = ""
    inherited_from: str = ""

    ready: bool = False
    status: str = ""


def _route_value(route: Any, name: str, default: str = "") -> str:
    if isinstance(route, dict):
        return str(route.get(name, default) or default)

    if isinstance(route, tuple):
        # Existing simple route_specs style: (leg_id, subleg_id)
        if name == "leg_id" and len(route) >= 1:
            return str(route[0] or default)
        if name == "subleg_id" and len(route) >= 2:
            return str(route[1] or default)
        return default

    return str(getattr(route, name, default) or default)


def _ready_from_basis(value: str) -> bool:
    return value in {DIRECT_RETURN, REVERSE_RETURN}


def build_return_arrangement_basis_acceptance_summary_v1(
    *,
    intent: ReturnArrangementIntentV1 | None,
    route_specs: Iterable[Any],
) -> list[ReturnArrangementBasisAcceptanceSummaryRowV1]:
    """
    Build read-only Proportioning readiness rows from the accepted
    return-arrangement intent.

    This does not mutate ProjectState.
    This does not use the F+R / F+RR comparison to auto-select a basis.
    """

    if intent is None:
        intent = ReturnArrangementIntentV1()

    rows: list[ReturnArrangementBasisAcceptanceSummaryRowV1] = []

    system_resolved = resolve_system_return_arrangement_v1(intent)

    rows.append(
        ReturnArrangementBasisAcceptanceSummaryRowV1(
            scope="System",
            target="Whole system",
            effective_return_basis=system_resolved.resolved_arrangement,
            acceptance_source=system_resolved.source,
            inherited_from=system_resolved.inherited_from,
            ready=bool(system_resolved.accepted),
            status=system_resolved.status,
        )
    )

    seen_legs: set[str] = set()

    for route in route_specs:
        leg_id = _route_value(route, "leg_id")
        subleg_id = _route_value(route, "subleg_id")
        parent_subleg_id = _route_value(route, "parent_subleg_id")

        if leg_id and leg_id not in seen_legs:
            leg_resolved = resolve_leg_return_arrangement_v1(
                intent,
                leg_id=leg_id,
            )

            rows.append(
                ReturnArrangementBasisAcceptanceSummaryRowV1(
                    scope="Leg",
                    target=leg_id,
                    leg_id=leg_id,
                    effective_return_basis=leg_resolved.resolved_arrangement,
                    acceptance_source=leg_resolved.source,
                    inherited_from=leg_resolved.inherited_from,
                    ready=bool(leg_resolved.accepted),
                    status=leg_resolved.status,
                )
            )

            seen_legs.add(leg_id)

        if subleg_id:
            subleg_resolved = resolve_subleg_return_arrangement_v1(
                intent,
                leg_id=leg_id,
                subleg_id=subleg_id,
                parent_subleg_id=parent_subleg_id,
            )

            rows.append(
                ReturnArrangementBasisAcceptanceSummaryRowV1(
                    scope="Subleg",
                    target=subleg_id,
                    leg_id=leg_id,
                    subleg_id=subleg_id,
                    parent_subleg_id=parent_subleg_id,
                    effective_return_basis=subleg_resolved.resolved_arrangement,
                    acceptance_source=subleg_resolved.source,
                    inherited_from=subleg_resolved.inherited_from,
                    ready=bool(subleg_resolved.accepted),
                    status=subleg_resolved.status,
                )
            )

    return rows