# ======================================================================
# HVACgooee — Heat-Loss Derived Metrics Constants (v1 LOCKED)
# ======================================================================

"""
Derived Metrics Constants (v1)

This module is the SINGLE source of truth for
all heat-loss derived metric constants.

⚠️ CONTRACT LOCK
- Do NOT redefine these numbers elsewhere
- Do NOT inline magic numbers in GUI or engines
- Changes require v2 discussion

Engineering lineage:
- CIBSE steady-state educational heuristics
- Used for interpretation, NOT sizing physics
"""

# ----------------------------------------------------------------------
# Global constants
# ----------------------------------------------------------------------

#: Comfort divisor used in Cv calculation (legacy educational constant)
CV_DIVISOR: float = 4.8

# ----------------------------------------------------------------------
# Availability flags (semantic, not numeric)
# ----------------------------------------------------------------------

#: Ce requires exposure / envelope model
CE_REQUIRES_EXPOSURE_MODEL: bool = True
