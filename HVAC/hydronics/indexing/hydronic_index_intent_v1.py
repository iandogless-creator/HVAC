# ======================================================================
# HVAC/hydronics/indexing/hydronic_index_intent_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.topology.hydronic_topology_editor_v1 import (
    HydronicTopologyEditorV1,
)


# ======================================================================
# DTO
# ======================================================================

@dataclass(frozen=True, slots=True)
class HydronicIndexIntentResultV1:
    """
    Result of applying hydronic index intent.

    Display/status only.
    """

    index_room_id: str
    index_emitter_id: str | None
    has_emitter: bool
    status: str


# ======================================================================
# Public API
# ======================================================================

def set_hydronic_index_room_v1(
    project_state: Any,
    room_id: str,
    *,
    leg_id: str = "leg-001",
    move_to_terminal: bool = False,
) -> HydronicIndexIntentResultV1:
    """
    Canonical helper for setting the hydronic index room.

    Authority
    ---------
    Updates:
    - ProjectState.basic_hydronic_sizing_intent.index_room_id
    - ProjectState.basic_hydronic_sizing_intent.index_emitter_id
    - HydronicTopologyV1 leg.index_room_id, when topology exists

    Optional:
    - move selected room to terminal route position

    Explicitly forbidden
    --------------------
    - no pipe sizing
    - no pressure-drop calculation
    - no proportioning calculation
    - no heat-loss calculation
    - no room_id mutation
    """

    if project_state is None:
        raise ValueError("project_state is required")

    room_id = str(room_id or "").strip()

    if not room_id:
        raise ValueError("room_id is required")

    _ensure_basic_hydronic_sizing_intent(project_state)

    intent = project_state.basic_hydronic_sizing_intent

    topology = getattr(project_state, "hydronic_topology", None)

    if topology is not None:
        if move_to_terminal:
            HydronicTopologyEditorV1.move_room_to_leg_terminal(
                topology=topology,
                leg_id=leg_id,
                room_id=room_id,
                set_index=True,
            )
        else:
            HydronicTopologyEditorV1.set_leg_index_room(
                topology=topology,
                leg_id=leg_id,
                room_id=room_id,
                move_to_terminal=False,
            )

    emitter_id = _first_emitter_id_for_room(
        project_state=project_state,
        room_id=room_id,
    )

    intent.index_room_id = room_id
    intent.index_emitter_id = emitter_id

    if emitter_id:
        status = "Index room and index emitter updated"
        has_emitter = True
    else:
        status = "Index room updated; selected room has no emitter assigned"
        has_emitter = False

    return HydronicIndexIntentResultV1(
        index_room_id=room_id,
        index_emitter_id=emitter_id,
        has_emitter=has_emitter,
        status=status,
    )


def apply_basic_hydronic_sizing_payload_v1(
    project_state: Any,
    payload: dict,
    *,
    leg_id: str = "leg-001",
    update_topology_index: bool = True,
    move_to_terminal: bool = False,
) -> HydronicIndexIntentResultV1 | None:
    """
    Apply Basic Hydronics panel payload through the same index-intent path.

    This keeps Basic Hydronics and Topology Arranger from drifting apart.

    The payload remains the authority for sizing assumptions:
    - basis mode
    - index length
    - nominal pressure gradient
    - source fields
    - notes

    The shared index helper remains the authority for keeping:
    - index_room_id
    - index_emitter_id
    - topology leg.index_room_id

    aligned.
    """

    if project_state is None:
        raise ValueError("project_state is required")

    payload = payload or {}

    _ensure_basic_hydronic_sizing_intent(project_state)
    intent = project_state.basic_hydronic_sizing_intent

    intent.basis_mode = str(payload.get("basis_mode") or "INDEX_LENGTH")
    intent.total_index_length_m = payload.get("total_index_length_m")
    intent.nominal_pressure_gradient_Pa_per_m = payload.get(
        "nominal_pressure_gradient_Pa_per_m"
    )
    intent.length_source = str(payload.get("length_source") or "unset")
    intent.pressure_gradient_source = str(
        payload.get("pressure_gradient_source") or "unset"
    )
    intent.notes = str(payload.get("notes") or "")

    room_id = payload.get("index_room_id")

    if not room_id:
        intent.index_room_id = None
        intent.index_emitter_id = payload.get("index_emitter_id")
        return None

    if update_topology_index:
        return set_hydronic_index_room_v1(
            project_state,
            str(room_id),
            leg_id=leg_id,
            move_to_terminal=move_to_terminal,
        )

    emitter_id = payload.get("index_emitter_id") or _first_emitter_id_for_room(
        project_state=project_state,
        room_id=str(room_id),
    )

    intent.index_room_id = str(room_id)
    intent.index_emitter_id = emitter_id

    return HydronicIndexIntentResultV1(
        index_room_id=str(room_id),
        index_emitter_id=emitter_id,
        has_emitter=bool(emitter_id),
        status=(
            "Index room and index emitter updated"
            if emitter_id
            else "Index room updated; selected room has no emitter assigned"
        ),
    )


# ======================================================================
# Internals
# ======================================================================

def _ensure_basic_hydronic_sizing_intent(project_state: Any) -> None:
    if getattr(project_state, "basic_hydronic_sizing_intent", None) is not None:
        return

    project_state.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1()


def _first_emitter_id_for_room(
    *,
    project_state: Any,
    room_id: str,
) -> str | None:
    """
    Return the first emitter id assigned to room_id, if any.

    Keeps the selected index emitter aligned with the selected index room.
    """

    emitters = getattr(project_state, "emitters", {}) or {}

    for emitter_id, emitter in emitters.items():
        emitter_room_id = getattr(emitter, "room_id", None)

        if emitter_room_id == room_id:
            return str(emitter_id)

    return None