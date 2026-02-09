# ======================================================================
# HVAC/hydronics/models/hydronic_skeleton_generator_v1.py
# ======================================================================
"""
HVACgooee — Hydronic Skeleton Generator v1
-----------------------------------------

Creates the minimal "System Design starts now" hydronic scaffold:

• One boiler node
• One terminal per room
• One supply leg per terminal (boiler -> terminal)
• One return leg per terminal (terminal -> boiler)

NO sizing.
NO flow calculation.
NO pressure drop.
NO fittings.
NO topology choice (direct/reverse return comes later).

Inputs
------
Authoritative room heat-loss results (frozen upstream truth):
    Iterable of rooms with:
        - room_id (stable key)
        - room_name
        - design_heat_loss_w

Outputs
-------
HydronicSkeletonV1
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from HVAC_legacy.hydronics.models.hydronic_skeleton_v1 import (
    HydronicSkeletonV1,
    BoilerNodeV1,
    TerminalNodeV1,
)

# ----------------------------------------------------------------------
# Public DTO for generator input (keeps generator decoupled from HL internals)
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RoomLoadV1:
    room_id: str
    room_name: str
    design_heat_loss_w: float

# ----------------------------------------------------------------------
# Internal deterministic ID helpers
# ----------------------------------------------------------------------

def _safe_token(s: str) -> str:
    """
    Make a stable, filename-ish token.

    Not for security. Just stable IDs.
    """
    s = s.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", ".", "/"):
            out.append("_")
        # else drop punctuation
    token = "".join(out)
    while "__" in token:
        token = token.replace("__", "_")
    return token.strip("_") or "x"


def _boiler_id() -> str:
    return "boiler_1"


def _terminal_id(room: RoomLoadV1, index_1: int) -> str:
    return f"term_{index_1:03d}_{_safe_token(room.room_id)}"


def _leg_id(kind: str, terminal_id: str) -> str:
    # kind: "S" (supply) or "R" (return)
    return f"leg_{kind}_{terminal_id}"


# ----------------------------------------------------------------------
# Generator
# ----------------------------------------------------------------------

def generate_initial_hydronic_skeleton_v1(
    rooms: Iterable[RoomLoadV1],
    *,
    skeleton_id: str = "skeleton_1",
    boiler_name: str = "Boiler / Heat Source",
) -> HydronicSkeletonV1:
    """
    Build the minimal hydronic skeleton.

    Determinism:
      The skeleton will be stable if the incoming rooms are provided
      in stable order. (Caller should sort by room_name or room_id.)
    """

    boiler = BoilerNodeV1(boiler_id=_boiler_id(), name=boiler_name)
    skel = HydronicSkeletonV1(skeleton_id=skeleton_id, boiler=boiler)

    # Ensure we iterate only once and keep ordering stable
    room_list: List[RoomLoadV1] = list(rooms)

    for i, room in enumerate(room_list, start=1):
        term_id = _terminal_id(room, i)

        terminal = TerminalNodeV1(
            terminal_id=term_id,
            room_id=room.room_id,
            room_name=room.room_name,
            design_heat_loss_w=float(room.design_heat_loss_w),
        )
        skel.add_terminal(terminal)

        # Supply: boiler -> terminal
        supply_leg = HydronicLegV1(
            leg_id=_leg_id("S", term_id),
            from_node_id=boiler.boiler_id,
            to_node_id=term_id,
            length_m=None,
            notes="Auto skeleton v1 (supply)",
        )
        skel.add_leg(supply_leg)

        # Return: terminal -> boiler
        return_leg = HydronicLegV1(
            leg_id=_leg_id("R", term_id),
            from_node_id=term_id,
            to_node_id=boiler.boiler_id,
            length_m=None,
            notes="Auto skeleton v1 (return)",
        )
        skel.add_leg(return_leg)

    return skel


# ----------------------------------------------------------------------
# Convenience: derive RoomLoadV1 from common heat-loss result shapes
# ----------------------------------------------------------------------

def extract_room_loads_from_project_state_v1(project_state: object) -> List[RoomLoadV1]:
    """
    Best-effort extractor so the generator can be used immediately.

    This function uses "duck typing" to avoid importing heat-loss engines/DTOs.

    Supported patterns (any one is sufficient):
      A) project_state.heatloss_room_results: Dict[room_id] -> object with (name, heat_loss_w)
      B) project_state.heatloss_rooms: List[object] with (room_id, name, heat_loss_w)
      C) project_state.heatloss_results.rooms: List[object] with (id/name/heat_loss_w variants)
      D) project_state.heatloss_results_dto.rooms: List[object] with (room_name, room_id, total_w variants)

    If nothing matches, returns [].
    Caller should treat [] as "no system intent can be generated yet".
    """

    rooms: List[RoomLoadV1] = []

    # A) Dict form
    d = getattr(project_state, "heatloss_room_results", None)
    if isinstance(d, dict) and d:
        for rid, robj in d.items():
            name = getattr(robj, "name", None) or getattr(robj, "room_name", None) or str(rid)
            hl_w = (
                getattr(robj, "heat_loss_w", None)
                or getattr(robj, "room_heat_loss_w", None)
                or getattr(robj, "total_heat_loss_w", None)
            )
            if hl_w is not None:
                rooms.append(RoomLoadV1(room_id=str(rid), room_name=str(name), design_heat_loss_w=float(hl_w)))
        return _stable_sort_rooms(rooms)

    # B) List form
    lst = getattr(project_state, "heatloss_rooms", None)
    if isinstance(lst, list) and lst:
        for robj in lst:
            rid = getattr(robj, "room_id", None) or getattr(robj, "id", None) or getattr(robj, "name", None)
            name = getattr(robj, "name", None) or getattr(robj, "room_name", None) or str(rid)
            hl_w = (
                getattr(robj, "heat_loss_w", None)
                or getattr(robj, "room_heat_loss_w", None)
                or getattr(robj, "total_heat_loss_w", None)
            )
            if rid is not None and hl_w is not None:
                rooms.append(RoomLoadV1(room_id=str(rid), room_name=str(name), design_heat_loss_w=float(hl_w)))
        return _stable_sort_rooms(rooms)

    # C/D) Nested results object
    results = getattr(project_state, "heatloss_results", None) or getattr(project_state, "heatloss_results_dto", None)
    if results is not None:
        rlist = getattr(results, "rooms", None) or getattr(results, "room_results", None)
        if isinstance(rlist, list) and rlist:
            for robj in rlist:
                rid = getattr(robj, "room_id", None) or getattr(robj, "id", None) or getattr(robj, "name", None)
                name = getattr(robj, "room_name", None) or getattr(robj, "name", None) or str(rid)
                hl_w = (
                    getattr(robj, "heat_loss_w", None)
                    or getattr(robj, "room_heat_loss_w", None)
                    or getattr(robj, "total_heat_loss_w", None)
                    or getattr(robj, "total_w", None)
                )
                if rid is not None and hl_w is not None:
                    rooms.append(RoomLoadV1(room_id=str(rid), room_name=str(name), design_heat_loss_w=float(hl_w)))
            return _stable_sort_rooms(rooms)

    return []


def _stable_sort_rooms(rooms: List[RoomLoadV1]) -> List[RoomLoadV1]:
    # Sort by name then id so generation order is stable and friendly.
    return sorted(rooms, key=lambda r: (r.room_name.lower(), r.room_id.lower()))
