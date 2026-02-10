# ======================================================================
# HVAC/hydronics/pumps/pump_duty_resolver_v1.py
# ======================================================================

"""
HVACgooee — Pump Duty Resolver v1
--------------------------------

Resolves pump duty point from ΔP aggregation results.
"""

from __future__ import annotations

from typing import Iterable

from HVAC.hydronics.pipes.dp.pressure_drop_path_v1 import PressureDropPathV1
from HVAC.hydronics.pumps.dto.pump_duty_point_v1 import PumpDutyPointV1


def resolve_pump_duty_v1(
    *,
    pressure_paths: Iterable[PressureDropPathV1],
    design_flow_m3_s: float,
) -> PumpDutyPointV1:
    """
    Determine pump duty point.

    RULES
    -----
    • Index path = max total ΔP
    • Flow is authoritative upstream
    """

    max_dp = None

    for path in pressure_paths:
        if max_dp is None or path.total_dp_Pa > max_dp:
            max_dp = path.total_dp_Pa

    if max_dp is None:
        raise RuntimeError("[PumpDuty] No pressure paths supplied.")

    return PumpDutyPointV1(
        design_flow_m3_s=design_flow_m3_s,
        required_head_Pa=max_dp,
    )
