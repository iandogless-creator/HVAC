from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


# ------------------------------------------------------------
# Node Hover Payload
# ------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NodeHoverDTO:
    """
    Read-only hover payload for a schematic node.

    All values are precomputed and observational.
    """
    title: str

    # Thermal intent
    qf_w: Optional[float]        # Room heat demand
    qt_w: Optional[float]        # Supplied heat

    # Hydraulic intent
    flow_kg_s: Optional[float]
    target_cv: Optional[float]


# ------------------------------------------------------------
# Edge Hover Payload
# ------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EdgeHoverDTO:
    """
    Read-only hover payload for a schematic edge (pipe).
    """
    pipe_ref: str

    size_mm: Optional[float]
    length_m: Optional[float]
    material: Optional[str]

    flow_kg_s: Optional[float]
    velocity_m_s: Optional[float]
    dp_pa: Optional[float]
