# ======================================================================
# HVAC/hydronics/emitter_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class EmitterV1:
    """
    Hydronics emitter DTO.

    Authority
    ---------
    • Belongs to ProjectState
    • Represents radiator / emitter intent
    • Does not perform hydronic calculation
    • Does not know about GUI
    """

    emitter_id: str
    room_id: str

    name: str = "Emitter"
    emitter_type: str = "radiator"

    design_output_W: Optional[float] = None
    flow_temp_C: Optional[float] = None
    return_temp_C: Optional[float] = None
    room_temp_C: Optional[float] = None

    notes: str = ""