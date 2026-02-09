"""
y_value_engine.py
-----------------

HVACgooee — Dynamic Y-value Engine (2025 edition)

Computes the intermittent heating coefficient Y [W/m²K] for
each surface, taking into account:

    • Heating period (24h / 16h / 12h / 10h / 8h / 6h)
    • U-value of the element
    • Areal heat capacity C_areal [J/m²K] when available
    • Surface type (wall/floor/roof/window/door/linear_bridge)

Design:
    1. If C_areal is provided and sensible:
           → use dynamic mass-based model (C_areal + period + U)

    2. Else:
           → fall back to legacy type-based multipliers
              (simple U * factor(period, type) model)

Explicit BEGIN/END markers are included for readability.
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union
# END IMPORTS
# ================================================================



# ================================================================
# BEGIN DATA STRUCTURES
# ================================================================

# ------------------------------------------------------------
# BEGIN CLASS: ThermalPeriod
# ------------------------------------------------------------
@dataclass(frozen=True)
class ThermalPeriod:
    label: str
    hours: float
# ------------------------------------------------------------
# END CLASS: ThermalPeriod
# ------------------------------------------------------------


# ------------------------------------------------------------
# BEGIN CLASS: MassCategory
# ------------------------------------------------------------
@dataclass(frozen=True)
class MassCategory:
    name: str
    factor: float
# ------------------------------------------------------------
# END CLASS: MassCategory
# ------------------------------------------------------------

# ================================================================
# END DATA STRUCTURES
# ================================================================



# ================================================================
# BEGIN SECTION: PERIOD PARSING
# ================================================================

# ------------------------------------------------------------
# BEGIN FUNCTION: parse_thermal_period
# ------------------------------------------------------------
def parse_thermal_period(period: Union[str, ThermalPeriod]) -> ThermalPeriod:
    """
    Parse a heating period specifier.

    Accepts:
        - "24h", "16h", "12h", "10h", "8h", "6h"
        - "continuous"
        - ThermalPeriod instance

    Returns:
        ThermalPeriod(label, hours)
    """
    if isinstance(period, ThermalPeriod):
        return period

    if isinstance(period, str):
        text = period.strip().lower()
        if text.endswith("h"):
            try:
                h = float(text[:-1])
                if h <= 0:
                    h = 24.0
                return ThermalPeriod(label=text, hours=h)
            except ValueError:
                pass

        if text in ("continuous", "24", "24h_cont"):
            return ThermalPeriod(label="24h", hours=24.0)
        if text in ("16", "16hr"):
            return ThermalPeriod(label="16h", hours=16.0)
        if text in ("12", "12hr"):
            return ThermalPeriod(label="12h", hours=12.0)
        if text in ("10", "10hr"):
            return ThermalPeriod(label="10h", hours=10.0)
        if text in ("8", "8hr"):
            return ThermalPeriod(label="8h", hours=8.0)
        if text in ("6", "6hr"):
            return ThermalPeriod(label="6h", hours=6.0)

    return ThermalPeriod(label="24h", hours=24.0)
# ------------------------------------------------------------
# END FUNCTION: parse_thermal_period
# ------------------------------------------------------------

# ================================================================
# END SECTION: PERIOD PARSING
# ================================================================



# ================================================================
# BEGIN SECTION: MASS CATEGORISATION
# ================================================================

# ------------------------------------------------------------
# BEGIN FUNCTION: _classify_mass
# ------------------------------------------------------------
def _classify_mass(C_areal: float) -> MassCategory:
    """
    Classify construction mass from C_areal [J/m²K].

    Thresholds (J/m²K), approximate:
        <  30 000 : very_light
        <  60 000 : light
        < 110 000 : medium
        < 180 000 : heavy
        >=180 000 : very_heavy
    """
    if C_areal < 30_000:
        return MassCategory("very_light", 0.5)
    if C_areal < 60_000:
        return MassCategory("light", 0.8)
    if C_areal < 110_000:
        return MassCategory("medium", 1.0)
    if C_areal < 180_000:
        return MassCategory("heavy", 1.2)
    return MassCategory("very_heavy", 1.5)
# ------------------------------------------------------------
# END FUNCTION: _classify_mass
# ------------------------------------------------------------


# ------------------------------------------------------------
# BEGIN FUNCTION: _period_factor
# ------------------------------------------------------------
def _period_factor(period: ThermalPeriod) -> float:
    """
    Factor that increases Y for shorter heating periods.

    24h → 0
    16h → moderate
    12h → higher
    8h, 6h → highest

    Clamped to [0, 1.2] for stability.
    """
    h = max(1.0, min(24.0, period.hours))
    phi = (24.0 - h) / 16.0  # 24h→0, 8h→1.0

    if phi < 0:
        phi = 0.0
    if phi > 1.2:
        phi = 1.2

    return phi
# ------------------------------------------------------------
# END FUNCTION: _period_factor
# ------------------------------------------------------------

# ================================================================
# END SECTION: MASS CATEGORISATION
# ================================================================



# ================================================================
# BEGIN SECTION: LEGACY TYPE/ U MODEL
# ================================================================

_BASE_PERIOD_FACTORS = {
    "24h": 0.0,
    "16h": 0.7,
    "12h": 1.0,
    "10h": 1.2,
    "8h": 1.4,
    "6h": 1.6,
}

_TYPE_FACTORS = {
    "wall": 1.0,
    "floor": 0.9,
    "roof": 1.1,
    "ceiling": 1.0,
    "window": 0.7,
    "door": 0.8,
    "linear_bridge": 1.2,
}

# ------------------------------------------------------------
# BEGIN FUNCTION: _legacy_y
# ------------------------------------------------------------
def _legacy_y(surface_type: str, U: float, period: ThermalPeriod) -> float:
    """
    Simple Y-value model when C_areal is not known:

        Y = U * base_factor(period) * type_factor(surface_type)
    """
    if U <= 0:
        return 0.0

    tkey = surface_type.lower()
    type_factor = _TYPE_FACTORS.get(tkey, 1.0)

    label = period.label.lower()
    base = _BASE_PERIOD_FACTORS.get(label, None)

    if base is None:
        h = period.hours
        if h >= 24:
            base = 0.0
        elif h >= 16:
            base = 0.7
        elif h >= 12:
            base = 1.0
        elif h >= 10:
            base = 1.2
        elif h >= 8:
            base = 1.4
        else:
            base = 1.6

    Y = U * base * type_factor
    return max(Y, 0.0)
# ------------------------------------------------------------
# END FUNCTION: _legacy_y
# ------------------------------------------------------------

# ================================================================
# END SECTION: LEGACY TYPE/ U MODEL
# ================================================================



# ================================================================
# BEGIN SECTION: DYNAMIC MASS MODEL
# ================================================================

# ------------------------------------------------------------
# BEGIN FUNCTION: _dynamic_y
# ------------------------------------------------------------
def _dynamic_y(surface_type: str, U: float, period: ThermalPeriod, C_areal: float) -> float:
    """
    Mass-based Y-value model:

        Y_dynamic = U * k0 * period_factor(period) * mass_factor(C_areal)

    Where:
        k0 ≈ 3.0
        period_factor ∈ [0, 1.2]
        mass_factor  ∈ [0.5, 1.5]
    """
    if U <= 0 or C_areal <= 0:
        return 0.0

    mass_cat = _classify_mass(C_areal)
    pf = _period_factor(period)
    k0 = 3.0

    Y = U * k0 * pf * mass_cat.factor
    return max(Y, 0.0)
# ------------------------------------------------------------
# END FUNCTION: _dynamic_y
# ------------------------------------------------------------

# ================================================================
# END SECTION: DYNAMIC MASS MODEL
# ================================================================



# ================================================================
# BEGIN SECTION: PUBLIC API
# ================================================================

# ------------------------------------------------------------
# BEGIN FUNCTION: compute_y_value
# ------------------------------------------------------------
def compute_y_value(
    surface_type: str,
    U: float,
    period: Union[str, ThermalPeriod],
    C_areal: Optional[float] = None,
) -> float:
    """
    Compute Y [W/m²K] for a surface.

    If C_areal is provided and > ~5 J/m²K:
        → dynamic mass-based model

    Else:
        → legacy type/U-based multiplier model
    """
    if U <= 0:
        return 0.0

    period_struct = parse_thermal_period(period)

    if C_areal is not None and C_areal > 5.0:
        return _dynamic_y(surface_type, U, period_struct, C_areal)

    return _legacy_y(surface_type, U, period_struct)
# ------------------------------------------------------------
# END FUNCTION: compute_y_value
# ------------------------------------------------------------

# ================================================================
# END SECTION: PUBLIC API
# ================================================================
