"""
flow_units.py
-------------
# CANONICAL v1 — DO NOT BYPASS

HVACgooee — Flow Unit Display Helper (v1)

Purpose
-------
Provide canonical conversions and formatted display of flow rates:

    • m³/h
    • L/s
    • kg/s

This module is:
✔ Pure utility
✔ Solver-agnostic
✔ Safe to use in CLI, GUI, reports, overlays
✔ Educational-friendly

No HVAC logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass


# ================================================================
# DATA MODEL
# ================================================================
@dataclass(frozen=True)
class FlowUnits:
    m3_h: float
    l_s: float
    kg_s: float


# ================================================================
# CONVERSIONS
# ================================================================
def flow_from_m3_h(
    m3_h: float,
    *,
    density_kg_m3: float = 1000.0,
) -> FlowUnits:
    """
    Convert flow from m³/h to all common units.

    density_kg_m3:
        • 1000 kg/m³ ≈ water
        • override for glycol, etc.
    """
    if m3_h < 0:
        raise ValueError("Flow must be non-negative")

    l_s = (m3_h * 1000.0) / 3600.0
    kg_s = (m3_h / 3600.0) * density_kg_m3

    return FlowUnits(
        m3_h=m3_h,
        l_s=l_s,
        kg_s=kg_s,
    )


def flow_from_l_s(
    l_s: float,
    *,
    density_kg_m3: float = 1000.0,
) -> FlowUnits:
    if l_s < 0:
        raise ValueError("Flow must be non-negative")

    m3_h = (l_s * 3600.0) / 1000.0
    kg_s = l_s * (density_kg_m3 / 1000.0)

    return FlowUnits(
        m3_h=m3_h,
        l_s=l_s,
        kg_s=kg_s,
    )


def flow_from_kg_s(
    kg_s: float,
    *,
    density_kg_m3: float = 1000.0,
) -> FlowUnits:
    if kg_s < 0:
        raise ValueError("Flow must be non-negative")

    m3_h = (kg_s / density_kg_m3) * 3600.0
    l_s = kg_s / (density_kg_m3 / 1000.0)

    return FlowUnits(
        m3_h=m3_h,
        l_s=l_s,
        kg_s=kg_s,
    )


# ================================================================
# DISPLAY HELPERS
# ================================================================
def describe_flow(flow: FlowUnits, *, precision: int = 4) -> str:
    """
    Pretty, side-by-side display for CLI / reports.
    """
    fmt = f"{{:.{precision}f}}"
    return (
        "Flow rate:\n"
        f"  {fmt.format(flow.m3_h)} m³/h\n"
        f"  {fmt.format(flow.l_s)} L/s\n"
        f"  {fmt.format(flow.kg_s)} kg/s"
    )
