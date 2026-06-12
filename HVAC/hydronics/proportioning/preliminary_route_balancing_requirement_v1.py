# ======================================================================
# HVAC/hydronics/proportioning/preliminary_route_balancing_requirement_v1.py
# ======================================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field

from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    ProportioningInputSnapshotV1,
)
from HVAC.hydronics.proportioning.proportioning_readiness_gate_v1 import (
    evaluate_proportioning_readiness_v1,
)


_TRUE_TEXT = {"yes", "true", "1", "y"}


@dataclass(slots=True)
class PreliminaryRouteBalancingRequirementV1:
    """
    Preliminary route-level balancing requirement.

    This is not valve selection.
    It is only the route pressure shortfall / added resistance basis.
    """

    route_id: str = ""
    route_label: str = ""
    sections: str = ""

    route_dp: str = ""
    controlling_route_dp: str = ""
    shortfall_dp: str = ""
    required_added_resistance_dp: str = ""

    controlling: str = "No"
    status: str = ""


@dataclass(slots=True)
class PreliminaryRouteBalancingPreviewV1:
    """
    Preview of route balancing requirement.

    Authority boundary:
    • no ProjectState mutation
    • no balancing valve selection
    • no pump sizing
    • no pipe resizing
    • no committed return arrangement
    """

    ready: bool = False
    status: str = "Balancing preview not ready"
    controlling_route_id: str = ""
    controlling_route_label: str = ""
    controlling_route_dp: str = ""
    rows: list[PreliminaryRouteBalancingRequirementV1] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


def _is_true_text(value: object) -> bool:
    return str(value or "").strip().lower() in _TRUE_TEXT


def _parse_pa(value: object) -> float | None:
    """
    Parse pressure text such as:
        "7654.1 Pa"
        "7,654.1 Pa"
        7654.1
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text == "—":
        return None

    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    return float(match.group(0))


def _format_pa(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f} Pa"


def build_preliminary_route_balancing_preview_v1(
    snapshot: ProportioningInputSnapshotV1 | None,
) -> PreliminaryRouteBalancingPreviewV1:
    """
    Build preliminary route balancing requirement preview from the
    proportioning input snapshot.

    This only calculates:
        controlling route Δp
        route shortfall
        required added resistance

    It does not select valves or commit any arrangement.
    """
    gate = evaluate_proportioning_readiness_v1(snapshot)

    if snapshot is None:
        return PreliminaryRouteBalancingPreviewV1(
            ready=False,
            status="Balancing preview not ready",
            blockers=["No proportioning input snapshot is available"],
        )

    if not gate.ready:
        return PreliminaryRouteBalancingPreviewV1(
            ready=False,
            status="Balancing preview not ready",
            blockers=list(gate.blockers),
        )

    controlling_routes = [
        route
        for route in snapshot.routes
        if _is_true_text(route.controlling)
    ]

    if len(controlling_routes) != 1:
        return PreliminaryRouteBalancingPreviewV1(
            ready=False,
            status="Balancing preview not ready",
            blockers=[
                f"Expected 1 controlling route, found {len(controlling_routes)}"
            ],
        )

    controlling_route = controlling_routes[0]
    controlling_dp = _parse_pa(controlling_route.route_dp_sum)

    if controlling_dp is None:
        return PreliminaryRouteBalancingPreviewV1(
            ready=False,
            status="Balancing preview not ready",
            blockers=["Controlling route Δp is not available"],
        )

    rows: list[PreliminaryRouteBalancingRequirementV1] = []

    for route in snapshot.routes:
        route_dp = _parse_pa(route.route_dp_sum)

        if route_dp is None:
            shortfall = None
            required_added = None
            status = "Route Δp unavailable"
        elif _is_true_text(route.controlling):
            shortfall = 0.0
            required_added = 0.0
            status = "Controlling route — no added resistance required"
        else:
            shortfall = max(controlling_dp - route_dp, 0.0)
            required_added = shortfall
            status = "Preliminary added resistance requirement"

        rows.append(
            PreliminaryRouteBalancingRequirementV1(
                route_id=route.route_id,
                route_label=route.route_label,
                sections=route.sections,
                route_dp=_format_pa(route_dp),
                controlling_route_dp=_format_pa(controlling_dp),
                shortfall_dp=_format_pa(shortfall),
                required_added_resistance_dp=_format_pa(required_added),
                controlling=route.controlling or "No",
                status=status,
            )
        )

    return PreliminaryRouteBalancingPreviewV1(
        ready=True,
        status="Preliminary route balancing preview ready",
        controlling_route_id=controlling_route.route_id,
        controlling_route_label=controlling_route.route_label,
        controlling_route_dp=_format_pa(controlling_dp),
        rows=rows,
        blockers=[],
    )