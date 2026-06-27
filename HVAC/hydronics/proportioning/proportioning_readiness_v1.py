# ======================================================================
# HVAC/hydronics/proportioning/proportioning_readiness_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    resolve_system_return_arrangement_v1,
)


@dataclass(frozen=True, slots=True)
class ProportioningReadinessV1:
    """
    Read-only Proportioning readiness projection.

    Authority
    ---------
    • Reads ProjectState only
    • No topology mutation
    • No pipe sizing
    • No pressure-drop calculation
    • No balancing
    """

    index_room_id: str | None
    index_room_label: str
    terminal_room_id: str | None
    terminal_room_label: str
    terminal_alignment_status: str
    basis_mode: str
    total_index_length_label: str
    nominal_gradient_label: str
    return_arrangement_basis_label: str
    return_arrangement_basis_ready: bool
    return_arrangement_basis_status: str
    proportioning_status: str


def build_proportioning_readiness_v1(project_state: Any) -> ProportioningReadinessV1:
    """
    Build read-only status for the Proportioning tab.

    This states what Proportioning has received from Basic Hydronics.
    It does not run Proportioning.
    """
    intent = getattr(project_state, "basic_hydronic_sizing_intent", None)
    topology = getattr(project_state, "hydronic_topology", None)

    index_room_id = getattr(intent, "index_room_id", None) if intent else None
    basis_mode = str(getattr(intent, "basis_mode", "") or "—") if intent else "—"

    total_index_length = (
        getattr(intent, "total_index_length_m", None)
        if intent is not None
        else None
    )
    nominal_gradient = (
        getattr(intent, "nominal_pressure_gradient_Pa_per_m", None)
        if intent is not None
        else None
    )

    terminal_room_id = _terminal_room_id(topology)

    return_intent = getattr(
        project_state,
        "hydronic_return_arrangement_intent",
        None,
    )
    resolved_return_basis = resolve_system_return_arrangement_v1(
        return_intent
    )

    return_basis_label = str(
        getattr(
            resolved_return_basis,
            "resolved_arrangement",
            "UNDECIDED",
        )
        or "UNDECIDED"
    )
    return_basis_ready = bool(
        getattr(
            resolved_return_basis,
            "accepted",
            False,
        )
    )
    return_basis_status = str(
        getattr(
            resolved_return_basis,
            "status",
            "System return arrangement undecided",
        )
        or "System return arrangement undecided"
    )

    index_label = _room_label(project_state, index_room_id)
    terminal_label = _room_label(project_state, terminal_room_id)

    if not index_room_id:
        alignment = "Missing — no Basic index room selected"
    elif not terminal_room_id:
        alignment = "Unknown — no terminal room resolved"
    elif str(index_room_id) == str(terminal_room_id):
        alignment = "OK — index room is terminal"
    else:
        alignment = "Mismatch — index room is not terminal"

    blockers: list[str] = []

    if not return_basis_ready:
        blockers.append("Accepted return arrangement basis required")

    if blockers:
        proportioning_status = "Blocked — " + "; ".join(blockers)
    else:
        proportioning_status = (
            "Read-only preview only — accepted return arrangement basis "
            "available; detailed balancing has not been run"
        )

    return ProportioningReadinessV1(
        index_room_id=str(index_room_id) if index_room_id else None,
        index_room_label=index_label,
        terminal_room_id=str(terminal_room_id) if terminal_room_id else None,
        terminal_room_label=terminal_label,
        terminal_alignment_status=alignment,
        basis_mode=basis_mode,
        total_index_length_label=_length_label(total_index_length),
        nominal_gradient_label=_gradient_label(nominal_gradient),
        return_arrangement_basis_label=return_basis_label,
        return_arrangement_basis_ready=return_basis_ready,
        return_arrangement_basis_status=return_basis_status,
        proportioning_status=proportioning_status,
    )


def _terminal_room_id(topology: Any) -> str | None:
    if topology is None:
        return None

    legs = getattr(topology, "legs", None) or {}

    try:
        leg = legs.get("leg-001")
    except AttributeError:
        leg = None

    if leg is None and isinstance(legs, (list, tuple)) and legs:
        leg = legs[0]

    if leg is None:
        return None

    # Prefer explicit terminal if your topology DTO has one.
    for attr in (
        "terminal_room_id",
        "terminal_index_room_id",
        "index_room_id",
    ):
        value = getattr(leg, attr, None)
        if value:
            return str(value)

    # Fallback: infer last room from common simple route collections.
    for attr in ("room_ids", "route_room_ids", "ordered_room_ids"):
        values = getattr(leg, attr, None)
        if values:
            return str(list(values)[-1])

    return None


def _room_label(project_state: Any, room_id: str | None) -> str:
    if not room_id:
        return "—"

    rooms = getattr(project_state, "rooms", None) or {}
    room = rooms.get(str(room_id)) if hasattr(rooms, "get") else None

    for attr in ("display_name", "name", "label"):
        value = getattr(room, attr, None)
        if value:
            return str(value)

    return str(room_id)


def _length_label(value: Any) -> str:
    try:
        if value is None:
            return "Not set"
        return f"{float(value):.2f} m"
    except (TypeError, ValueError):
        return "Not set"


def _gradient_label(value: Any) -> str:
    try:
        if value is None:
            return "Not set"
        return f"{float(value):.1f} Δp/m"
    except (TypeError, ValueError):
        return "Not set"