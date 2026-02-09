# FILE: HVAC/heatloss/comfort_vs_compliance_module.py
"""
comfort_vs_compliance_module.py
HVACgooee — Comfort vs Compliance Thermal Module

Purpose
-------
This module provides two parallel assessments:

1. COMPLIANCE
   - Regulation-style assessment based mostly on:
       • U-values
       • Ventilation / infiltration
       • Glazing g-values
       • Simple peak heat-loss
       • Setpoints (°C)

2. COMFORT
   - Human comfort model based on:
       • Air temperature
       • Mean radiant temperature (MRT)
       • Thermal mass
       • Solar gains
       • Night cooling
       • Humidity & air movement (moderate approximations)

We keep BOTH models lightweight so they integrate easily with:
- heatloss_wizard.py
- energy_costs.py
- fenestration_advanced.py
- airflow_min_vent_requirements.py
- future room editor GUI

This is NOT a compliance engine. It is a design/comfort helper.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Literal


# ---------------------------------------------------------------------------
# TYPES & CONSTANTS
# ---------------------------------------------------------------------------

ThermalMassClass = Literal["low", "medium", "high"]

# Very simple “regulation target” U-values for building as a whole
DEFAULT_TARGET_MEAN_U = 0.25  # W/m²K, rough notional

# Ventilation benchmark (W/m²K equivalent) for "typical" tight dwelling
DEFAULT_VENT_W_M2K = 0.35

# Comfort “band” around setpoint (°C)
COMFORT_BAND = 2.0

# Humidity ideal band (fraction)
HUMIDITY_IDEAL_MIN = 0.40
HUMIDITY_IDEAL_MAX = 0.60


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class ComplianceInputs:
    """
    Inputs required for a regulation-style / compliance-oriented calculation.

    mean_U:
        Area-weighted average U-value for envelope (W/m²·K)

    ventilation_W_m2K:
        Effective ventilation heat loss coefficient (W/m²·K) per m² floor.
        This can be derived from ACH and volume, or a simple rule of thumb.

    delta_t:
        Winter design temperature difference (K)

    glazing_solar_gain_W_m2:
        W per m² of glazing per W/m² incident solar (effective g * shading)

    floor_area_m2:
        Total treated floor area (for normalisation).

    heating_setpoint:
        Indoor target temperature (°C)
    """
    mean_U: float
    ventilation_W_m2K: float
    delta_t: float
    glazing_solar_gain_W_m2: float
    floor_area_m2: float
    heating_setpoint: float = 21.0


@dataclass
class ComfortInputs:
    """
    Inputs for comfort model (room or zone).

    air_temp:
        Indoor air temperature (°C)

    radiant_temp:
        Mean radiant temperature (MRT) of surfaces (°C)

    thermal_mass:
        'low', 'medium', 'high' (affects smoothing, night stability)

    diurnal_range:
        Daily outdoor swing amplitude (°C). Higher = more stress.

    humidity:
        Relative humidity (0–1)

    air_speed:
        Local air speed (m/s). Higher can offset higher temperature slightly.

    clothing_clo:
        Clothing insulation (0.0 naked, 0.5 light, 1.0 winter).

    age_category:
        'adult' / 'older' / 'child' – older often prefer +1°C.
    """
    air_temp: float
    radiant_temp: float
    thermal_mass: ThermalMassClass
    diurnal_range: float
    humidity: float
    air_speed: float = 0.1
    clothing_clo: float = 0.7
    age_category: Literal["adult", "older", "child"] = "adult"


@dataclass
class ComplianceResult:
    passes: bool
    compliance_index: float  # 0–1 (1 = excellent)
    peak_heat_loss_W: float
    peak_heat_loss_W_m2: float
    mean_U: float
    ventilation_W_m2K: float
    notes: str

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class ComfortResult:
    comfort_index: float  # 0–1 (0 = perfect, 1 = very poor)
    pmv_like_score: float  # crude -3..+3 style indicator mapped to -1..+1
    operative_temp: float
    preferred_temp: float
    humidity_penalty: float
    radiant_asymmetry_penalty: float
    thermal_mass_bonus: float
    notes: str

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class CombinedAssessment:
    """
    Combined comfort + compliance overview for a room / zone / whole building.
    """
    compliance: ComplianceResult
    comfort: ComfortResult

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        return {
            "compliance": self.compliance.to_dict(),
            "comfort": self.comfort.to_dict(),
        }


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS — COMPLIANCE
# ---------------------------------------------------------------------------

def _compliance_index(mean_U: float, ventilation_W_m2K: float) -> float:
    """
    Simple 0–1 score based on how far we are from 'typical' targets.

    - 1.0 = much better than typical
    - 0.5 = around typical
    - 0.0 = very poor
    """
    # Compare mean U to target
    u_ratio = mean_U / DEFAULT_TARGET_MEAN_U if DEFAULT_TARGET_MEAN_U > 0 else 1.0
    # Ratio < 1 = good, >1 = bad
    if u_ratio <= 0.5:
        u_score = 1.0
    elif u_ratio >= 2.0:
        u_score = 0.0
    else:
        u_score = max(0.0, min(1.0, 1.0 - (u_ratio - 1.0) / 1.0))

    # Ventilation comparison
    if DEFAULT_VENT_W_m2K > 0:
        v_ratio = ventilation_W_m2K / DEFAULT_VENT_W_m2K
    else:
        v_ratio = 1.0

    if v_ratio <= 0.5:
        v_score = 1.0
    elif v_ratio >= 2.0:
        v_score = 0.0
    else:
        v_score = max(0.0, min(1.0, 1.0 - (v_ratio - 1.0) / 1.0))

    # Blend, weighting fabric a bit more than ventilation
    return 0.6 * u_score + 0.4 * v_score


def assess_compliance(inputs: ComplianceInputs) -> ComplianceResult:
    """
    Regulation-style assessment: rough "passes or not" notion and peak heat-loss.
    """
    H_fabric = inputs.mean_U * inputs.floor_area_m2
    H_vent = inputs.ventilation_W_m2K * inputs.floor_area_m2
    H_total = H_fabric + H_vent

    peak_heat_loss_W = H_total * inputs.delta_t
    peak_heat_loss_W_m2 = peak_heat_loss_W / max(inputs.floor_area_m2, 1e-6)

    comp_index = _compliance_index(inputs.mean_U, inputs.ventilation_W_m2K)
    passes = comp_index >= 0.5  # arbitrary threshold – "around notional target"

    note_bits = []
    if inputs.mean_U <= DEFAULT_TARGET_MEAN_U:
        note_bits.append("Fabric U-value at or better than notional target.")
    else:
        note_bits.append("Fabric U-value worse than notional target.")

    if inputs.ventilation_W_m2K <= DEFAULT_VENT_W_m2K:
        note_bits.append("Ventilation heat loss typical or better.")
    else:
        note_bits.append("Ventilation / infiltration on high side.")

    note_bits.append(
        f"Peak heat-loss ≈ {peak_heat_loss_W_m2:.1f} W/m² at ΔT={inputs.delta_t:.1f} K."
    )

    notes = " ".join(note_bits)

    return ComplianceResult(
        passes=passes,
        compliance_index=comp_index,
        peak_heat_loss_W=peak_heat_loss_W,
        peak_heat_loss_W_m2=peak_heat_loss_W_m2,
        mean_U=inputs.mean_U,
        ventilation_W_m2K=inputs.ventilation_W_m2K,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS — COMFORT
# ---------------------------------------------------------------------------

def _preferred_temp_from_clothing_and_age(
    base_setpoint: float,
    clothing_clo: float,
    age_category: str,
) -> float:
    """
    Very simple comfort uplift logic (mirrors airflow_min_vent_requirements ComfortProfile).
    """
    clothing_adj = 0.0
    if clothing_clo < 0.3:
        clothing_adj = 2.0  # almost naked
    elif clothing_clo < 0.5:
        clothing_adj = 1.0
    elif clothing_clo > 1.0:
        clothing_adj = -1.0

    age_adj = 0.0
    if age_category == "older":
        age_adj = 1.0

    preferred = base_setpoint + clothing_adj + age_adj
    return max(18.0, min(26.0, preferred))


def _thermal_mass_bonus(thermal_mass: ThermalMassClass, diurnal_range: float) -> float:
    """
    Provide a bonus (negative penalty) for heavy mass, especially when diurnal
    range is high.
    """
    base = 0.0
    if thermal_mass == "low":
        base = 0.0
    elif thermal_mass == "medium":
        base = -0.05
    else:  # high
        base = -0.10

    if diurnal_range > 10.0 and thermal_mass == "high":
        base -= 0.05

    return base


def _humidity_penalty(humidity: float) -> float:
    """
    0–1 penalty for being outside 40–60 % RH.
    """
    h = max(0.0, min(1.0, humidity))

    if HUMIDITY_IDEAL_MIN <= h <= HUMIDITY_IDEAL_MAX:
        return 0.0

    if h < HUMIDITY_IDEAL_MIN:
        # Too dry
        diff = HUMIDITY_IDEAL_MIN - h  # up to 0.4
    else:
        # Too humid
        diff = h - HUMIDITY_IDEAL_MAX  # up to 0.4

    # Map 0–0.4 → 0–0.3
    return max(0.0, min(0.3, diff * (0.3 / 0.4)))


def _radiant_asymmetry_penalty(air: float, mrt: float) -> float:
    """
    Penalty for MRT being far below air temperature (cold surfaces).
    """
    diff = air - mrt  # positive if air > MRT
    if diff <= 1.0:
        return 0.0
    if diff >= 6.0:
        return 0.4
    # Map 1–6 K -> 0–0.4
    return (diff - 1.0) * (0.4 / 5.0)


def assess_comfort(
    inputs: ComfortInputs,
    base_setpoint: float = 21.0,
) -> ComfortResult:
    """
    Lightweight comfort assessment.

    Returns:
      - comfort_index 0–1 (0 = perfect, 1 = very poor)
      - pmv_like_score (crude -1..+1)
      - various penalty components
    """
    operative_temp = 0.5 * (inputs.air_temp + inputs.radiant_temp)

    preferred_temp = _preferred_temp_from_clothing_and_age(
        base_setpoint=base_setpoint,
        clothing_clo=inputs.clothing_clo,
        age_category=inputs.age_category,
    )

    # Temperature deviation
    temp_diff = operative_temp - preferred_temp

    # Convert temp_diff into a crude PMV-like range [-1, 1]
    # where ±3°C ≈ ±1
    pmv_like = max(-1.0, min(1.0, temp_diff / 3.0))

    # Base discomfort from temperature
    if abs(temp_diff) <= COMFORT_BAND:
        temp_penalty = 0.0
    elif abs(temp_diff) >= 6.0:
        temp_penalty = 0.6
    else:
        temp_penalty = (abs(temp_diff) - COMFORT_BAND) * (0.6 / (6.0 - COMFORT_BAND))

    # Humidity + radiant penalties
    hum_pen = _humidity_penalty(inputs.humidity)
    rad_pen = _radiant_asymmetry_penalty(inputs.air_temp, inputs.radiant_temp)

    # Thermal mass bonus (negative penalty)
    mass_bonus = _thermal_mass_bonus(inputs.thermal_mass, inputs.diurnal_range)

    # Air speed small relief (e.g. fan)
    air_speed_relief = 0.0
    if inputs.air_speed > 0.15:
        air_speed_relief = -0.05
    if inputs.air_speed > 0.3:
        air_speed_relief = -0.10

    # Aggregate comfort index
    raw_index = temp_penalty + hum_pen + rad_pen + mass_bonus + air_speed_relief

    comfort_index = max(0.0, min(1.0, raw_index))

    note_bits = []
    if temp_diff > 1.0:
        note_bits.append("Room tends warm relative to preferred.")
    elif temp_diff < -1.0:
        note_bits.append("Room tends cool relative to preferred.")
    else:
        note_bits.append("Temperature close to preferred comfort.")

    if hum_pen > 0.0:
        note_bits.append("Humidity outside ideal 40–60% band.")

    if rad_pen > 0.1:
        note_bits.append("Cold surfaces (MRT below air temp) may be felt.")

    if mass_bonus < 0.0:
        note_bits.append("High thermal mass provides beneficial smoothing.")

    if inputs.air_speed > 0.15:
        note_bits.append("Air movement provides slight cooling relief.")

    notes = " ".join(note_bits)

    return ComfortResult(
        comfort_index=comfort_index,
        pmv_like_score=pmv_like,
        operative_temp=operative_temp,
        preferred_temp=preferred_temp,
        humidity_penalty=hum_pen,
        radiant_asymmetry_penalty=rad_pen,
        thermal_mass_bonus=mass_bonus,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# COMBINED VIEW
# ---------------------------------------------------------------------------

def combined_assessment(
    compliance_inputs: ComplianceInputs,
    comfort_inputs: ComfortInputs,
) -> CombinedAssessment:
    """
    Convenience function that runs both compliance and comfort and returns
    a combined summary object.
    """
    comp = assess_compliance(compliance_inputs)
    conf = assess_comfort(comfort_inputs, base_setpoint=compliance_inputs.heating_setpoint)
    return CombinedAssessment(compliance=comp, comfort=conf)


# ---------------------------------------------------------------------------
# SELF-TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== HVACgooee — Comfort vs Compliance Module Demo ===")

    ci = ComplianceInputs(
        mean_U=0.24,
        ventilation_W_m2K=0.35,
        delta_t=22.0,
        glazing_solar_gain_W_m2=0.5,
        floor_area_m2=120.0,
        heating_setpoint=21.0,
    )

    ki = ComfortInputs(
        air_temp=23.0,
        radiant_temp=21.0,
        thermal_mass="high",
        diurnal_range=8.0,
        humidity=0.45,
        air_speed=0.1,
        clothing_clo=0.3,      # very light clothing
        age_category="older",  # comfort uplift ~+1°C
    )

    combined = combined_assessment(ci, ki)

    print("Compliance:", combined.compliance)
    print("Comfort:", combined.comfort)
