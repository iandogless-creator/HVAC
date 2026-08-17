from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RoomOpeningThermalRowV1:
    opening_type: str
    label: str
    construction_id: str
    construction_name: str
    area_m2: float
    u_value_W_m2K: float


@dataclass(frozen=True, slots=True)
class RoomOpeningScheduleThermalProjectionV1:
    ready: bool
    gross_external_wall_area_m2: float
    external_opening_area_m2: float
    net_external_wall_area_m2: float
    excluded_internal_opening_area_m2: float
    rows: tuple[RoomOpeningThermalRowV1, ...]
    blockers: tuple[str, ...]


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number) or number <= 0.0:
        return None
    return number


def resolve_room_opening_schedule_thermal_projection_v1(
    *,
    schedule: Any,
    constructions: Mapping[str, Any],
    gross_external_wall_area_m2: float,
) -> RoomOpeningScheduleThermalProjectionV1:
    """Resolve room-level external openings without inventing wall placement.

    External openings are grouped by opening type and construction identity.
    Different physical sizes using the same construction share one thermal
    row.  Internal doors remain in the room schedule but are excluded from
    external-wall area and external fabric heat loss.
    """
    blockers: list[str] = []
    try:
        gross_area = float(gross_external_wall_area_m2)
    except (TypeError, ValueError):
        gross_area = 0.0
        blockers.append("Gross external-wall area is unavailable.")
    if not isfinite(gross_area) or gross_area < 0.0:
        gross_area = 0.0
        blockers.append("Gross external-wall area must be finite and non-negative.")

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    external_area = 0.0
    excluded_internal_area = 0.0
    openings = _value(schedule, "openings", ()) if schedule is not None else ()

    for index, opening in enumerate(openings or ()):
        opening_type = str(_value(opening, "opening_type", "") or "").upper()
        profile_id = str(_value(opening, "profile_id", "") or "").upper()
        width = _positive_float(_value(opening, "width_m", None))
        height = _positive_float(_value(opening, "height_m", None))
        try:
            quantity = int(_value(opening, "quantity", 0))
        except (TypeError, ValueError):
            quantity = 0

        if width is None or height is None or quantity <= 0:
            blockers.append(
                f"Opening schedule item {index + 1} has invalid dimensions or quantity."
            )
            continue
        area = width * height * quantity

        if opening_type == "DOOR" and profile_id == "INTERNAL_DOOR":
            excluded_internal_area += area
            continue
        if opening_type not in {"WINDOW", "DOOR"}:
            blockers.append(
                f"Opening schedule item {index + 1} has unsupported type "
                f"{opening_type or 'Not set'}."
            )
            continue

        construction_id = str(
            _value(opening, "construction_id", "") or ""
        ).strip()
        if not construction_id:
            blockers.append(
                f"Opening schedule item {index + 1} has no construction."
            )
            continue
        construction = constructions.get(construction_id)
        if construction is None:
            blockers.append(
                f"Opening construction {construction_id!r} is unavailable."
            )
            continue
        u_value = _positive_float(
            _value(construction, "u_value_W_m2K", None)
        )
        if u_value is None:
            blockers.append(
                f"Opening construction {construction_id!r} has no valid U-value."
            )
            continue

        construction_name = str(
            _value(construction, "name", None)
            or _value(construction, "display_name", None)
            or construction_id
        )
        key = (opening_type, construction_id)
        group = grouped.setdefault(
            key,
            {
                "area_m2": 0.0,
                "u_value_W_m2K": u_value,
                "construction_name": construction_name,
            },
        )
        group["area_m2"] += area
        external_area += area

    if external_area > gross_area + 1.0e-9:
        blockers.append(
            "External opening area exceeds gross external-wall area."
        )
    net_area = max(gross_area - external_area, 0.0)

    type_order = {"WINDOW": 0, "DOOR": 1}
    rows = tuple(
        RoomOpeningThermalRowV1(
            opening_type=opening_type,
            label="Window" if opening_type == "WINDOW" else "External Door",
            construction_id=construction_id,
            construction_name=str(group["construction_name"]),
            area_m2=float(group["area_m2"]),
            u_value_W_m2K=float(group["u_value_W_m2K"]),
        )
        for (opening_type, construction_id), group in sorted(
            grouped.items(),
            key=lambda item: (
                type_order[item[0][0]],
                str(item[1]["construction_name"]).lower(),
                item[0][1],
            ),
        )
    )

    return RoomOpeningScheduleThermalProjectionV1(
        ready=not blockers,
        gross_external_wall_area_m2=gross_area,
        external_opening_area_m2=external_area,
        net_external_wall_area_m2=net_area,
        excluded_internal_opening_area_m2=excluded_internal_area,
        rows=rows,
        blockers=tuple(blockers),
    )
