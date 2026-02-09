from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HeatLossIntentDTO:
    room_id: str
    participates: bool = True
    design_internal_temp_c: float | None = None
    intent_complete: bool = False
