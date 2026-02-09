# ======================================================================
# HVAC/heatloss/physics/cv_tai_model.py
# ======================================================================
"""
Cv / Tai Companion Model (v1 — Educational / Optional)

Purpose
-------
Provide legacy steady-state relationships between:

    • Fabric heat loss (ΣQf)
    • Total exposed area (ΣA)
    • Environmental temperature (Tei)
    • Air temperature (Tai)
    • Ventilation allowance (Qv)

This module:
✔ Performs NO fabric calculations
✔ Performs NO ventilation calculations
✔ Has NO GUI dependencies
✔ Is OPTIONAL for engines
✔ Exists to preserve engineering lineage

----------------------------------------
LEGACY CONTEXT (CIBSE-style)
----------------------------------------

Definitions:
    ΣQf   = total fabric heat loss (W)
    ΣA    = total exposed area (m²)
    Tei   = internal environmental temperature (°C)
            (what the room should *feel like*)
    Tai   = internal air temperature (°C)
    Cv    = convection factor (K)

Classic relationship:

    Cv = ΣQf / (ΣA · 4.8)

    Tai = Tei + Cv

Ventilation heat loss then becomes:

    Qv = V̇ · ρ · cₚ · (Tai − Tao)

----------------------------------------
IMPORTANT
----------------------------------------

• Tai MUST NOT be used inside fabric heat loss
• Doing so creates a circular reference
• Tai is DERIVED, never an input
• This module makes that explicit
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ----------------------------------------------------------------------
# Constants (legacy convection factor)
# ----------------------------------------------------------------------

CONVECTION_COEFF_W_M2K = 4.8  # W/m²·K (legacy steady-state)


# ----------------------------------------------------------------------
# Core computations
# ----------------------------------------------------------------------

def compute_cv(
    total_fabric_heat_loss_w: float,
    total_exposed_area_m2: float,
) -> float:
    """
    Compute convection factor Cv (K).

        Cv = ΣQf / (ΣA · 4.8)

    Raises:
        ValueError if area is zero or negative
    """

    if total_exposed_area_m2 <= 0.0:
        raise ValueError("Total exposed area must be > 0")

    return (
        total_fabric_heat_loss_w
        / (total_exposed_area_m2 * CONVECTION_COEFF_W_M2K)
    )


def compute_tai(
    tei_internal_env_temp_c: float,
    cv: float,
) -> float:
    """
    Compute internal air temperature Tai (°C).

        Tai = Tei + Cv
    """

    return tei_internal_env_temp_c + cv


# ----------------------------------------------------------------------
# Convenience bundle (optional)
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class CvTaiResult:
    """
    Immutable result container for Cv/Tai calculations.
    """
    cv_k: float
    tai_c: float
    tei_c: float


def compute_cv_tai(
    *,
    total_fabric_heat_loss_w: float,
    total_exposed_area_m2: float,
    tei_internal_env_temp_c: float,
) -> CvTaiResult:
    """
    Convenience wrapper that computes both Cv and Tai.

    Intended for:
        • Educational display
        • Optional ventilation coupling
        • Reporting
    """

    cv = compute_cv(
        total_fabric_heat_loss_w,
        total_exposed_area_m2,
    )

    tai = compute_tai(
        tei_internal_env_temp_c,
        cv,
    )

    return CvTaiResult(
        cv_k=cv,
        tai_c=tai,
        tei_c=tei_internal_env_temp_c,
    )


# ----------------------------------------------------------------------
# Demo / sanity check
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Example legacy room
    ΣQf = 1800.0   # W
    ΣA = 55.0      # m²
    Tei = 20.0     # °C

    result = compute_cv_tai(
        total_fabric_heat_loss_w=ΣQf,
        total_exposed_area_m2=ΣA,
        tei_internal_env_temp_c=Tei,
    )

    print("Cv:", round(result.cv_k, 3), "K")
    print("Tai:", round(result.tai_c, 2), "°C")
