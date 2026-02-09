"""
heatloss_labels.py
------------------

HVACgooee — Canonical Heat-Loss Symbols & Labels (GUI v2)

This file is the SINGLE SOURCE OF TRUTH for:
- Column headings
- Total labels
- Mathematical symbols

NO GUI logic
NO calculations
"""

# -----------------------------
# Table column headers
# -----------------------------

COL_ELEMENT = "Element"
COL_AREA = "Area (m²)"
COL_U = "U (W/m²·K)"
COL_U_SOURCE = "U Source"
COL_TB = "Tᵦ (°C)"
COL_DT = "ΔT (K)"
COL_QT = "Qt (W)"          # ← per-element heat flow

TABLE_HEADERS = [
    COL_ELEMENT,
    COL_AREA,
    COL_U,
    COL_U_SOURCE,
    COL_TB,
    COL_DT,
    COL_QT,
]

# -----------------------------
# Totals & summaries
# -----------------------------

LABEL_VENT_LOSS = "Ventilation heat loss:"
LABEL_FABRIC_TOTAL = "Fabric total:"
LABEL_SUM_QT = "ΣQt:"      # ← SUM of ALL heat losses

UNIT_W = "W"

# -----------------------------
# Physical constants (v1)
# -----------------------------

# Used for Cv derivation (legacy / educational)
DELTA_T_STANDARD = 4.8
