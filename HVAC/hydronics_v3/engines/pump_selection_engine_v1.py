# ======================================================================
# HVAC/hydronics_v3/engines/pump_selection_engine_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

from HVAC_legacy.hydronics_v3.dto.pump_catalog_dto import (
    PumpCatalogDTO,
    PumpCandidateDTO,
    PumpCurvePointDTO,
)
from HVAC_legacy.hydronics_v3.dto.pump_duty_point_dto import PumpDutyPointInputDTO
from HVAC_legacy.hydronics_v3.dto.pump_selection_result_dto import PumpSelectionResultDTO


_RHO_WATER_KG_M3 = 1000.0
_G_M_S2 = 9.80665


def _pa_to_head_m(dp_pa: float) -> float:
    return dp_pa / (_RHO_WATER_KG_M3 * _G_M_S2)


def _validate_curve(points: List[PumpCurvePointDTO], pump_ref: str) -> None:
    if len(points) < 2:
        raise ValueError(f"Pump {pump_ref}: curve must have at least 2 points")

    last_f = None
    for p in points:
        if p.flow_m3_h <= 0:
            raise ValueError(f"Pump {pump_ref}: flow_m3_h must be > 0")
        if p.head_m < 0:
            raise ValueError(f"Pump {pump_ref}: head_m must be >= 0")
        if last_f is not None and p.flow_m3_h <= last_f:
            raise ValueError(f"Pump {pump_ref}: curve_points must be strictly increasing in flow_m3_h")
        last_f = p.flow_m3_h


def _interp_head(points: List[PumpCurvePointDTO], flow_m3_h: float) -> Optional[float]:
    """
    Linear interpolation within the curve range.
    Returns None if flow is outside the provided curve domain.
    """
    if flow_m3_h < points[0].flow_m3_h or flow_m3_h > points[-1].flow_m3_h:
        return None

    # Exact endpoints
    if flow_m3_h == points[0].flow_m3_h:
        return points[0].head_m
    if flow_m3_h == points[-1].flow_m3_h:
        return points[-1].head_m

    # Find segment
    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        if a.flow_m3_h <= flow_m3_h <= b.flow_m3_h:
            # linear interpolation
            t = (flow_m3_h - a.flow_m3_h) / (b.flow_m3_h - a.flow_m3_h)
            return a.head_m + t * (b.head_m - a.head_m)

    return None


class PumpSelectionEngineV1:
    """
    Deterministic pump selector.

    Selection rule (LOCKED for v1)
    ------------------------------
    Among pumps that can meet required head at design flow,
    select the pump with the smallest positive head_excess_m.
    (i.e. closest match without being under-duty)

    RED-STOP CONDITIONS
    -------------------
    • invalid duty input
    • empty catalog
    • curve invalid
    • no pump can meet duty point
    """

    @staticmethod
    def run(duty: PumpDutyPointInputDTO, catalog: PumpCatalogDTO) -> PumpSelectionResultDTO:
        if duty.design_flow_m3_h <= 0:
            raise ValueError("design_flow_m3_h must be > 0")

        if duty.required_head_pa <= 0:
            raise ValueError("required_head_pa must be > 0")

        if duty.head_margin_frac < 0:
            raise ValueError("head_margin_frac must be >= 0")

        if not catalog.pumps:
            raise ValueError("Pump catalog is empty")

        required_head_m = _pa_to_head_m(duty.required_head_pa) * (1.0 + duty.head_margin_frac)

        best: Optional[Tuple[float, PumpCandidateDTO, float]] = None
        # best = (head_excess_m, pump, predicted_head_m)

        for pump in catalog.pumps:
            _validate_curve(pump.curve_points, pump.pump_ref)

            predicted_head_m = _interp_head(pump.curve_points, duty.design_flow_m3_h)
            if predicted_head_m is None:
                # outside curve domain → not eligible in v1
                continue

            head_excess_m = predicted_head_m - required_head_m

            # must meet or exceed required head
            if head_excess_m < 0:
                continue

            if best is None or head_excess_m < best[0]:
                best = (head_excess_m, pump, predicted_head_m)

        if best is None:
            raise ValueError(
                "No pump in catalog can meet duty point: "
                f"flow={duty.design_flow_m3_h:.3f} m3/h, "
                f"required_head={required_head_m:.3f} m"
            )

        head_excess_m, pump, predicted_head_m = best

        return PumpSelectionResultDTO(
            system_id=duty.system_id,
            pump_ref=pump.pump_ref,
            design_flow_m3_h=duty.design_flow_m3_h,
            required_head_m=required_head_m,
            required_head_pa=duty.required_head_pa,
            predicted_pump_head_m=predicted_head_m,
            head_excess_m=head_excess_m,
            note="Selected closest pump meeting duty head at design flow (PumpSelectionEngineV1)",
        )
