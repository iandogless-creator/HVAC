# ======================================================================
# HVAC/hydronics/dto/topology_snapshot_dto.py
# ======================================================================

"""
HVACgooee — Hydronics Topology Snapshot DTO

Authoritative, read-only structural snapshot of a hydronic system.

Purpose
-------
• Capture resolved topology ONLY
• No physics
• No sizing
• No calculations
• Safe for GUI consumption

This DTO is created once by the hydronics pipeline
and attached to ProjectState.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


# ----------------------------------------------------------------------
# Nodes
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TopologyNodeDTO:
    """
    Structural node in the hydronics network.

    Examples:
    - plant
    - pump
    - emitter
    - junction
    - sensor
    """
    id: str
    kind: str


# ----------------------------------------------------------------------
# Edges
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TopologyEdgeDTO:
    """
    Structural connection between two nodes.
    """
    from_node_id: str
    to_node_id: str

    # Optional semantic hints (still topology-only)
    direction: str | None = None      # "FLOW" | "RETURN" | None
    classification: str | None = None # "primary" | "secondary" | "branch"


# ----------------------------------------------------------------------
# Snapshot
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TopologySnapshotDTO:
    """
    Immutable snapshot of hydronic topology.

    This is the ONLY structure the GUI is allowed to see.
    """
    nodes: Tuple[TopologyNodeDTO, ...]
    edges: Tuple[TopologyEdgeDTO, ...]
