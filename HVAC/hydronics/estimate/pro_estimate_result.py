# ======================================================================
# HVAC/hydronics/estimate/pro_estimate_result.py
# ======================================================================

"""
HVACgooee — Professional Hydronics Estimate Result DTO
------------------------------------------------------

Container for a complete Stage-1 Professional Mode estimate.

This result:
• Is NOT a design output
• Is NOT suitable for sizing
• Is NOT suitable for ΔP calculations
• Is NOT persisted
• Must be explicitly triggered by the user
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from HVAC.hydronics.estimate.pro_leg_estimate import ProLegEstimate


@dataclass(slots=True)
class ProEstimateResult:
    """
    Top-level container for a professional hydronics estimate (Stage-1).

    This object is intentionally incompatible with downstream solvers.
    """

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    run_id: str
    timestamp_utc: datetime

    # ------------------------------------------------------------------
    # Mode / stage identity (explicit)
    # ------------------------------------------------------------------
    mode: str = "PROFESSIONAL"
    stage: str = "ESTIMATE"

    # ------------------------------------------------------------------
    # System-wide provisional values
    # ------------------------------------------------------------------
    total_heat_demand_w: float = 0.0
    total_flow_lps: float = 0.0

    # ------------------------------------------------------------------
    # Structural outcome
    # ------------------------------------------------------------------
    index_leg_id: str = ""

    # ------------------------------------------------------------------
    # Per-leg estimates
    # ------------------------------------------------------------------
    legs: List[ProLegEstimate] = None

    # ------------------------------------------------------------------
    # Safety banner
    # ------------------------------------------------------------------
    provisional: bool = True
    confidence: str = "LOW"
    disclaimer: str = (
        "PROVISIONAL ESTIMATE ONLY — "
        "Not a design result. "
        "Not suitable for pipe sizing, ΔP, or pump selection."
    )
