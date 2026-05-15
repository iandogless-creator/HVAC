# ======================================================================
# HVAC/core/room_identity.py
# ======================================================================

from __future__ import annotations


# ======================================================================
# Storey defaults
# ======================================================================

DEFAULT_STOREYS: tuple[tuple[str, int], ...] = (
    ("Sub-Basement", -2),
    ("Basement", -1),
    ("Ground Floor", 0),
    ("First Floor", 1),
    ("Second Floor", 2),
)


# ======================================================================
# Human-facing room identity helpers
# ======================================================================

def room_ref_from_room_id(room_id: str) -> str:
    """
    Derive a compact fallback room reference from a stable room_id.

    Example:
        room-001 -> R1
        room-007 -> R7

    Display fallback only.
    Not engineering authority.
    """
    suffix = str(room_id).split("-")[-1]

    try:
        return f"R{int(suffix)}"
    except (TypeError, ValueError):
        return str(room_id)


def room_display_label(
    room_id: str,
    room: object,
    *,
    include_storey: bool = True,
) -> str:
    """
    Human-facing room label for GUI panels and reports.

    IDs remain internal authority.
    This helper is display-only and must not be used for calculations.
    """
    room_ref = getattr(room, "room_ref", None) or room_ref_from_room_id(room_id)
    name = getattr(room, "name", None) or room_id
    storey_label = getattr(room, "storey_label", None)

    base = f"{room_ref} {name}"

    if include_storey and storey_label:
        return f"{base} — {storey_label}"

    return base


def room_short_label(room_id: str, room: object) -> str:
    """
    Compact human-facing room label for tight UI spaces.
    """
    return room_display_label(
        room_id,
        room,
        include_storey=False,
    )