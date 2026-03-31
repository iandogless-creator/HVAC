# ======================================================================
# HVAC/heatloss/segment_to_rows_v1.py
# ======================================================================

from __future__ import annotations
from typing import Any, List, Dict


# ----------------------------------------------------------------------
# Temporary deterministic U-value policy (Phase IV-A)
# ----------------------------------------------------------------------

U_VALUE_POLICY = {
    "EXTERNAL": 0.35,
    "INTER_ROOM": 1.5,
    "ADIABATIC": 0.0,
}


# ----------------------------------------------------------------------
# ΔT resolver (adjacency-aware)
# ----------------------------------------------------------------------

def resolve_delta_t(segment: Any, ps: Any, room: Any) -> float | None:
    Ti = getattr(room, "internal_design_temp_C", None)
    Te = getattr(ps.environment, "external_design_temp_C", None)

    if Ti is None:
        return None

    if segment.boundary_kind == "EXTERNAL":
        if Te is None:
            return None
        return Ti - Te

    if segment.boundary_kind == "INTER_ROOM":
        adj = ps.rooms.get(segment.adjacent_room_id)
        if adj is None:
            return None

        Ti_adj = getattr(adj, "internal_design_temp_C", None)
        if Ti_adj is None:
            return None

        return Ti - Ti_adj

    if segment.boundary_kind == "ADIABATIC":
        return 0.0

    return None


# ----------------------------------------------------------------------
# Main builder
# ----------------------------------------------------------------------

def build_segment_heat_loss_rows(
    *,
    project_state: Any,
    room: Any,
) -> List[Dict]:

    rows: List[Dict] = []

    segments = getattr(project_state, "boundary_segments", {})

    for seg_id, s in segments.items():

        # --------------------------------------------------
        # Only owner computes heat-loss
        # --------------------------------------------------
        if s.owner_room_id != room.room_id:
            continue

        # --------------------------------------------------
        # Geometry → Area
        # --------------------------------------------------
        height = getattr(room.geometry, "height_m", None)
        if height is None or s.length_m is None:
            continue

        area = s.length_m * height

        # --------------------------------------------------
        # U-value (deterministic policy)
        # --------------------------------------------------
        U = U_VALUE_POLICY.get(s.boundary_kind, None)
        if U is None:
            continue

        # --------------------------------------------------
        # ΔT (adjacency-aware)
        # --------------------------------------------------
        dT = resolve_delta_t(s, project_state, room)
        if dT is None:
            continue

        # --------------------------------------------------
        # Heat loss
        # --------------------------------------------------
        Q = U * area * dT

        # --------------------------------------------------
        # Row
        # --------------------------------------------------
        rows.append({
            "surface_id": seg_id,
            "element": s.boundary_kind.lower(),
            "A": area,
            "U": U,
            "dT": dT,
            "Qf": Q,
        })

    return rows