# ======================================================================
# HVAC/hydronics_v3/enums/hydronic_system_type.py
# ======================================================================

from __future__ import annotations
from enum import Enum


class HydronicSystemType(Enum):
    """
    Declared hydronic emitter system type.

    NO physics.
    Used for intent + downstream selection only.
    """

    RADIATORS = "radiators"
    UFH = "underfloor_heating"
    FAN_COILS = "fan_coils"
