# ======================================================================
# HVAC/hydronics/physics/fittings_k_library_v1.py
# ======================================================================

"""
HVACgooee — Fittings K-Value Library v1
--------------------------------------

Authoritative loss coefficients (K-values) for common hydronic fittings.

RULES
-----
• Data only — no physics
• No unit conversions
• Stable identifiers
• Conservative defaults
• Educationally transparent
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


# ----------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FittingKValue:
    """
    Loss coefficient for a single fitting type.
    """
    fitting_id: str
    k_value: float
    description: str
    typical_application: str | None = None


# ----------------------------------------------------------------------
# Library (v1 defaults)
# ----------------------------------------------------------------------

FITTINGS_K_LIBRARY_V1: Dict[str, FittingKValue] = {

    # -------------------------------
    # Elbows
    # -------------------------------
    "ELBOW_90_STD": FittingKValue(
        fitting_id="ELBOW_90_STD",
        k_value=0.9,
        description="90° standard elbow",
        typical_application="General pipework",
    ),

    "ELBOW_90_LONG": FittingKValue(
        fitting_id="ELBOW_90_LONG",
        k_value=0.6,
        description="90° long-radius elbow",
        typical_application="Low-noise or low-loss runs",
    ),

    "BEND_90_SWEPT": FittingKValue(
        fitting_id="ELBOW_90_SWEPT",
        k_value=0.2,
        description="90° swept / formed bend",
        typical_application="Low-loss pipe routing",
    ),

    # -------------------------------
    # Tees
    # -------------------------------
    "TEE_THROUGH": FittingKValue(
        fitting_id="TEE_THROUGH",
        k_value=0.6,
        description="Tee fitting, straight-through flow",
    ),

    "TEE_BRANCH": FittingKValue(
        fitting_id="TEE_BRANCH",
        k_value=1.8,
        description="Tee fitting, branch flow",
    ),

    # -------------------------------
    # Valves
    # -------------------------------
    "GATE_VALVE": FittingKValue(
        fitting_id="GATE_VALVE",
        k_value=0.15,
        description="Fully open gate valve",
    ),

    "BALL_VALVE": FittingKValue(
        fitting_id="BALL_VALVE",
        k_value=0.05,
        description="Fully open ball valve",
    ),

    "CHECK_VALVE": FittingKValue(
        fitting_id="CHECK_VALVE",
        k_value=2.0,
        description="Spring-loaded check valve",
    ),

    # -------------------------------
    # Radiator controls
    # -------------------------------
    "TRV": FittingKValue(
        fitting_id="TRV",
        k_value=2.5,
        description="Thermostatic radiator valve (open)",
        typical_application="Radiator inlet",
    ),

    "LOCKSHIELD": FittingKValue(
        fitting_id="LOCKSHIELD",
        k_value=1.5,
        description="Lockshield valve (balanced)",
        typical_application="Radiator return",
    ),

    # --------------------------------------------------
    #
    # --------------------------------------------------



    # ...
}

# ----------------------------------------------------------------------
# Public helpers
# ----------------------------------------------------------------------

def get_fitting_k_value(fitting_id: str) -> float:
    """
    Return the K-value for a fitting.

    Raises KeyError if fitting_id is unknown.
    """
    return FITTINGS_K_LIBRARY_V1[fitting_id].k_value
