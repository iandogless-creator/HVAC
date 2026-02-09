# ======================================================================
# HVAC/hydronics/pipes/dp/pressure_drop_path_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True, slots=True)
class PressureDropPathV1:
    """
    Aggregated pressure drop result for a single hydronic path.
    """

    path_id: str
    leg_ids: List[str]

    total_dp_Pa: float
    per_leg_dp_Pa: Dict[str, float]
