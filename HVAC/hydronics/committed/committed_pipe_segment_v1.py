# HVAC/hydronics/committed/committed_pipe_segment_v1.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

SegmentKind = Literal["pipe", "fitting"]

@dataclass(frozen=True, slots=True)
class CommittedPipeSegmentV1:
    """
    Authoritative geometric segment inside a hydronic leg.

    • Used for ΔP aggregation
    • Immutable
    • Flow assumed uniform within leg
    """

    segment_id: str
    leg_id: str

    kind: SegmentKind  # "pipe" | "fitting"

    # Geometry
    length_m: float = 0.0          # pipes only
    diameter_m: float | None = None

    # Fitting resistance
    k_value: float = 0.0           # fittings only

    # Audit
    label: str | None = None

@dataclass(frozen=True, slots=True)
class SizedPipeSegmentV1:
    segment_id: str
    leg_id: str

    diameter_m: float
    velocity_m_s: float

    pressure_drop_Pa_per_m: float  # pipes
