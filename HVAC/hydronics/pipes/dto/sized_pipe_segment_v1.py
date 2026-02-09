# ======================================================================
# HVAC/hydronics/pipes/dto/sized_pipe_segment_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SizedPipeSegmentV1:
    """
    Authoritative pipe sizing result for a single hydronic segment.
    """

    segment_id: str
    leg_id: str

    nominal_diameter_mm: float
    internal_diameter_mm: float

    velocity_m_s: float
    reynolds_number: float

    friction_factor: float
    pressure_drop_Pa_per_m: float

    sizing_method: str
    notes: Optional[str] = None
