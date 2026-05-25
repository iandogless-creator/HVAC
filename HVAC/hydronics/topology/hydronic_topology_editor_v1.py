# ======================================================================
# HVAC/hydronics/topology/hydronic_topology_editor_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_route_room_ids_for_leg,
    set_primary_index_room_id_for_leg,
    set_primary_route_room_ids_for_leg,
)

# ======================================================================
# HydronicTopologyEditorV1
# ======================================================================

class HydronicTopologyEditorV1:
    """
    Pure helper/editor for HydronicTopologyV1 route authority.

    Purpose
    -------
    Provide small deterministic editing operations for hydronic route order.

    This is intended to support the future Hydronic Topology Wizard.

    Authority rules
    ---------------
    - room_id remains stable identity.
    - route_room_ids define hydronic route order.
    - index_room_id is mutable design/index intent for a leg/subleg.
    - selected index room may be moved to terminal route position.

    Explicitly forbidden
    --------------------
    - no pipe sizing
    - no pressure-drop calculation
    - no proportioning calculation
    - no GUI painting
    - no ProjectState persistence
    - no room_id mutation
    """

    # ------------------------------------------------------------------
    # Leg lookup
    # ------------------------------------------------------------------
    @staticmethod
    def find_leg(
        topology: HydronicTopologyV1,
        leg_id: str,
    ) -> HydronicLegV1 | None:
        """
        Return the leg with matching leg_id, or None.
        """

        for leg in topology.legs:
            if leg.leg_id == leg_id:
                return leg

        return None

    @staticmethod
    def move_room_up(
            topology: HydronicTopologyV1,
            leg_id: str,
            room_id: str,
    ) -> HydronicTopologyV1:
        """
        Move room_id one position earlier in the leg's primary subleg route.

        H-S7:
        Legs do not finally own rooms directly.
        This edits the primary subleg and mirrors to legacy leg.route_room_ids.
        """

        HydronicTopologyEditorV1.require_leg(topology, leg_id)
        room_id = str(room_id)

        route_room_ids = list(
            primary_route_room_ids_for_leg(
                topology=topology,
                leg_id=leg_id,
            )
        )

        if room_id not in route_room_ids:
            raise ValueError(
                f"Cannot move room {room_id!r} up; "
                f"room is not in primary subleg for leg {leg_id!r}"
            )

        index = route_room_ids.index(room_id)

        if index == 0:
            return topology

        route_room_ids[index - 1], route_room_ids[index] = (
            route_room_ids[index],
            route_room_ids[index - 1],
        )

        return set_primary_route_room_ids_for_leg(
            topology=topology,
            leg_id=leg_id,
            room_ids=route_room_ids,
        )

    @staticmethod
    def move_room_down(
            topology: HydronicTopologyV1,
            leg_id: str,
            room_id: str,
    ) -> HydronicTopologyV1:
        """
        Move room_id one position later in the leg's primary subleg route.

        H-S7:
        Legs do not finally own rooms directly.
        This edits the primary subleg and mirrors to legacy leg.route_room_ids.
        """

        HydronicTopologyEditorV1.require_leg(topology, leg_id)
        room_id = str(room_id)

        route_room_ids = list(
            primary_route_room_ids_for_leg(
                topology=topology,
                leg_id=leg_id,
            )
        )

        if room_id not in route_room_ids:
            raise ValueError(
                f"Cannot move room {room_id!r} down; "
                f"room is not in primary subleg for leg {leg_id!r}"
            )

        index = route_room_ids.index(room_id)

        if index >= len(route_room_ids) - 1:
            return topology

        route_room_ids[index], route_room_ids[index + 1] = (
            route_room_ids[index + 1],
            route_room_ids[index],
        )

        return set_primary_route_room_ids_for_leg(
            topology=topology,
            leg_id=leg_id,
            room_ids=route_room_ids,
        )

    @staticmethod
    def require_leg(
        topology: HydronicTopologyV1,
        leg_id: str,
    ) -> HydronicLegV1:
        """
        Return the leg with matching leg_id, or raise ValueError.
        """

        leg = HydronicTopologyEditorV1.find_leg(topology, leg_id)

        if leg is None:
            raise ValueError(f"Hydronic leg not found: {leg_id!r}")

        return leg

    # ------------------------------------------------------------------
    # Leg route editing
    # ------------------------------------------------------------------
    @staticmethod
    def move_room_to_leg_terminal(
            topology: HydronicTopologyV1,
            leg_id: str,
            room_id: str,
            *,
            set_index: bool = True,
    ) -> HydronicTopologyV1:
        """
        Move room_id to the terminal/end position of a leg's primary subleg.

        H-S7:
        Legs do not finally own rooms directly.
        This edits the primary subleg and mirrors to legacy leg.route_room_ids.

        If room_id already exists in the primary subleg route, it is removed
        from its current position and appended at the end.

        If room_id is not already in the primary subleg route, it is appended.

        By default, the primary subleg index_room_id is also set to room_id.
        """

        HydronicTopologyEditorV1.require_leg(topology, leg_id)
        room_id = str(room_id)

        HydronicTopologyEditorV1._reject_heat_source_room(
            topology=topology,
            room_id=room_id,
        )

        route_room_ids = [
            existing_room_id
            for existing_room_id in primary_route_room_ids_for_leg(
                topology=topology,
                leg_id=leg_id,
            )
            if existing_room_id != room_id
        ]

        route_room_ids.append(room_id)

        set_primary_route_room_ids_for_leg(
            topology=topology,
            leg_id=leg_id,
            room_ids=route_room_ids,
        )

        if set_index:
            set_primary_index_room_id_for_leg(
                topology=topology,
                leg_id=leg_id,
                room_id=room_id,
            )

        return topology

    @staticmethod
    def set_leg_index_room(
        topology: HydronicTopologyV1,
        leg_id: str,
        room_id: str,
        *,
        move_to_terminal: bool = False,
    ) -> HydronicTopologyV1:
        """
        Set a leg's mutable selected/default index room.

        If move_to_terminal=True, the selected room is also moved to the
        terminal/end position of that leg route.
        """

        if move_to_terminal:
            return HydronicTopologyEditorV1.move_room_to_leg_terminal(
                topology=topology,
                leg_id=leg_id,
                room_id=room_id,
                set_index=True,
            )

        leg = HydronicTopologyEditorV1.require_leg(topology, leg_id)
        room_id = str(room_id)

        HydronicTopologyEditorV1._reject_heat_source_room(
            topology=topology,
            room_id=room_id,
        )

        if room_id not in leg.route_room_ids:
            raise ValueError(
                f"Cannot set index room {room_id!r}; "
                f"room is not in leg {leg_id!r}"
            )

        return set_primary_index_room_id_for_leg(
            topology=topology,
            leg_id=leg_id,
            room_id=room_id,
        )

    # ------------------------------------------------------------------
    # Subleg lookup
    # ------------------------------------------------------------------
    @staticmethod
    def iter_sublegs(
        leg_or_subleg: HydronicLegV1 | HydronicSublegV1,
    ) -> Iterable[HydronicSublegV1]:
        """
        Yield all nested sublegs depth-first.
        """

        for subleg in leg_or_subleg.sublegs:
            yield subleg
            yield from HydronicTopologyEditorV1.iter_sublegs(subleg)

    @staticmethod
    def find_subleg(
        topology: HydronicTopologyV1,
        subleg_id: str,
    ) -> HydronicSublegV1 | None:
        """
        Return the subleg with matching subleg_id, or None.
        """

        for leg in topology.legs:
            for subleg in HydronicTopologyEditorV1.iter_sublegs(leg):
                if subleg.subleg_id == subleg_id:
                    return subleg

        return None

    @staticmethod
    def require_subleg(
        topology: HydronicTopologyV1,
        subleg_id: str,
    ) -> HydronicSublegV1:
        """
        Return the subleg with matching subleg_id, or raise ValueError.
        """

        subleg = HydronicTopologyEditorV1.find_subleg(topology, subleg_id)

        if subleg is None:
            raise ValueError(f"Hydronic subleg not found: {subleg_id!r}")

        return subleg

    # ------------------------------------------------------------------
    # Subleg route editing
    # ------------------------------------------------------------------
    @staticmethod
    def move_room_to_subleg_terminal(
        topology: HydronicTopologyV1,
        subleg_id: str,
        room_id: str,
        *,
        set_index: bool = True,
    ) -> HydronicTopologyV1:
        """
        Move room_id to the terminal/end position of a subleg route.

        This mirrors move_room_to_leg_terminal(), but for a specific subleg.
        """

        room_id = str(room_id)
        subleg = HydronicTopologyEditorV1.require_subleg(topology, subleg_id)

        HydronicTopologyEditorV1._reject_heat_source_room(
            topology=topology,
            room_id=room_id,
        )

        subleg.route_room_ids[:] = [
            existing_room_id
            for existing_room_id in subleg.route_room_ids
            if existing_room_id != room_id
        ]

        subleg.route_room_ids.append(room_id)

        if set_index:
            subleg.index_room_id = room_id

        return topology

    @staticmethod
    def set_subleg_index_room(
        topology: HydronicTopologyV1,
        subleg_id: str,
        room_id: str,
        *,
        move_to_terminal: bool = False,
    ) -> HydronicTopologyV1:
        """
        Set a subleg's mutable selected/default index room.

        If move_to_terminal=True, the selected room is also moved to the
        terminal/end position of that subleg route.
        """

        if move_to_terminal:
            return HydronicTopologyEditorV1.move_room_to_subleg_terminal(
                topology=topology,
                subleg_id=subleg_id,
                room_id=room_id,
                set_index=True,
            )

        subleg = HydronicTopologyEditorV1.require_subleg(topology, subleg_id)
        room_id = str(room_id)

        HydronicTopologyEditorV1._reject_heat_source_room(
            topology=topology,
            room_id=room_id,
        )

        if room_id not in subleg.route_room_ids:
            raise ValueError(
                f"Cannot set index room {room_id!r}; "
                f"room is not in subleg {subleg_id!r}"
            )

        subleg.index_room_id = room_id
        return topology

    # ------------------------------------------------------------------
    # Internal guards
    # ------------------------------------------------------------------
    @staticmethod
    def _reject_heat_source_room(
        *,
        topology: HydronicTopologyV1,
        room_id: str,
    ) -> None:
        """
        Do not allow the heat-source enclosure to be silently inserted as a
        downstream route node.

        If the heat-source room has a real emitter/load later, it should be
        represented explicitly by the topology wizard, not inferred here.
        """

        if room_id == topology.heat_source_room_id:
            raise ValueError(
                "Heat-source room cannot be moved into a downstream "
                f"route by this editor: {room_id!r}"
            )