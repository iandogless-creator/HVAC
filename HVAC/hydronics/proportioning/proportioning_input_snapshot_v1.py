# ======================================================================
# HVAC/hydronics/proportioning/proportioning_input_snapshot_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProportioningInputSectionV1:
    """
    One section of pipework available to the future proportioning engine.

    Snapshot only:
    • no balancing
    • no pipe resizing
    • no pump sizing
    """

    section_id: str = ""
    order: str = ""
    from_label: str = ""
    to_label: str = ""

    route_id: str = ""
    route_label: str = ""
    leg_id: str = ""
    subleg_id: str = ""
    room_id: str = ""
    emitter_id: str = ""

    q_carried: str = ""
    flow_kg_s: str = ""
    pipe: str = ""
    velocity_m_s: str = ""
    dp_per_m: str = ""
    length_m: str = ""

    k_total: str = ""
    local_dp: str = ""
    straight_dp: str = ""
    section_dp: str = ""

    status: str = ""


@dataclass(slots=True)
class ProportioningInputRouteV1:
    """
    Route-level pressure basis available to future proportioning.
    """

    route_id: str = ""
    route_label: str = ""
    sections: str = ""

    straight_dp_sum: str = ""
    local_dp_sum: str = ""
    route_dp_sum: str = ""

    shortfall_pa: str = ""
    complete: str = ""
    controlling: str = ""

    status: str = ""


@dataclass(slots=True)
class ProportioningInputReturnComparisonV1:
    """
    F+R / F+RR comparison evidence.

    This does not commit the return arrangement.
    """

    route: str = ""
    room: str = ""
    emitter: str = ""

    leg_id: str = ""
    subleg_id: str = ""
    room_id: str = ""
    emitter_id: str = ""

    direct_rank: str = ""
    direct_total_dp: str = ""
    direct_controlling: str = ""

    reverse_rank: str = ""
    reverse_total_dp: str = ""
    reverse_controlling: str = ""

    rr_suitability: str = ""
    status: str = ""


@dataclass(slots=True)
class ProportioningInputSnapshotV1:
    """
    Complete read-only input snapshot for future proportioning.

    This is the bridge between:
    • Basic PS / Local K / route Δp / return comparison previews
    and:
    • future proportioning authority.

    It is not itself a balancing engine.
    """

    sections: list[ProportioningInputSectionV1] = field(default_factory=list)
    routes: list[ProportioningInputRouteV1] = field(default_factory=list)
    return_comparisons: list[ProportioningInputReturnComparisonV1] = field(
        default_factory=list
    )

    status: str = "Snapshot empty"
    warnings: list[str] = field(default_factory=list)


def _text(row: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return str(value)
    return default


def build_proportioning_input_snapshot_v1(
    *,
    section_rows: list[dict[str, Any]] | None = None,
    route_rows: list[dict[str, Any]] | None = None,
    shortfall_rows: list[dict[str, Any]] | None = None,
    return_comparison_rows: list[dict[str, Any]] | None = None,
) -> ProportioningInputSnapshotV1:
    """
    Build the read-only proportioning input snapshot from existing preview rows.

    Display/authority boundary:
    • no ProjectState mutation
    • no balancing
    • no pump selection
    • no pipe resizing
    • no committed return arrangement
    """
    section_rows = section_rows or []
    route_rows = route_rows or []
    shortfall_rows = shortfall_rows or []
    return_comparison_rows = return_comparison_rows or []

    warnings: list[str] = []

    sections = [
        ProportioningInputSectionV1(
            section_id=_text(row, "section_id"),
            order=_text(row, "order"),
            from_label=_text(row, "from", "from_label"),
            to_label=_text(row, "to", "to_label"),
            route_id=_text(row, "route_id"),
            route_label=_text(row, "route", "route_label"),
            leg_id=_text(row, "leg_id"),
            subleg_id=_text(row, "subleg_id"),
            room_id=_text(row, "room_id"),
            emitter_id=_text(row, "emitter_id"),
            q_carried=_text(row, "q_carried"),
            flow_kg_s=_text(row, "flow_kg_s"),
            pipe=_text(row, "pipe"),
            velocity_m_s=_text(row, "velocity_m_s"),
            dp_per_m=_text(row, "dp_per_m"),
            length_m=_text(row, "length_m"),
            k_total=_text(row, "k_total"),
            local_dp=_text(row, "local_dp"),
            straight_dp=_text(row, "straight_dp"),
            section_dp=_text(row, "section_dp"),
            status=_text(row, "status"),
        )
        for row in section_rows
    ]

    shortfall_by_route = {
        _text(row, "route_id", "route", "route_label"): row
        for row in shortfall_rows
    }

    routes: list[ProportioningInputRouteV1] = []

    for row in route_rows:
        route_key = _text(row, "route_id", "route", "route_label")
        shortfall = shortfall_by_route.get(route_key, {})

        routes.append(
            ProportioningInputRouteV1(
                route_id=_text(row, "route_id"),
                route_label=_text(row, "route", "route_label"),
                sections=_text(row, "sections"),
                straight_dp_sum=_text(
                    row,
                    "straight_dp_sum",
                    "sum_straight_dp",
                    "straight_dp",
                ),
                local_dp_sum=_text(
                    row,
                    "local_dp_sum",
                    "sum_local_dp",
                    "local_dp",
                ),
                route_dp_sum=_text(
                    row,
                    "route_dp_sum",
                    "sum_route_dp",
                    "route_dp",
                    "route_total_dp",
                    "total_dp",
                ),
                shortfall_pa=_text(
                    shortfall,
                    "shortfall_pa",
                    "shortfall_dp",
                    "shortfall",
                ),
                complete=_text(row, "complete"),
                controlling=_text(row, "controlling"),
                status=_text(row, "status"),
            )
        )
    return_comparisons = [
        ProportioningInputReturnComparisonV1(
            route=_text(row, "route"),
            room=_text(row, "room"),
            emitter=_text(row, "emitter"),
            leg_id=_text(row, "leg_id"),
            subleg_id=_text(row, "subleg_id"),
            room_id=_text(row, "room_id"),
            emitter_id=_text(row, "emitter_id"),
            direct_rank=_text(row, "direct_rank"),
            direct_total_dp=_text(row, "direct_total_dp"),
            direct_controlling=_text(row, "direct_controlling"),
            reverse_rank=_text(row, "reverse_rank"),
            reverse_total_dp=_text(row, "reverse_total_dp"),
            reverse_controlling=_text(row, "reverse_controlling"),
            rr_suitability=_text(row, "rr_suitability"),
            status=_text(row, "status"),
        )
        for row in return_comparison_rows
    ]

    if not sections:
        warnings.append("No Basic PS / Local K section rows available")

    if not routes:
        warnings.append("No route Δp rows available")

    if not return_comparisons:
        warnings.append("No F+R / F+RR return comparison rows available")

    if warnings:
        status = "Snapshot incomplete"
    else:
        status = "Snapshot ready"

    return ProportioningInputSnapshotV1(
        sections=sections,
        routes=routes,
        return_comparisons=return_comparisons,
        status=status,
        warnings=warnings,
    )