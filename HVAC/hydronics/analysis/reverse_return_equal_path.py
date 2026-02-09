# ======================================================================
# HVAC/hydronics/analysis/reverse_return_equal_path_v1.py
# ======================================================================

"""
HVACgooee — Reverse Return Equal Path Generator (v1)
----------------------------------------------------

Generates reverse-return hydronic paths using topology only.

This module:
• Does NOT calculate pressure loss
• Does NOT size pipes
• Does NOT balance flows
• Does NOT mutate project state

It produces deterministic path definitions suitable for:
    • ΔP aggregation
    • Pump duty estimation
    • Reporting / inspection

Reverse-return principle:
    Supply paths are ordered nearest → furthest
    Return paths are ordered furthest → nearest
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from HVAC_legacy.hydronics.committed.committed_hydronic_leg import (
    CommittedHydronicLeg,
)

# ----------------------------------------------------------------------
# DTOs
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ReverseReturnResultV1:
    """
    Result container for reverse return path generation.
    """
    paths: Dict[str, List[str]]


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def build_reverse_return_equal_paths_v1(
    *,
    committed_legs: List[CommittedHydronicLeg],
    source_leg_id: str,
) -> ReverseReturnResultV1:
    """
    Build reverse-return equal-length paths.

    PARAMETERS
    ----------
    committed_legs:
        Authoritative committed legs (tree topology already resolved).

    source_leg_id:
        Leg ID of the system source (boiler / header).

    RETURNS
    -------
    ReverseReturnResultV1
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
    # Identify terminal legs (no children)
    # --------------------------------------------------------------
    terminal_legs = [
        leg.leg_id
        for leg in committed_legs
        if not children_by_leg.get(leg.leg_id)
    ]

    if not terminal_legs:
        raise RuntimeError("[RR] No terminal legs found.")

    # --------------------------------------------------------------
    # Build supply paths (source → terminal)
    # --------------------------------------------------------------
    def build_path_to_source(leg_id: str) -> List[str]:
        path = [leg_id]
        current = leg_id
        while current != source_leg_id:
            parent = parent_by_leg.get(current)
            if parent is None:
                raise RuntimeError(
                    f"[RR] Leg '{leg_id}' does not connect to source '{source_leg_id}'."
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
    terminals_reverse = list(reversed(terminals_sorted))

    # --------------------------------------------------------------
    # Build reverse-return paths
    # --------------------------------------------------------------
    paths: Dict[str, List[str]] = {}

    for idx, supply_leg in enumerate(terminals_sorted):
        return_leg = terminals_reverse[idx]

        supply_path = supply_paths[supply_leg]
        return_path = supply_paths[return_leg]

        # Reverse return path and remove duplicate source
        full_path = supply_path + list(reversed(return_path[1:]))

        path_id = f"RR_PATH_{idx + 1}"

        paths[path_id] = full_path

    return ReverseReturnResultV1(paths=paths)


# ======================================================================
# END MODULE
# ======================================================================
