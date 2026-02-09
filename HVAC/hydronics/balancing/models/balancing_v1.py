# ======================================================================
# HVAC/hydronics/balancing/models/balancing_v1.py
# ======================================================================

"""
HVACgooee — Balancing Models v1
------------------------------

Immutable result containers for hydronic balancing.

No logic.
No engine code.
Safe for GUI and reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class BalancingLegResultV1:
    """
    Balancing result for one terminal leg.
    """
    leg_id: str
    required_dp_pa: float
    applied_dp_pa: float
    valve_setting: Optional[str] = None


@dataclass(frozen=True, slots=True)
class BalancingSummaryV1:
    """
    Overall balancing summary.
    """
    index_leg_id: str
    index_dp_pa: float
    legs: List[BalancingLegResultV1]
