# HVAC/hydronics/schematic/dto/connector_dto.py

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True, slots=True)
class HydronicConnectorDTO:
    """
    Phase A — Connector DTO (CANONICAL)

    Represents hydraulic reality.
    """
    id: str
    from_node: str
    to_node: str

    # Optional precomputed data
    flow_kg_s: Optional[float] = None
    dp_pa: Optional[float] = None
