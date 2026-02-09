# ======================================================================
# HVAC/gui_v3/schematic/layout_dto.py
# ======================================================================

"""
HVACgooee — GUI v3
Hydronics Schematic Layout DTOs — Phase E

Pure layout metadata for schematic rendering.

RULES (LOCKED — Phase E)
-----------------------
• No physics
• No behaviour
• No ProjectState access
• GUI-only visual intent
• Read-only by convention
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple


# ----------------------------------------------------------------------
# Type aliases
# ----------------------------------------------------------------------

LayoutCoord = Tuple[float, float]


# ----------------------------------------------------------------------
# Layout semantics
# ----------------------------------------------------------------------

LayoutBand = Literal[
    "SUPPLY",
    "RETURN",
    "DISTRIBUTION",
    "TERMINAL",
    "AUX",
]

LayoutStrategy = Literal[
    "LINEAR",
    "TREE",
    "SPINE",
    "LOOP_AWARE",
]


# ----------------------------------------------------------------------
# Visual shape hint (GUI-only)
# ----------------------------------------------------------------------

NodeShape = Literal[
    "CIRCLE",     # default / generic
    "RECT",       # equipment block
    "OBLONG",     # boiler / plant (pipe-friendly)
    "TRIANGLE",   # pump / directional device
]


# ----------------------------------------------------------------------
# Node layout DTO
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NodeLayoutDTO:
    """
    Declarative layout metadata for a schematic node.

    No authority — visual hint only.
    """

    node_id: str

    # Absolute schematic position (Phase E = deterministic, not scaled)
    position: LayoutCoord

    # Semantic vertical band
    band: LayoutBand

    # Optional visual hints
    shape: NodeShape = "CIRCLE"
    fixed: bool = False          # if True, engine must not move node
    weight: float | None = None  # layout priority (higher = more stable)


# ----------------------------------------------------------------------
# Edge layout DTO
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EdgeLayoutDTO:
    """
    Declarative layout metadata for a schematic edge.
    """

    from_node_id: str
    to_node_id: str

    # Optional bend points (orthogonal routing)
    route: List[LayoutCoord] | None = None

    # Visual hint only (parallel pipes, offsets)
    offset_index: int = 0


# ----------------------------------------------------------------------
# Root layout DTO
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HydronicsLayoutDTO:
    """
    Complete schematic layout description.

    Produced by Phase E layout engine.
    Consumed by GUI renderer only.
    """

    strategy: LayoutStrategy

    node_layouts: Dict[str, NodeLayoutDTO]
    edge_layouts: List[EdgeLayoutDTO]

    # Optional debug / explanation
    notes: List[str] | None = None
