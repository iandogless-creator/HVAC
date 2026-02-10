from __future__ import annotations
from dataclasses import dataclass
from typing import List

from HVAC.hydronics.pipes.dto.pipe_segment_v1 import PipeSegmentV1


@dataclass(frozen=True, slots=True)
class CommittedLegGeometryV1:
    """
    Explicit pipe geometry for a committed hydronic leg.
    """

    leg_id: str
    segments: List[PipeSegmentV1]
