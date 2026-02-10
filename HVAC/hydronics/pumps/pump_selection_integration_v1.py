# ======================================================================
# HVAC/hydronics/pumps/pump_selection_integration_v1.py
# ======================================================================

"""
HVACgooee — Pump Selection Integration v1
-----------------------------------------

Wires:
    ΔP aggregation → Pump duty resolution → Pump sizing engine

This module:
• Owns orchestration only
• Does NOT implement pump physics
• Does NOT mutate upstream state
"""

from __future__ import annotations

from typing import Iterable, Optional

from HVAC.hydronics.pipes.dp.pressure_drop_path_v1 import PressureDropPathV1
from HVAC.hydronics.pumps.pump_duty_resolver_v1 import resolve_pump_duty_v1
from HVAC.hydronics.pumps.pump_sizing_engine import (
    size_pump_from_flow_and_dp,
    PumpSizingConfig,
    PumpSizingResult,
)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def select_pump_from_hydronics_v1(
    *,
    pressure_paths: Iterable[PressureDropPathV1],
    design_flow_m3_s: float,
    cfg: Optional[PumpSizingConfig] = None,
) -> PumpSizingResult:
    """
    Full pump sizing from hydronic results.

    PARAMETERS
    ----------
    pressure_paths:
        Output of ΔP aggregation (per path Pa totals).

    design_flow_m3_s:
        Authoritative design flow (m³/s).

    cfg:
        Optional PumpSizingConfig.

    RETURNS
    -------
    PumpSizingResult
    """

    # ------------------------------------------------------------
    # 1) Resolve index ΔP
    # ------------------------------------------------------------
    duty = resolve_pump_duty_v1(
        pressure_paths=pressure_paths,
        design_flow_m3_s=design_flow_m3_s,
    )

    # ------------------------------------------------------------
    # 2) Convert flow to L/h (pump engine expects this)
    # ------------------------------------------------------------
    flow_lph = duty.design_flow_m3_s * 3600.0 * 1000.0

    # ------------------------------------------------------------
    # 3) Call existing pump sizing engine
    # ------------------------------------------------------------
    return size_pump_from_flow_and_dp(
        flow_lph=flow_lph,
        total_dp_Pa=duty.required_head_Pa,
        cfg=cfg,
    )
