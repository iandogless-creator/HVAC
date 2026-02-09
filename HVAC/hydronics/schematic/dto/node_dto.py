# HVAC/hydronics/schematic/dto/node_dto.py

from dataclasses import dataclass
from typing import Literal, Optional

NodeKind = Literal[
    "room",
    "emitter",
    "manifold",
    "junction",
    "plant",
]

@dataclass(frozen=True, slots=True)
class HydronicNodeDTO:
    """
    Phase A — Node DTO (CANONICAL)

    Represents thermal intent.
    No geometry, no authority.
    """
    id: str
    kind: NodeKind
    label: str

    # Optional precomputed values (read-only, may be None)
    heat_demand_w: Optional[float] = None
    design_flow_kg_s: Optional[float] = None
