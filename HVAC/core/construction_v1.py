# ======================================================================
# HVAC/core/construction_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConstructionV1:
    """
    Phase V-A Construction Authority

    • Defines thermal transmittance (U-value)
    • Single source of truth for U
    • Referenced by surfaces via construction_id
    """

    construction_id: str
    name: str
    u_value_W_m2K: float