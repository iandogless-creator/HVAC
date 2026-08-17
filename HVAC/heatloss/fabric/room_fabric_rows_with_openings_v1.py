from __future__ import annotations

from dataclasses import replace
import re
from typing import Any

from HVAC.heatloss.dto.fabric_surface_row_v1 import FabricSurfaceRowV1
from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1
from HVAC.heatloss.fabric.room_opening_schedule_thermal_projection_v1 import (
    resolve_room_opening_schedule_thermal_projection_v1,
)


def _schedule_openings(schedule: Any) -> tuple[Any, ...]:
    if schedule is None:
        return ()
    openings = getattr(schedule, "openings", ())
    return tuple(openings or ())


def _is_external_wall(row: FabricSurfaceRowV1) -> bool:
    element = str(getattr(row, "element", "") or "").lower()
    if element not in {"external_wall", "external wall"}:
        return False
    segment = getattr(row, "_segment", None)
    boundary_kind = str(
        getattr(segment, "boundary_kind", "EXTERNAL") or "EXTERNAL"
    ).upper()
    return boundary_kind == "EXTERNAL"


def _qf_for_row(
    *,
    area_m2: float,
    u_value_W_m2K: float | None,
    delta_t_K: float | None,
) -> float | None:
    if u_value_W_m2K is None or delta_t_K is None or area_m2 <= 0.0:
        return None
    return float(area_m2) * float(u_value_W_m2K) * float(delta_t_K)


def _opening_surface_id(
    room_id: str,
    opening_type: str,
    construction_id: str,
    index: int,
) -> str:
    safe_cid = re.sub(r"[^A-Za-z0-9_.-]+", "-", construction_id).strip("-")
    return (
        f"{room_id}-room-opening-{opening_type.lower()}-"
        f"{index + 1}-{safe_cid or 'construction'}"
    )


def build_room_fabric_rows_with_openings_v1(
    project: Any,
    room: Any,
) -> list[FabricSurfaceRowV1]:
    """Return the canonical room fabric rows including room-level openings.

    Room schedules intentionally do not assign an opening to a particular
    external wall in v1.  Their area is therefore deducted proportionally
    from every external-wall row.  This preserves wall identities and gives
    an exact room-level net wall area without inventing physical placement.

    The returned rows are shared by the committed heat-loss snapshot and the
    Heat-Loss worksheet projection.  This function does not mutate ProjectState.
    """
    base_rows = list(FabricFromSegmentsV1.build_rows_for_room(project, room))
    room_id = str(getattr(room, "room_id", "") or "")
    schedules = getattr(project, "room_opening_schedules", {}) or {}
    schedule = schedules.get(room_id)
    if not _schedule_openings(schedule):
        return base_rows

    legacy_opening_rows = [
        row
        for row in base_rows
        if getattr(row, "parent_surface_id", None) is not None
    ]
    if legacy_opening_rows:
        raise RuntimeError(
            f"Room {room_id!r} contains both room-schedule and surface openings."
        )

    external_indexes = [
        index for index, row in enumerate(base_rows) if _is_external_wall(row)
    ]
    gross_external_wall_area = sum(
        float(base_rows[index].area_m2) for index in external_indexes
    )

    projection = resolve_room_opening_schedule_thermal_projection_v1(
        schedule=schedule,
        constructions=getattr(project, "constructions", {}) or {},
        gross_external_wall_area_m2=gross_external_wall_area,
    )
    if not projection.ready:
        raise RuntimeError("; ".join(projection.blockers))

    if not projection.rows:
        return base_rows
    if not external_indexes or gross_external_wall_area <= 0.0:
        raise RuntimeError(
            f"Room {room_id!r} has external openings but no external-wall area."
        )

    scale = (
        projection.net_external_wall_area_m2
        / projection.gross_external_wall_area_m2
    )
    external_delta_t = base_rows[external_indexes[0]].delta_t_K
    opening_rows = [
        FabricSurfaceRowV1(
            surface_id=_opening_surface_id(
                room_id,
                item.opening_type,
                item.construction_id,
                index,
            ),
            room_id=room_id,
            element=(
                "window" if item.opening_type == "WINDOW" else "external_door"
            ),
            area_m2=float(item.area_m2),
            u_value_W_m2K=float(item.u_value_W_m2K),
            delta_t_K=external_delta_t,
            qf_W=_qf_for_row(
                area_m2=float(item.area_m2),
                u_value_W_m2K=float(item.u_value_W_m2K),
                delta_t_K=external_delta_t,
            ),
            construction_id=item.construction_id,
            parent_surface_id=None,
            _segment=None,
        )
        for index, item in enumerate(projection.rows)
    ]

    last_external_index = external_indexes[-1]
    result: list[FabricSurfaceRowV1] = []
    external_index_set = set(external_indexes)
    for index, row in enumerate(base_rows):
        if index in external_index_set:
            net_area = float(row.area_m2) * scale
            if net_area > 1.0e-12:
                result.append(
                    replace(
                        row,
                        area_m2=net_area,
                        qf_W=_qf_for_row(
                            area_m2=net_area,
                            u_value_W_m2K=row.u_value_W_m2K,
                            delta_t_K=row.delta_t_K,
                        ),
                    )
                )
        else:
            result.append(row)
        if index == last_external_index:
            result.extend(opening_rows)

    return result
