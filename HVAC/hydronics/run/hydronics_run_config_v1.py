# ======================================================================
# HVAC/hydronics/run/hydronics_run_config_v1.py
# ======================================================================

"""
HVACgooee — Hydronics Run Config v1
----------------------------------

Defines user-controlled execution options for a hydronics run.

This object is GUI-safe and engine-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class HydronicsRunConfigV1:
    """
    User-selected run options.

    include_balancing:
        If True, run lockshield balancing engine (v1).
        If False, skip entirely.

    index_strategy:
        'auto'     -> highest ΔP terminal becomes index
        'explicit' -> GUI/user supplies index terminal (future use)

    pump_safety_factor:
        Multiplier applied during pump duty resolution.
    """
    include_balancing: bool = False
    index_strategy: Literal["auto", "explicit"] = "auto"
    pump_safety_factor: float = 1.1
