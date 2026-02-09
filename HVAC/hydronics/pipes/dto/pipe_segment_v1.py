from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class PipeSegmentV1:
    """
    Physical pipe segment within a leg.
    """

    segment_id: str
    leg_id: str

    length_m: float

    nominal_diameter_mm: float
    internal_diameter_mm: float

    roughness_mm: float = 0.05
    local_k: float = 0.0

    notes: Optional[str] = None
