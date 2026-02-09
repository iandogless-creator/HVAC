# ======================================================================
# HVAC/hydronics_v3/tests/validation/example_a_steel_25mm_1972_dataset_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List


EXAMPLE_ID = "HIVE_1972_STEEL_25MM_EXAMPLE_A_V1"

# Water @ 75°C (engineering constants, LOCKED for this validation)
RHO_WATER_75C_KG_M3 = 977.8       # approx
MU_WATER_75C_PA_S = 0.000382      # approx (dynamic viscosity)

# Heavy grade steel roughness (order-of-magnitude standard engineering value)
EPS_STEEL_M = 4.5e-5              # 0.045 mm

# Nominal 25 mm heavy grade steel: typical internal diameter ~ 20–21 mm.
# We lock an assumed ID so the test is deterministic.
PIPE_ID_M = 0.0210

# Legacy reference points extracted from user-provided scan (Table C4.11, HIVE-era)
# Interpreting:
#   Q_l_s  = flow (L/s)
#   v_m_s  = velocity (m/s) shown in the table (approx)
#   dp_pa_m = Δpᵢ (Pa/m) shown in the right column (approx)
@dataclass(frozen=True, slots=True)
class LegacyPoint:
    q_l_s: float
    v_m_s: float
    dp_pa_m: float


LEGACY_POINTS: List[LegacyPoint] = [
    LegacyPoint(q_l_s=0.262, v_m_s=0.9, dp_pa_m=140.0),
    LegacyPoint(q_l_s=0.300, v_m_s=1.0, dp_pa_m=180.0),
    LegacyPoint(q_l_s=0.334, v_m_s=1.0, dp_pa_m=220.0),
]

# Tolerances (LOCKED)
# Table values are rounded + table method details unknown (minor loss assumptions, exact ID, exact μ, etc.)
VEL_REL_TOL = 0.12      # ±12%
DP_REL_TOL = 0.18       # ±18%
