# ======================================================================
# HVAC/hydronics_v3/dto/valve_catalog_dto.py
# ======================================================================

"""
HVACgooee — Valve Catalog DTO (v1)

Purpose
-------
Declarative list of available valve Kv options.

No manufacturer logic.
No inference.
No mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class ValveKvOptionDTO:
    """
    Single selectable valve option.
    """

    valve_ref: str
    kv_m3_h: float
    note: str = ""


@dataclass(frozen=True, slots=True)
class ValveCatalogDTO:
    """
    Valve catalog available to the sizing engine.
    """

    catalog_id: str
    kv_options: List[ValveKvOptionDTO]
