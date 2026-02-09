"""
hydronics_distribution_result_v1.py
-----------------------------------

HVACgooee — Hydronics Distribution Result (v1)

Purpose
-------
Formalises the output of the "duct 1.5" layer:
distribution feasibility + budgeting.

This is a contract object that captures:
    - derived flow from QT + ΔT
    - design targets (velocity, dp/m)
    - pressure/head budgets (early-stage)
    - assumptions used

Design Rules (v1)
-----------------
✔ Data-only
✔ Immutable
✔ No project / GUI / heat-loss imports
✔ No network topology required
✔ Safe to serialize + report
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class HydronicsDistributionResult:
    """
    Canonical distribution-layer result (v1).

    Represents early-stage distribution design outputs.
    """

    # ------------------------------------------------------------------
    # Thermal contract (input summary, not re-calculated here)
    # ------------------------------------------------------------------

    required_output_W: float
    """Total heat demand served by this distribution scope (W)."""

    design_deltaT_K: float
    """Chosen system water temperature drop across the scope (K)."""

    # ------------------------------------------------------------------
    # Derived hydraulic requirement (core "duct 1.5" output)
    # ------------------------------------------------------------------

    required_flow_rate_m3_s: float
    """Required volume flow rate (m³/s) to carry required_output_W at design_deltaT_K."""

    # ------------------------------------------------------------------
    # Budgets / targets (early stage)
    # ------------------------------------------------------------------

    target_velocity_m_s: Optional[float] = None
    """Design target velocity (m/s), if used."""

    target_dp_per_m_Pa_m: Optional[float] = None
    """Target pressure loss per metre (Pa/m), if used."""

    estimated_total_dp_Pa: Optional[float] = None
    """
    Early-stage estimate of total pressure drop (Pa) for the distribution scope.
    Can be derived later from an actual network, but useful as a budget now.
    """

    estimated_pump_head_m: Optional[float] = None
    """
    Early-stage estimate of pump head (m).
    If provided, should be consistent with estimated_total_dp_Pa and density.
    """

    # ------------------------------------------------------------------
    # Assumptions (must be explicit)
    # ------------------------------------------------------------------

    fluid_name: str = "water"
    """e.g. 'water', 'glycol_20pct' (string only, no coupling)."""

    density_kg_m3: Optional[float] = None
    """Fluid density assumption (kg/m³)."""

    kinematic_viscosity_m2_s: Optional[float] = None
    """Fluid kinematic viscosity assumption (m²/s)."""

    pipe_roughness_m: Optional[float] = None
    """Pipe roughness assumption (m)."""

    # ------------------------------------------------------------------
    # Identity (optional, for reporting)
    # ------------------------------------------------------------------

    scope_id: Optional[str] = None
    """Optional identifier, e.g. 'S1', 'ZoneA', 'Branch-01'."""

    notes: Optional[str] = None
    """Human-readable notes / warnings."""

    extra: Optional[Dict[str, float]] = None
    """
    Numeric-only extension bag (v1-safe).
    Examples:
        - diversity_factor
        - safety_margin_fraction
        - assumed_main_length_m
    """
