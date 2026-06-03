# HVAC/hydronics/proportioning/route_proportioning_shortfall_preview_v1.py
#
# H-S18 — Route Δp shortfall preview
#
# Preview-only:
# - no valve settings
# - no pump selection
# - no pipe resizing
# - no final proportioning commit

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class RouteShortfallPreviewRowV1:
    route_key: str
    leg_id: str
    subleg_id: str
    route_label: str

    rank: int | None
    route_dp_Pa: float | None
    controlling_dp_Pa: float | None
    shortfall_dp_Pa: float | None

    complete: bool
    controlling: bool
    action: str
    status: str


@dataclass(frozen=True, slots=True)
class RouteShortfallPreviewV1:
    rows: tuple[RouteShortfallPreviewRowV1, ...]
    controlling_route_key: str | None
    controlling_dp_Pa: float | None
    complete: bool
    status: str


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default

    if hasattr(obj, name):
        return getattr(obj, name)

    if isinstance(obj, dict):
        return obj.get(name, default)

    return default


def _first_existing(obj: Any, names: Iterable[str], default: Any = None) -> Any:
    for name in names:
        value = _get(obj, name, None)
        if value is not None:
            return value
    return default


def _route_key(route: Any) -> str:
    route_key = _first_existing(
        route,
        (
            "route_id",
            "route_key",
            "key",
        ),
        None,
    )

    if route_key:
        return str(route_key)

    leg_id = str(_first_existing(route, ("leg_id",), ""))
    subleg_id = str(_first_existing(route, ("subleg_id",), ""))

    if leg_id or subleg_id:
        return f"{leg_id}:{subleg_id}"

    return "unknown-route"


def _route_label(route: Any) -> str:
    label = _first_existing(
        route,
        (
            "route_label",
            "label",
            "display_label",
            "name",
        ),
        None,
    )

    if label:
        return str(label)

    leg_label = _first_existing(route, ("leg_label",), None)
    subleg_label = _first_existing(route, ("subleg_label",), None)

    if leg_label and subleg_label:
        return f"{leg_label} / {subleg_label}"

    if subleg_label:
        return str(subleg_label)

    return _route_key(route)


def _route_dp(route: Any) -> float | None:
    value = _first_existing(
        route,
        (
            "route_pressure_drop_total_Pa",
            "route_dp_Pa",
            "route_pressure_drop_Pa",
            "route_total_pressure_drop_Pa",
            "total_route_dp_Pa",
            "total_route_pressure_drop_Pa",
            "total_pressure_drop_Pa",
            "section_total_pressure_drop_Pa",
            "sum_route_dp_Pa",
            "sum_pressure_drop_Pa",
            "dp_Pa",
        ),
        None,
    )

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _route_rank(route: Any) -> int | None:
    value = _first_existing(route, ("rank", "route_rank", "pressure_rank"), None)

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_complete(route: Any) -> bool:
    value = _first_existing(route, ("complete", "is_complete"), True)
    return bool(value)


def _is_controlling(route: Any) -> bool:
    value = _first_existing(
        route,
        (
            "is_controlling_candidate",
            "controlling",
            "is_controlling",
            "controlling_route",
            "is_controlling_route",
        ),
        False,
    )
    return bool(value)


def _projection_routes(route_pressure_projection: Any) -> tuple[Any, ...]:
    rows = _first_existing(
        route_pressure_projection,
        (
            "routes",
            "rows",
            "route_rows",
        ),
        (),
    )

    return tuple(rows or ())


def build_route_proportioning_shortfall_preview_v1(
    route_pressure_projection: Any,
) -> RouteShortfallPreviewV1:
    """
    Build H-S18 preview rows from the H-S17 route pressure projection.

    Controlling route selection:
    1. Use an existing controlling=True flag if present.
    2. Otherwise use the complete route with the highest route Δp.

    For complete non-controlling routes:
        shortfall = controlling_route_dp - route_dp
    """

    routes = _projection_routes(route_pressure_projection)

    complete_routes = [
        route
        for route in routes
        if _is_complete(route) and _route_dp(route) is not None
    ]

    explicit_controlling = [
        route
        for route in complete_routes
        if _is_controlling(route)
    ]

    if explicit_controlling:
        controlling_route = explicit_controlling[0]
    elif complete_routes:
        controlling_route = max(
            complete_routes,
            key=lambda route: _route_dp(route) or 0.0,
        )
    else:
        controlling_route = None

    controlling_route_key = (
        _route_key(controlling_route)
        if controlling_route is not None
        else None
    )

    controlling_dp = (
        _route_dp(controlling_route)
        if controlling_route is not None
        else None
    )

    rows: list[RouteShortfallPreviewRowV1] = []

    for route in routes:
        key = _route_key(route)
        route_dp = _route_dp(route)
        complete = _is_complete(route)

        is_controlling = (
            key == controlling_route_key
            if controlling_route_key is not None
            else False
        )

        if not complete:
            shortfall = None
            action = "Cannot compare"
            status = "Incomplete — cannot compare"

        elif route_dp is None:
            shortfall = None
            action = "Cannot compare"
            status = "Missing route Δp — cannot compare"

        elif controlling_dp is None:
            shortfall = None
            action = "Cannot compare"
            status = "No controlling route — cannot compare"

        elif is_controlling:
            shortfall = 0.0
            action = "No added resistance"
            status = "Controlling route — no added resistance"

        else:
            shortfall = max(0.0, controlling_dp - route_dp)
            action = "Add resistance preview"
            status = "Needs added resistance preview"

        rows.append(
            RouteShortfallPreviewRowV1(
                route_key=key,
                leg_id=str(_first_existing(route, ("leg_id",), "")),
                subleg_id=str(_first_existing(route, ("subleg_id",), "")),
                route_label=_route_label(route),
                rank=_route_rank(route),
                route_dp_Pa=route_dp,
                controlling_dp_Pa=controlling_dp,
                shortfall_dp_Pa=shortfall,
                complete=complete,
                controlling=is_controlling,
                action=action,
                status=status,
            )
        )

    return RouteShortfallPreviewV1(
        rows=tuple(rows),
        controlling_route_key=controlling_route_key,
        controlling_dp_Pa=controlling_dp,
        complete=bool(rows) and controlling_dp is not None,
        status=(
            "Route shortfall preview ready"
            if rows and controlling_dp is not None
            else "No complete controlling route available"
        ),
    )