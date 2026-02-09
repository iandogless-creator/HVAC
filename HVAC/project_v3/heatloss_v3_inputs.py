"""
heatloss_v3_inputs.py
---------------------

HVACgooee — v3 → v2 Heat-Loss Input Adapters

Purpose:
    Translate v3 assembled project data into
    the minimal inputs required by Heat-Loss v2.

NO physics.
NO calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class HL_SurfaceInput:
    surface_id: str
    surface_class: str          # external_wall, window, roof, etc.
    area_m2: float
    u_value_W_m2K: float
    orientation: Optional[str] = None


@dataclass(frozen=True)
class HL_SpaceInput:
    space_id: str
    name: str
    design_temp_C: float
    volume_m3: Optional[float]
    surfaces: List[HL_SurfaceInput]
