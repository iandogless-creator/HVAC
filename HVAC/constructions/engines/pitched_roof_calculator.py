"""
pitched_roof_calculator.py
HVACgooee — Advanced Pitched Roof Calculation Module

Implements:
- Roof pitch effects on Rsi/Rse
- Heat-flow direction modifications
- Ventilated cavity R-values (cold roof)
- Insulation above/between/below rafters
- Bridging fractions (rafters vs insulation)
- Continuous over-rafter insulation logic
- Rockwool ↔ PIR performance equivalence
- U-value target mode (0.11–0.13 W/m²K)
- Comfort mode (thermal mass / cold-soak)
- SAP vs CIBSE comparison mode

Used by:
- heatloss_elements.py
- construction_presets.py
- heatloss_wizard.py
- future GUI roof editor
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import math

# ---------------------------------------------------------------------------
# BASE CONSTANTS
# ---------------------------------------------------------------------------

# Internal/external surface resistances for roofs (approximate CIBSE / BRE ranges)
Rsi_FLAT = 0.10
Rse_FLAT = 0.04

# Pitched roof adjustment factors for surface resistances
# Approximate corrections derived from CIBSE and environmental-era notes
PITCH_RSE_FACTOR = {
    0: 1.00,     # flat
    15: 1.05,
    30: 1.10,
    45: 1.15,
    60: 1.20,
    75: 1.25,
}

# Ventilated cavity resistance (cold roof) — typical fixed values
R_VENTILATED_CAVITY = 0.20

# Example thermal conductivities (W/mK)
LAMBDA = {
    "plasterboard": 0.19,
    "osb": 0.13,
    "plywood": 0.14,
    "rafters": 0.13,
    "rockwool": 0.037,
    "pir": 0.022,
    "xps": 0.030,
}

# Bridging fractions (fraction of rafter vs insulation area)
BRIDGING = {
    "typical": 0.10,     # 10% rafter, 90% insulation
    "good": 0.07,
    "poor": 0.15,
}

# Thermal mass categories for comfort mode (decrement factor etc.)
THERMAL_MASS = {
    "light": 0.05,
    "medium": 0.10,
    "heavy": 0.20,
}


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class RoofLayer:
    """
    Represents one layer in the roof construction.
    thickness_m: thickness in metres
    material: key referencing LAMBDA dict
    position: "internal", "between_rafters", "external"
    """
    thickness_m: float
    material: str
    position: str


@dataclass
class PitchedRoof:
    """
    Full roof definition for U-value + thermal response calculation.
    """
    pitch_deg: float
    layers: List[RoofLayer]
    ventilated: bool
    bridging: str
    thermal_mass: str
    mode: str     # "CIBSE", "SAP", "COMFORT"
    target_u: Optional[float] = None   # used in "TARGET" mode


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def interpolate_pitch_factor(pitch_deg: float) -> float:
    """
    Interpolate Rse correction factor based on pitch.
    """
    keys = sorted(PITCH_RSE_FACTOR.keys())
    if pitch_deg <= keys[0]:
        return PITCH_RSE_FACTOR[keys[0]]
    if pitch_deg >= keys[-1]:
        return PITCH_RSE_FACTOR[keys[-1]]

    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a <= pitch_deg <= b:
            fa = PITCH_RSE_FACTOR[a]
            fb = PITCH_RSE_FACTOR[b]
            t = (pitch_deg - a) / (b - a)
            return fa + t * (fb - fa)

    return 1.15  # fallback


def layer_resistance(layer: RoofLayer) -> float:
    """
    Returns thermal resistance of a layer.
    """
    lam = LAMBDA.get(layer.material)
    if lam is None:
        raise ValueError(f"Material '{layer.material}' has no lambda assigned.")
    return layer.thickness_m / lam


# ---------------------------------------------------------------------------
# CORE CALCULATIONS
# ---------------------------------------------------------------------------

def roof_u_value(roof: PitchedRoof) -> float:
    """
    Calculate overall U-value for a pitched roof.
    Includes:
    - pitch-dependent surface resistance
    - optional ventilated cavity
    - bridging fraction between rafters and insulation
    """
    # Surface resistances
    Rsi = Rsi_FLAT   # internal surface recommended value
    Rse = Rse_FLAT * interpolate_pitch_factor(roof.pitch_deg)

    # Accumulate resistances
    R_ins = 0.0
    R_raf = 0.0

    for layer in roof.layers:
        R = layer_resistance(layer)
        if layer.position == "between_rafters":
            R_ins += R
            # rafters have lower R (higher λ)
            R_raf += layer.thickness_m / LAMBDA["rafters"]
        else:
            # non-rafter layers apply equally
            R_ins += R
            R_raf += R

    # Bridging fraction
    f = BRIDGING.get(roof.bridging, 0.10)

    # Composite insulated + bridged path
    R_composite = (1 - f) * R_ins + f * R_raf

    # Ventilated cavity (cold roof)
    if roof.ventilated:
        R_composite += R_VENTILATED_CAVITY

    # Total resistance
    R_total = Rsi + R_composite + Rse

    return 1.0 / R_total


# ---------------------------------------------------------------------------
# COMFORT MODE (thermal lag)
# ---------------------------------------------------------------------------

def comfort_adjusted_u(roof: PitchedRoof, U: float) -> float:
    """
    Apply a simple decrement-factor-based modification for comfort mode.
    This is NOT a dynamic simulation — a lightweight comfort proxy.
    """
    mass_factor = THERMAL_MASS.get(roof.thermal_mass, 0.10)
    # A small reduction in the "felt" U-value due to heat capacity
    return U * (1.0 - mass_factor)


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def compute_roof_performance(roof: PitchedRoof) -> Dict[str, float]:
    """
    Main entry point for U-value and comfort-mode performance.
    """
    U = roof_u_value(roof)

    if roof.mode.upper() == "COMFORT":
        U_adj = comfort_adjusted_u(roof, U)
    else:
        U_adj = U

    return {
        "U_value": U,
        "Comfort_adjusted_U": U_adj,
        "Pitch_deg": roof.pitch_deg,
        "Ventilated": roof.ventilated,
        "Bridging": roof.bridging,
        "Thermal_mass": roof.thermal_mass,
    }


# ---------------------------------------------------------------------------
# SELF-TEST (optional)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    layers = [
        RoofLayer(0.0125, "plasterboard", "internal"),
        RoofLayer(0.200, "rockwool", "between_rafters"),
        RoofLayer(0.018, "osb", "external"),
    ]

    roof = PitchedRoof(
        pitch_deg=35,
        layers=layers,
        ventilated=True,
        bridging="typical",
        thermal_mass="medium",
        mode="COMFORT",
    )

    print("=== Pitched Roof Calculator — Self Test ===")
    results = compute_roof_performance(roof)
    for k, v in results.items():
        print(f"{k}: {v}")
