from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class EmitterType(str, Enum):
    RADIATOR = "radiator"
    UFH = "underfloor_heating"


@dataclass(slots=True)
class EmitterV1:
    """
    Declarative emitter definition (no sizing).
    """

    terminal_id: str
    emitter_type: EmitterType

    # Design intent (not results)
    design_dt_k: float = 20.0          # ΔT50 for rads, ΔT5–10 for UFH later
    notes: str | None = None
