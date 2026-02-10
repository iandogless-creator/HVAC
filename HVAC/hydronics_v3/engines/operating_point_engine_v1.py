# ======================================================================
# HVAC/hydronics_v3/engines/operating_point_engine_v1.py
# ======================================================================

from __future__ import annotations

import math
from typing import Optional

from HVAC.hydronics_v3.dto.system_curve_dto import SystemCurveDTO
from HVAC.hydronics_v3.dto.pump_catalog_dto import (
    PumpCandidateDTO,
    PumpCurvePointDTO,
)
from HVAC.hydronics_v3.dto.operating_point_result_dto import (
    OperatingPointResultDTO,
)

_RHO_WATER_KG_M3 = 1000.0
_G_M_S2 = 9.80665


def _head_m_to_pa(head_m: float) -> float:
    return head_m * _RHO_WATER_KG_M3 * _G_M_S2


class OperatingPointEngineV1:
    """
    Determines the hydraulic operating point by intersecting
    the system curve with the pump curve.

    LOCKED
    ------
    • No iteration loops
    • Deterministic
    • DTO-in / DTO-out
    • Red-stop on failure
    """

    @staticmethod
    def run(
        system_curve: SystemCurveDTO,
        pump: PumpCandidateDTO,
    ) -> OperatingPointResultDTO:

        if system_curve.k_pa_per_m3h2 <= 0:
            raise ValueError("System curve coefficient must be > 0")

        points = pump.curve_points
        if len(points) < 2:
            raise ValueError("Pump curve must contain at least two points")

        # Walk each linear segment of the pump curve
        for i in range(len(points) - 1):
            p1: PumpCurvePointDTO = points[i]
            p2: PumpCurvePointDTO = points[i + 1]

            q1, h1 = p1.flow_m3_h, p1.head_m
            q2, h2 = p2.flow_m3_h, p2.head_m

            # Pump curve: h = a*q + b
            a = (h2 - h1) / (q2 - q1)
            b = h1 - a * q1

            # System curve in head form:
            # head = (K / (ρg)) * q²
            k_head = system_curve.k_pa_per_m3h2 / (_RHO_WATER_KG_M3 * _G_M_S2)

            # Solve: a*q + b = k_head * q²
            # → k*q² - a*q - b = 0
            A = k_head
            B = -a
            C = -b

            disc = B * B - 4 * A * C
            if disc < 0:
                continue

            sqrt_disc = math.sqrt(disc)

            for q in (
                (B + sqrt_disc) / (2 * A),
                (B - sqrt_disc) / (2 * A),
            ):
                if q1 <= q <= q2 and q > 0:
                    head_m = a * q + b
                    head_pa = _head_m_to_pa(head_m)

                    return OperatingPointResultDTO(
                        system_id=system_curve.system_id,
                        pump_ref=pump.pump_ref,
                        operating_flow_m3_h=q,
                        operating_head_pa=head_pa,
                        operating_head_m=head_m,
                        note="Operating point from pump/system curve intersection",
                    )

        raise ValueError(
            f"No valid operating point found for pump {pump.pump_ref}"
        )
