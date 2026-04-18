from __future__ import annotations

from typing import Optional

from HVAC.core.value_resolution import resolve_effective_internal_temp_C


from HVAC.core.value_resolution import resolve_effective_internal_temp_C


class AdjacencyDeltaTResolver:

    @staticmethod
    def resolve_delta_t_K(
        *,
        project_state,
        owner_room,
        boundary_kind,
        adjacent_room_id,
    ) -> float | None:

        ti, _ = resolve_effective_internal_temp_C(project_state, owner_room)

        if ti is None:
            return None

        # EXTERNAL
        if boundary_kind == "EXTERNAL":
            env = project_state.environment
            te = getattr(env, "external_design_temp_C", None) if env else None

            if te is None:
                return None

            return ti - te

        # INTER_ROOM
        if boundary_kind == "INTER_ROOM":
            if not adjacent_room_id:
                return None

            adj_room = project_state.rooms.get(adjacent_room_id)
            if not adj_room:
                return None

            ati, _ = resolve_effective_internal_temp_C(project_state, adj_room)

            if ati is None:
                return None

            return ti - ati

        # ADIABATIC
        if boundary_kind == "ADIABATIC":
            return 0.0

        return None