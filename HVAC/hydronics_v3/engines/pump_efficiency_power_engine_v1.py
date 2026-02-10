# ======================================================================
# HVAC/hydronics_v3/engines/pump_efficiency_power_engine_v1.py
# ======================================================================

from __future__ import annotations

from typing import Optional

from HVAC.hydronics_v3.dto.operating_point_result_dto import (
    OperatingPointResultDTO,
)
from HVAC.hydronics_v3.dto.pump_efficiency_curve_dto import (
    PumpEfficiencyCurveDTO,
    PumpEfficiencyPointDTO,
)
from HVAC.hydronics_v3.dto.pump_power_result_dto import (
    PumpPowerResultDTO,
)

_RHO_WATER_KG_M3 = 1000.0
_G_M_S2 = 9.80665


class PumpEfficiencyPowerEngineV1:
    """
    Computes pump power and efficiency at a known operating point.

    DTO-in / DTO-out
    No mutation
    Red-stop strict
    """

    @staticmethod
    def _interp_efficiency(
        points: list[PumpEfficiencyPointDTO],
        flow_m3_h: float,
    ) -> float:
        if len(points) < 2:
            raise ValueError("Efficiency curve must have at least two points")

        last_flow = None
        for p in points:
            if p.flow_m3_h <= 0:
                raise ValueError("Efficiency curve flow must be > 0")
            if not (0.0 < p.efficiency <= 1.0):
                raise ValueError("Efficiency must be in (0, 1]")
            if last_flow is not None and p.flow_m3_h <= last_flow:
                raise ValueError("Efficiency points must be strictly increasing in flow")
            last_flow = p.flow_m3_h

        if flow_m3_h < points[0].flow_m3_h or flow_m3_h > points[-1].flow_m3_h:
            raise ValueError("Operating flow is outside efficiency curve range")

        for i in range(len(points) - 1):
            a = points[i]
            b = points[i + 1]
            if a.flow_m3_h <= flow_m3_h <= b.flow_m3_h:
                t = (flow_m3_h - a.flow_m3_h) / (b.flow_m3_h - a.flow_m3_h)
                return a.efficiency + t * (b.efficiency - a.efficiency)

        raise ValueError("Failed to interpolate pump efficiency")

    @staticmethod
    def run(
        operating_point: OperatingPointResultDTO,
        efficiency_curve: PumpEfficiencyCurveDTO,
        motor_efficiency: Optional[float] = None,
    ) -> PumpPowerResultDTO:

        if efficiency_curve.pump_ref != operating_point.pump_ref:
            raise ValueError("Pump reference mismatch")

        if motor_efficiency is not None:
            if not (0.0 < motor_efficiency <= 1.0):
                raise ValueError("Motor efficiency must be in (0, 1]")

        efficiency = PumpEfficiencyPowerEngineV1._interp_efficiency(
            efficiency_curve.efficiency_points,
            operating_point.operating_flow_m3_h,
        )

        # Hydraulic power: P = ρ g Q H
        flow_m3_s = operating_point.operating_flow_m3_h / 3600.0
        hydraulic_power_w = (
            _RHO_WATER_KG_M3
            * _G_M_S2
            * flow_m3_s
            * operating_point.operating_head_m
        )

        shaft_power_w = hydraulic_power_w / efficiency

        electrical_power_w: Optional[float] = None
        if motor_efficiency is not None:
            electrical_power_w = shaft_power_w / motor_efficiency

        return PumpPowerResultDTO(
            system_id=operating_point.system_id,
            pump_ref=operating_point.pump_ref,
            flow_m3_h=operating_point.operating_flow_m3_h,
            head_pa=operating_point.operating_head_pa,
            head_m=operating_point.operating_head_m,
            efficiency=efficiency,
            hydraulic_power_w=hydraulic_power_w,
            shaft_power_w=shaft_power_w,
            motor_efficiency=motor_efficiency,
            electrical_power_w=electrical_power_w,
            note="Pump power evaluated at operating point",
        )
