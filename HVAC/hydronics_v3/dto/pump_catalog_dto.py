# ======================================================================
# HVAC/hydronics_v3/dto/pump_catalog_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class PumpCurvePointDTO:
    """
    One point on a pump curve.

    flow_m3_h: flow rate in m³/h
    head_m:    head in metres of water column (mH2O)
    """
    flow_m3_h: float
    head_m: float


@dataclass(frozen=True, slots=True)
class PumpCandidateDTO:
    """
    A selectable pump option.

    curve_points must be sorted by flow_m3_h (engine will validate).
    """
    pump_ref: str
    curve_points: List[PumpCurvePointDTO]

    # Optional metadata (not used for selection in v1 unless provided)
    note: str = ""
    max_flow_m3_h: Optional[float] = None
    max_head_m: Optional[float] = None


@dataclass(frozen=True, slots=True)
class PumpCatalogDTO:
    """
    Declarative pump library.
    """
    catalog_id: str
    pumps: List[PumpCandidateDTO]
