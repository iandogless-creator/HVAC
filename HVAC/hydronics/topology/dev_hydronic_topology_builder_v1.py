# ======================================================================
# HVAC/hydronics/topology/dev_hydronic_topology_builder_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicTopologyV1,
)


# ======================================================================
# DEV Hydronic Topology Builder V1
# ======================================================================

class DevHydronicTopologyBuilderV1:
    """
    DEV-only hydronic topology seed builder.

    Purpose
    -------
    Build a simple HydronicTopologyV1 from the current ProjectState room list.

    This is a temporary bridge before the real Hydronic Topology Wizard exists.

    Authority rule
    --------------
    - ProjectState.rooms remains stable room/spatial identity.
    - HydronicTopologyV1 becomes hydronic route/order authority.
    - This builder only seeds that authority for DEV/testing.

    Explicitly forbidden
    --------------------
    - No pipe sizing.
    - No pressure-drop calculation.
    - No proportioning calculation.
    - No GUI painting.
    - No mutation of room IDs.
    """

    @staticmethod
    def build_single_leg_from_project(
        project_state: Any,
        *,
        heat_source_room_id: str | None = None,
        leg_id: str = "leg-001",
        leg_label: str = "Heating Leg 1",
    ) -> HydronicTopologyV1:
        """
        Build a simple one-leg hydronic topology.

        The heat-source room is excluded from route_room_ids unless the user
        later explicitly models it as a separate downstream emitter/load.

        Default index room = last downstream route room.
        """

        rooms = getattr(project_state, "rooms", {}) or {}

        room_ids = [
            str(room_id)
            for room_id in rooms.keys()
            if room_id is not None
        ]

        resolved_heat_source_room_id = (
            str(heat_source_room_id)
            if heat_source_room_id
            else DevHydronicTopologyBuilderV1._default_heat_source_room_id(room_ids)
        )

        route_room_ids = [
            room_id
            for room_id in room_ids
            if room_id != resolved_heat_source_room_id
        ]

        index_room_id = route_room_ids[-1] if route_room_ids else None

        return HydronicTopologyV1(
            heat_source_room_id=resolved_heat_source_room_id,
            legs=[
                HydronicLegV1(
                    leg_id=leg_id,
                    label=leg_label,
                    route_room_ids=route_room_ids,
                    index_room_id=index_room_id,
                    sublegs=[],
                )
            ],
        )

    @staticmethod
    def install_single_leg_on_project(
        project_state: Any,
        *,
        heat_source_room_id: str | None = None,
        leg_id: str = "leg-001",
        leg_label: str = "Heating Leg 1",
        overwrite: bool = False,
    ) -> HydronicTopologyV1:
        """
        Build and attach a DEV hydronic topology to ProjectState.

        By default this does not overwrite an existing hydronic_topology.
        """

        existing_topology = getattr(project_state, "hydronic_topology", None)

        if existing_topology is not None and not overwrite:
            return existing_topology

        topology = DevHydronicTopologyBuilderV1.build_single_leg_from_project(
            project_state,
            heat_source_room_id=heat_source_room_id,
            leg_id=leg_id,
            leg_label=leg_label,
        )

        project_state.hydronic_topology = topology
        return topology

    @staticmethod
    def _default_heat_source_room_id(room_ids: list[str]) -> str:
        """
        Resolve DEV fallback heat-source room id.

        Current DEV assumption:
        - first room in ProjectState.rooms is heat-source location
        - this is only a seed fallback, not final authority
        """

        return room_ids[0] if room_ids else ""