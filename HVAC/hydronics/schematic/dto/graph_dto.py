# HVAC/hydronics/schematic/dto/graph_dto.py

from dataclasses import dataclass
from typing import Tuple

from .node_dto import HydronicNodeDTO
from .connector_dto import HydronicConnectorDTO

@dataclass(frozen=True, slots=True)
class HydronicSchematicGraphDTO:
    """
    Phase A — Schematic Graph DTO (CANONICAL)

    Topology + immutable data.
    """
    nodes: Tuple[HydronicNodeDTO, ...]
    connectors: Tuple[HydronicConnectorDTO, ...]
