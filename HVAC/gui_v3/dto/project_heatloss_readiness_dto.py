# ======================================================================
# HVACgooee — Project Heat-Loss Readiness DTO
# Phase: D.8 — Project-Level Readiness
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class ProjectHeatLossReadinessDTO:
    """
    GUI-owned project-level readiness status for heat-loss execution.

    Presence-based only.
    Non-authoritative.
    """

    is_ready: bool
    blocking_reasons: List[str]
