from __future__ import annotations
from dataclasses import dataclass


# ------------------------------------------------------------------
# Node hover payload
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NodeHoverDTO:
    """
    Read-only hover payload for a schematic node.

    Phase D:
    - Observational only
    - No computation
    """

    title: str

    # Thermal intent
    qf_w: float | None          # Design heat demand
    qt_w: float | None          # Supplied heat

    # Hydraulic intent
    flow_kg_s: float | None
    target_cv: float | None


# ------------------------------------------------------------------
# Edge hover payload
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EdgeHoverDTO:
    """
    Read-only hover payload for a schematic edge (pipe).
    """

    pipe_ref: str

    size_mm: float | None
    length_m: float | None
    material: str | None

    flow_kg_s: float | None
    velocity_m_s: float | None
    dp_pa: float | None
