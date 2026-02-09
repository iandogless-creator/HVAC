# ======================================================================
# HVAC/hydronics_v3/dto/index_path_result_dto.py
# ======================================================================

"""
HVACgooee — Index Path Result DTO (v1)

Purpose
-------
Authoritative result of index-path discovery after pressure-drop
estimation.

This DTO answers ONE question only:

    "Which hydronic path governs the system, and why?"

It is consumed by:
• BalancingTargetEngineV1
• Valve sizing engines
• Valve authority engines
• Reporting layers

It does NOT:
• infer topology
• recalculate pressure drop
• mutate hydronic objects
• import GUI / Qt / ProjectState
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


# ----------------------------------------------------------------------
# Index path leg row (ordered, declarative)
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class IndexPathLegDTO:
    """
    One leg participating in the discovered index path.

    Notes
    -----
    • order defines traversal from boiler → terminal
    • leg_id is a LABEL only
    • dp_pa is the aggregated Δp contribution of this leg
    """

    order: int
    leg_id: str
    dp_pa: float


# ----------------------------------------------------------------------
# IndexPathResultDTO (top-level authoritative result)
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class IndexPathResultDTO:
    """
    Canonical output of index-path discovery.

    LOCKED RULES
    ------------
    • DTO-only (no behaviour)
    • Read-only once created
    • Engines may consume, never mutate
    • Ordering is explicit and authoritative
    • IDs are labels, not structure

    Meaning
    -------
    The index path is the *worst-case* hydraulic path through the system
    after pressure-drop aggregation.

    Single-leg systems are valid and produce a one-row index path.
    """

    system_id: str

    # Terminal leg at the end of the governing path.
    index_leg_id: str

    # Ordered legs forming the path (boiler → terminal).
    path_legs: List[IndexPathLegDTO]

    # Total Δp of the path (Pa).
    total_dp_pa: float

    # ADD THIS FIELD (non-breaking for meaning)
    terminal_leg_ids: List[str]

    # Optional explanation for diagnostics / reporting.
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.path_legs:
            raise ValueError("Index path must contain at least one leg")

        # Validate ordering
        orders = [l.order for l in self.path_legs]
        if sorted(orders) != list(range(len(self.path_legs))):
            raise ValueError("IndexPathLegDTO.order must be contiguous starting at 0")

        # Validate Δp
        if self.total_dp_pa < 0:
            raise ValueError("total_dp_pa must be >= 0")

        sum_dp = sum(l.dp_pa for l in self.path_legs)
        if abs(sum_dp - self.total_dp_pa) > 1e-6:
            raise ValueError(
                "total_dp_pa must equal sum of path_legs dp_pa values"
            )

        for leg in self.path_legs:
            if leg.dp_pa < 0:
                raise ValueError("leg dp_pa must be >= 0")
