# ======================================================================
# HVACgooee — Heat-Loss Readiness DTO
# Phase: I-A — Execution Gate
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class HeatLossReadiness:
    """
    Heat-loss execution readiness status.

    • Pure data object
    • No logic
    • Human-readable blocking reasons
    """

    is_ready: bool
    blocking_reasons: List[str]