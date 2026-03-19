# ======================================================================
# HVAC/topology/adjacency_delta_t_resolver.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.core.value_resolution import resolve_effective_internal_temp_C


class AdjacencyDeltaTResolver:
    """
    Resolve delta-T for topology-aware fabric rows.

    Rules
    -----
    EXTERNAL   -> Ti(owner) - Te
    INTER_ROOM -> Ti(owner) - Ti(adjacent)
    ADIABATIC  -> 0
    """

    @staticmethod
    def resolve_delta_t_K(
        *,
        project_state: Any,
        owner_room: Any,
        boundary_kind: str,
        adjacent_room_id: str | None,
    ) -> float | None:
        env = getattr(project_state, "environment", None)
        if env is None or env.external_design_temp_C is None:
            return None

        owner_ti_C, _ = resolve_effective_internal_temp_C(project_state, owner_room)

        if owner_ti_C is None:
            return None

        if boundary_kind == "EXTERNAL":
            return owner_ti_C - env.external_design_temp_C

        if boundary_kind == "ADIABATIC":
            return 0.0

        if boundary_kind == "INTER_ROOM":
            if not adjacent_room_id:
                return None

            adj_room = getattr(project_state, "rooms", {}).get(adjacent_room_id)
            if adj_room is None:
                return None

            adj_ti_C, _ = resolve_effective_internal_temp_C(project_state, adj_room)
            if adj_ti_C is None:
                return None

            return owner_ti_C - adj_ti_C

        return None