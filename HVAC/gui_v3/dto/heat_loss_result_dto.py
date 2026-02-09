from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HeatLossResultDTO:
    room_id: str
    total_heat_loss_w: float | None = None
    valid: bool = False
    calculation_version: str | None = None
