# ======================================================================
# HVAC/hydronics/builders/hydronic_skeleton_from_project_state_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.hydronics.models.hydronic_skeleton_v1 import HydronicSkeletonV1
from HVAC.hydronics.models.hydronic_skeleton_generator_v1 import (
    RoomLoadV1,
    generate_initial_hydronic_skeleton_v1,
)


def build_hydronic_skeleton_from_project_state_v1(
    project_state: Any,
    *,
    skeleton_id: str = "skeleton_1",
) -> HydronicSkeletonV1:
    """
    Build hydronic skeleton intent from ProjectState.

    Authority
    ---------
    • Reads ProjectState only
    • Does not mutate ProjectState
    • Does not calculate heat-loss
    • Does not size pipes
    • Does not calculate pressure loss
    """

    room_loads = extract_room_loads_from_project_state_v1(project_state)

    skeleton = generate_initial_hydronic_skeleton_v1(
        room_loads,
        skeleton_id=skeleton_id,
    )

    # Persisted hydronic intent is carried into the skeleton for display/use.
    skeleton.emitters.update(
        dict(getattr(project_state, "emitters", {}) or {})
    )

    return skeleton


def extract_room_loads_from_project_state_v1(project_state: Any) -> list[RoomLoadV1]:
    """
    Extract room heat-load intent from the committed heat-loss result container.

    Current confirmed heat-loss shape:

        project_state.heatloss_results["room_totals"][room_id]["q_total_W"]

    Room names are resolved from project_state.rooms where available.
    """

    heatloss_results = getattr(project_state, "heatloss_results", None) or {}
    room_totals = heatloss_results.get("room_totals", {}) or {}
    rooms_by_id = getattr(project_state, "rooms", {}) or {}

    loads: list[RoomLoadV1] = []

    for room_id, totals in room_totals.items():
        qt_w = _resolve_q_total_W(totals)

        if qt_w is None:
            continue

        room = rooms_by_id.get(room_id)

        room_name = (
            getattr(room, "name", None)
            or getattr(room, "room_name", None)
            or str(room_id)
        )

        loads.append(
            RoomLoadV1(
                room_id=str(room_id),
                room_name=str(room_name),
                design_heat_loss_w=float(qt_w),
            )
        )

    return sorted(
        loads,
        key=lambda r: (r.room_name.lower(), r.room_id.lower()),
    )


def _resolve_q_total_W(totals: Any) -> float | None:
    """
    Resolve total room heat load in watts from current or near-current shapes.
    """

    if isinstance(totals, dict):
        for key in (
            "q_total_W",
            "qt_W",
            "Qt_W",
            "total_W",
            "total_heat_loss_W",
            "heat_loss_W",
        ):
            value = totals.get(key)
            if value is not None:
                return float(value)

        return None

    for attr in (
        "q_total_W",
        "qt_W",
        "Qt_W",
        "total_W",
        "total_heat_loss_W",
        "heat_loss_W",
    ):
        value = getattr(totals, attr, None)
        if value is not None:
            return float(value)

    return None
