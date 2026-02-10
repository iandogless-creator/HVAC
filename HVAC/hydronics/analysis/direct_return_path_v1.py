# ======================================================================
# HVAC/hydronics/analysis/direct_return_path_v1.py
# ======================================================================

"""
HVACgooee — Direct Return Path Generator (v1)
--------------------------------------------

Generates direct-return hydronic paths using topology only.

This module:
• Does NOT calculate pressure loss
• Does NOT size pipes
• Does NOT balance flows
• Does NOT mutate project state

Direct-return principle:
    Supply paths and return paths follow the SAME order
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from HVAC.hydronics.committed.committed_hydronic_leg import (
    CommittedHydronicLeg,
)

# ----------------------------------------------------------------------
# DTOs
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DirectReturnResultV1:
    """
    Result container for direct return path generation.
    """
    paths: Dict[str, List[str]]


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def build_direct_return_paths_v1(
    *,
    committed_legs: List[CommittedHydronicLeg],
    source_leg_id: str,
) -> DirectReturnResultV1:
    """
    Build direct-return paths.

    PARAMETERS
    ----------
    committed_legs:
        Authoritative committed legs (tree topology already resolved).

    source_leg_id:
        Leg ID of the system source (boiler / header).

    RETURNS
    -------
    DirectReturnResultV1
        paths:
            path_id → ordered list of leg_ids
    """

    # --------------------------------------------------------------
    # Index topology
    # --------------------------------------------------------------
    parent_by_leg: Dict[str, str | None] = {}
    children_by_leg: Dict[str, List[str]] = {}

    for leg in committed_legs:
        parent_by_leg[leg.leg_id] = leg.parent_leg_id
        children_by_leg.setdefault(leg.leg_id, [])

    for leg in committed_legs:
        if leg.parent_leg_id is not None:
            children_by_leg.setdefault(leg.parent_leg_id, []).append(leg.leg_id)

    # --------------------------------------------------------------
    # Identify terminal legs
    # --------------------------------------------------------------
    terminal_legs = [
        leg.leg_id
        for leg in committed_legs
        if not children_by_leg.get(leg.leg_id)
    ]

    if not terminal_legs:
        raise RuntimeError("[DR] No terminal legs found.")

    # --------------------------------------------------------------
    # Build supply paths
    # --------------------------------------------------------------
    def build_path_to_source(leg_id: str) -> List[str]:
        path = [leg_id]
        current = leg_id
        while current != source_leg_id:
            parent = parent_by_leg.get(current)
            if parent is None:
                raise RuntimeError(
                    f"[DR] Leg '{leg_id}' does not connect to source '{source_leg_id}'."
                )
            path.append(parent)
            current = parent
        return list(reversed(path))

    supply_paths: Dict[str, List[str]] = {
        leg_id: build_path_to_source(leg_id)
        for leg_id in terminal_legs
    }

    # --------------------------------------------------------------
    # Order terminals by depth (nearest → furthest)
    # --------------------------------------------------------------
    def depth(leg_id: str) -> int:
        d = 0
        current = leg_id
        while current != source_leg_id:
            parent = parent_by_leg.get(current)
            if parent is None:
                break
            d += 1
            current = parent
        return d

    terminals_sorted = sorted(terminal_legs, key=depth)

    # --------------------------------------------------------------
    # Build direct-return paths
    # --------------------------------------------------------------
    paths: Dict[str, List[str]] = {}

    for idx, leg_id in enumerate(terminals_sorted):
        supply_path = supply_paths[leg_id]
        return_path = supply_path  # SAME order (direct return)

        full_path = supply_path + list(reversed(return_path[1:]))

        path_id = f"DR_PATH_{idx + 1}"
        paths[path_id] = full_path

    return DirectReturnResultV1(paths=paths)


# ======================================================================
# END MODULE
# ======================================================================
