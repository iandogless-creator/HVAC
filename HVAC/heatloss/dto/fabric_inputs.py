# ======================================================================
# HVAC/heatloss/dto/fabric_inputs.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


# ----------------------------------------------------------------------
# Per-surface input (authoritative)
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FabricSurfaceInputDTO:
    """
    Phase II-A — Fabric surface input

    Represents ONE declared fabric heat-loss participant.

    This DTO is purely declarative.
    No inference, no defaults, no geometry logic.
    """

    surface_id: str
    room_id: str

    surface_class: str
    """
    Examples (non-exhaustive):
        - "external_wall"
        - "roof"
        - "ground_floor"
        - "window"
        - "door"

    Interpretation is engine-owned.
    Controller does not branch on this.
    """

    area_m2: float
    u_value_W_m2K: float

    delta_t_K: float
    """
    Reference temperature difference:
        ΔT = Ti - Te

    Must be strictly positive.
    If <= 0, execution must fail upstream.
    """


# ----------------------------------------------------------------------
# Engine input container
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FabricHeatLossInputDTO:
    """
    Phase II-A — Fabric heat-loss engine input (CANONICAL)

    Contains ALL fabric transmission intent for a project.
    """

    surfaces: List[FabricSurfaceInputDTO]

    internal_design_temp_C: float
    external_design_temp_C: float

    """
    These are included for traceability and reporting only.
    Engines must NOT recompute ΔT from them.
    """

    project_id: str | None = None