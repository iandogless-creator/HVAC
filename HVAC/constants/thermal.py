# HVAC/constants/thermal.py
"""
Thermal & Physical Constants (v1 — LOCKED)

Single source of truth for:
- Specific heat capacities
- Densities (where needed)
- Reference HVAC constants

NO calculations live here.
"""

# ------------------------------------------------------------------
# Specific Heat Capacity (J/kg·K)
# ------------------------------------------------------------------

SHC_WATER = 4180.0        # Liquid water (hydronics)
SHC_AIR = 1005.0          # Dry air @ ~20°C
SHC_STEAM = 2010.0        # (future use)

# ------------------------------------------------------------------
# Densities (kg/m³) — for ventilation / flow
# ------------------------------------------------------------------

DENSITY_WATER = 1000.0
DENSITY_AIR = 1.204       # @ 20°C, sea level

# ------------------------------------------------------------------
# HVAC reference constants
# ------------------------------------------------------------------

SECONDS_PER_HOUR = 3600.0
