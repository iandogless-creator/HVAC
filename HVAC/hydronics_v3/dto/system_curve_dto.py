# ======================================================================
# HVAC/hydronics_v3/dto/system_curve_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemCurveDTO:
    """
    Canonical system curve representation.

    Δp = K * Q²

    Q in m³/h
    Δp in Pa
    """

    system_id: str

    # Quadratic resistance coefficient
    k_pa_per_m3h2: float

    # Optional reference / diagnostic
    note: str = ""
