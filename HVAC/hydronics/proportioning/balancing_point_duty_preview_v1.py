# ======================================================================
# HVAC/hydronics/proportioning/balancing_point_duty_preview_v1.py
# H-S24-A — Balancing point duty preview
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field

from HVAC.hydronics.proportioning.preliminary_balancing_resistance_basis_v1 import (
    PreliminaryBalancingResistanceBasisV1,
    PreliminaryBalancingResistanceRowV1,
)
from HVAC.hydronics.proportioning.preliminary_route_balancing_requirement_v1 import (
    PreliminaryRouteBalancingPreviewV1,
    PreliminaryRouteBalancingRequirementV1,
)


@dataclass(slots=True)
class BalancingPointDutyPreviewRowV1:
    """
    Combined route/subleg balancing-point duty row.

    This combines:
    - route pressure shortfall preview
    - preliminary balancing resistance basis

    It does not select valves or commit balancing.
    """

    route_id: str = ""
    route_label: str = ""
    sections: str = ""

    flow_kg_s: str = ""
    route_dp: str = ""
    controlling_route_dp: str = ""
    required_added_dp: str = ""
    required_resistance_pa_per_kg_s2: str = ""

    balancing_point_scope: str = "route/subleg balancing point"
    controlling: str = "No"
    status: str = ""


@dataclass(slots=True)
class BalancingPointDutyPreviewV1:
    """
    Preview-only balancing point duty projection.

    Authority boundary:
    • no ProjectState mutation
    • no valve selection
    • no Kv/Kvs
    • no manufacturer catalogue
    • no lockshield setting
    • no pump sizing
    • no pipe resizing
    • no balancing commit
    """

    ready: bool = False
    status: str = "Balancing point duty preview not ready"
    rows: list[BalancingPointDutyPreviewRowV1] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


def _key_from_parts(
    *,
    route_id: str,
    route_label: str,
) -> str:
    route_id = str(route_id or "").strip()
    route_label = str(route_label or "").strip()

    if route_id:
        return f"id:{route_id}"

    if route_label:
        return f"label:{route_label.lower()}"

    return ""


def _route_key(row: PreliminaryRouteBalancingRequirementV1) -> str:
    return _key_from_parts(
        route_id=str(getattr(row, "route_id", "") or ""),
        route_label=str(getattr(row, "route_label", "") or ""),
    )


def _resistance_key(row: PreliminaryBalancingResistanceRowV1) -> str:
    return _key_from_parts(
        route_id=str(getattr(row, "route_id", "") or ""),
        route_label=str(getattr(row, "route_label", "") or ""),
    )


def _is_controlling_text(value: object) -> bool:
    return str(value or "").strip().lower() in {"yes", "true", "1", "y"}


def _row_status(
    *,
    route_row: PreliminaryRouteBalancingRequirementV1,
    resistance_row: PreliminaryBalancingResistanceRowV1 | None,
) -> str:
    if resistance_row is None:
        return "Balancing point duty incomplete — resistance basis missing"

    if _is_controlling_text(route_row.controlling):
        return "Controlling route — no balancing duty required"

    if (
        str(resistance_row.flow_kg_s or "").strip() in {"", "—"}
        or str(resistance_row.required_added_dp or "").strip() in {"", "—"}
        or str(resistance_row.resistance_pa_per_kg_s2 or "").strip() in {"", "—"}
    ):
        return "Balancing point duty incomplete"

    return "Balancing point duty preview calculated"


def build_balancing_point_duty_preview_v1(
    *,
    route_balancing_preview: PreliminaryRouteBalancingPreviewV1 | None,
    resistance_basis: PreliminaryBalancingResistanceBasisV1 | None,
) -> BalancingPointDutyPreviewV1:
    """
    Build a combined balancing-point duty preview.

    H-S24-A:
    This is a display/projection layer joining the existing route shortfall
    and preliminary resistance basis. It does not introduce valve selection.
    """

    if route_balancing_preview is None:
        return BalancingPointDutyPreviewV1(
            ready=False,
            status="Balancing point duty preview not ready",
            blockers=["No preliminary route balancing preview is available"],
        )

    if not route_balancing_preview.ready:
        return BalancingPointDutyPreviewV1(
            ready=False,
            status="Balancing point duty preview not ready",
            blockers=list(route_balancing_preview.blockers or []),
        )

    if resistance_basis is None:
        return BalancingPointDutyPreviewV1(
            ready=False,
            status="Balancing point duty preview not ready",
            blockers=["No preliminary balancing resistance basis is available"],
        )

    if not resistance_basis.ready:
        return BalancingPointDutyPreviewV1(
            ready=False,
            status="Balancing point duty preview not ready",
            blockers=list(resistance_basis.blockers or []),
        )

    resistance_by_key: dict[str, PreliminaryBalancingResistanceRowV1] = {}

    for resistance_row in resistance_basis.rows:
        key = _resistance_key(resistance_row)
        if key:
            resistance_by_key[key] = resistance_row

    rows: list[BalancingPointDutyPreviewRowV1] = []
    blockers: list[str] = []

    for route_row in route_balancing_preview.rows:
        key = _route_key(route_row)
        resistance_row = resistance_by_key.get(key)

        if resistance_row is None:
            blockers.append(
                f"{route_row.route_label}: resistance basis missing"
            )

        rows.append(
            BalancingPointDutyPreviewRowV1(
                route_id=route_row.route_id,
                route_label=route_row.route_label,
                sections=route_row.sections,
                flow_kg_s=(
                    resistance_row.flow_kg_s
                    if resistance_row is not None
                    else "—"
                ),
                route_dp=route_row.route_dp,
                controlling_route_dp=route_row.controlling_route_dp,
                required_added_dp=(
                    resistance_row.required_added_dp
                    if resistance_row is not None
                    else route_row.required_added_resistance_dp
                ),
                required_resistance_pa_per_kg_s2=(
                    resistance_row.resistance_pa_per_kg_s2
                    if resistance_row is not None
                    else "—"
                ),
                balancing_point_scope="route/subleg balancing point",
                controlling=route_row.controlling or "No",
                status=_row_status(
                    route_row=route_row,
                    resistance_row=resistance_row,
                ),
            )
        )

    ready = not blockers

    return BalancingPointDutyPreviewV1(
        ready=ready,
        status=(
            "Balancing point duty preview ready"
            if ready
            else "Balancing point duty preview incomplete"
        ),
        rows=rows,
        blockers=blockers,
    )
