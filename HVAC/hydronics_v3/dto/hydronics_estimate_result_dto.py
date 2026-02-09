
# ======================================================================
# HVAC/hydronics_v3/dto/hydronics_estimate_result_dto.py
# ======================================================================

"""
hydronics_estimate_result_dto.py
--------------------------------

HVACgooee — Hydronics Estimate Result DTO (v1)

Purpose
-------
Immutable result of a first-pass hydronic system estimate.

This represents ENGINE OUTPUT, not editable intent.

RULES (LOCKED)
--------------
• DTO ONLY (no logic)
• Immutable
• Serializable
• Units explicit
• No GUI imports
• No sizing detail here
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ----------------------------------------------------------------------
# DTO
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HydronicsEstimateResultDTO:
    """
    Result of hydronic estimate stage (v1).

    Provides sufficient information to:
    • size emitters
    • size primary pipework (next stage)
    • select pump (estimate)
    """

    # ------------------------------------------------------------
    # Thermal confirmation
    # ------------------------------------------------------------
    design_heat_load_w: float
    """
    Design heat load used for estimate (Qt).
    """

    # ------------------------------------------------------------
    # Flow results
    # ------------------------------------------------------------
    design_flow_rate_l_s: float
    """
    Required system flow rate (litres/second).
    """

    design_flow_rate_m3_h: float
    """
    Required system flow rate (m³/hour).
    """

    # ------------------------------------------------------------
    # Temperature regime
    # ------------------------------------------------------------
    flow_temp_c: float
    return_temp_c: float
    delta_t_k: float
    """
    Operating temperatures used in estimate.
    """

    # ------------------------------------------------------------
    # Pressure (ESTIMATE ONLY)
    # ------------------------------------------------------------
    estimated_system_pressure_drop_pa: float
    """
    Estimated total system pressure drop (Pa).

    NOT a final indexed path result.
    """

    estimated_system_pressure_drop_m: float
    """
    Estimated system pressure drop expressed as metres head.
    """

    # ------------------------------------------------------------
    # Pump estimate
    # ------------------------------------------------------------
    estimated_pump_power_w: Optional[float]
    """
    Estimated electrical pump power (W), if derived.
    """

    # ------------------------------------------------------------
    # Validity / metadata
    # ------------------------------------------------------------
    calculation_notes: Optional[str] = None
    """
    Non-functional notes or warnings.
    """

    estimate_valid: bool = True
    """
    Explicit validity flag.
    """
