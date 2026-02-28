# ======================================================================
# HVAC/heatloss/dto/vent_inputs.py
# ======================================================================

"""
HVACgooee — Phase II-B DTOs (Ventilation Inputs, ACH-only)

Status: SKELETON (FIELDS NOT YET WIRED)
Purpose:
- Provide a stable import target for HeatLossControllerV4 wiring.
- Phase II-B current uses ACH-only input basis.

No physics lives here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VentilationACHInputDTO:
    """
    Phase II-B (ACH-only) input DTO.

    Fields will be added when wiring ProjectState -> DTO builders.
    """
    pass