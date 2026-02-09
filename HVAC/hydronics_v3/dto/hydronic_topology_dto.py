# HVAC/hydronics_v3/dto/hydronic_topology_dto.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True, slots=True)
class HydronicTopologyDTO:
    """
    Declared hydronic topology (v3).

    Describes connectivity and intent only.
    No sizing, no pressure-drop, no balancing.
    """

    # All legs in the system (keyed by leg_id)
    legs: Dict[str, "HydronicLegDTO"]

    # Ordered paths (each path = list of leg_ids from source to terminal)
    paths: Dict[str, List[str]]

    # Optional declared source (boiler / plant)
    source_leg_id: Optional[str]

    # User-declared ordering (room / emitter intent order)
    declared_order: List[str]
