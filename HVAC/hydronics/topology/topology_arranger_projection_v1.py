# ======================================================================
# HVAC/hydronics/topology/topology_arranger_projection_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.topology.hydronic_topology_editor_v1 import (
    HydronicTopologyEditorV1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicTopologyV1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_for_leg_id,
)

# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class TopologyArrangerRowV1:
    """
    Read-only row for the future Topology Arranger panel.

    Display/projection only.
    """

    room_id: str
    label: str
    order: int
    is_index: bool = False
    is_terminal: bool = False


@dataclass(frozen=True, slots=True)
class TopologyArrangerProjectionV1:
    """
    Read-only route projection for the future Topology Arranger panel.
    """

    leg_id: str
    leg_label: str
    heat_source_room_id: str
    rows: tuple[TopologyArrangerRowV1, ...]
    selected_index_room_id: str | None = None


# ======================================================================
# Public builder
# ======================================================================

def build_topology_arranger_projection_v1(
    project_state: Any,
    *,
    leg_id: str = "leg-001",
) -> TopologyArrangerProjectionV1:
    """
    Build a read-only row projection for the future Topology Arranger.

    Authority
    ---------
    Reads:
    - ProjectState.hydronic_topology
    - ProjectState.rooms

    Does not:
    - mutate ProjectState
    - size pipes
    - calculate pressure loss
    - create emitters
    - modify room identity
    """

    topology = getattr(project_state, "hydronic_topology", None)

    if topology is None:
        raise ValueError("ProjectState has no hydronic_topology")

    if not isinstance(topology, HydronicTopologyV1):
        raise TypeError("ProjectState.hydronic_topology is not HydronicTopologyV1")

    leg = HydronicTopologyEditorV1.require_leg(topology, leg_id)
    primary_subleg = primary_subleg_for_leg_id(topology, leg_id)
    rooms = getattr(project_state, "rooms", {}) or {}

    rows = _build_subleg_rows(
        subleg=primary_subleg,
        rooms=rooms,
    )

    return TopologyArrangerProjectionV1(
        leg_id=leg.leg_id,
        leg_label=leg.label,
        heat_source_room_id=topology.heat_source_room_id,
        rows=tuple(rows),
        selected_index_room_id=primary_subleg.index_room_id,
    )


# ======================================================================
# Internals
# ======================================================================

def _build_subleg_rows(
    *,
    subleg: Any,
    rooms: dict[str, Any],
) -> list[TopologyArrangerRowV1]:
    rows: list[TopologyArrangerRowV1] = []
    terminal_room_id = (
        subleg.route_room_ids[-1]
        if subleg.route_room_ids
        else None
    )

    for order, room_id in enumerate(subleg.route_room_ids, start=1):
        room_id = str(room_id)
        room = rooms.get(room_id)

        rows.append(
            TopologyArrangerRowV1(
                room_id=room_id,
                label=_room_label(room=room, room_id=room_id),
                order=order,
                is_index=(room_id == subleg.index_room_id),
                is_terminal=(room_id == terminal_room_id),
            )
        )

    return rows


def _room_label(*, room: Any, room_id: str) -> str:
    raw_label = getattr(room, "name", None) if room is not None else None
    label = str(raw_label or room_id).strip()

    return label
