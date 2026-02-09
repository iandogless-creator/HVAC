# ======================================================================
# HVAC/hydronics_v3/dto/hydronics_estimate_input_dto.py
# ======================================================================

"""
hydronics_estimate_input_dto.py
-------------------------------

HVACgooee — Hydronics Estimate Input DTO (v1)

Purpose
-------
Immutable declaration of hydronic system intent
required to perform a first-pass hydronic estimate.

RULES (LOCKED)
--------------
• DTO ONLY (no logic, no validation)
• Immutable
• Serializable
• Units explicit
• No GUI imports
• No heat-loss calculation here
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ----------------------------------------------------------------------
# Enumerations (string-based, serialisation-safe)
# ----------------------------------------------------------------------

HydronicSystemType = Literal[
    "radiators",
    "underfloor",
    "fan_coils",
    "mixed",
]


# ----------------------------------------------------------------------
# DTO
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HydronicsEstimateInputDTO:
    """
    Declared hydronic design intent for estimate stage.

    This DTO represents WHAT the engineer intends to design,
    not HOW it is calculated.
    """

    # ------------------------------------------------------------
    # Thermal demand
    # ------------------------------------------------------------
    design_heat_load_w: float
    """
    Total design heat load (Qt) in watts.

    MUST originate from Heat-Loss v3.
    """

    # ------------------------------------------------------------
    # Temperature regime
    # ------------------------------------------------------------
    flow_temp_c: float
    return_temp_c: float
    """
    Flow / return temperatures (°C).

    ΔT = flow_temp_c - return_temp_c
    """

    # ------------------------------------------------------------
    # System intent
    # ------------------------------------------------------------
    system_type: HydronicSystemType
    """
    High-level emitter/system classification.
    """

    include_balancing: bool = False
    """
    Whether balancing devices (e.g. lockshields)
    should be included in the estimate.
    """

    # ------------------------------------------------------------
    # Future expansion (INTENTIONALLY UNUSED IN v1)
    # ------------------------------------------------------------
    diversity_factor: float | None = None
    """
    Optional diversity factor (0–1).
    Not applied in v1.
    """

    design_notes: str | None = None
    """
    Optional engineer notes (non-functional).
    """
