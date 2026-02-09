from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class HeatLossPreviewDTO:
    # ------------------------------------------------------------------
    # Room context
    # ------------------------------------------------------------------
    room_name: Optional[str]

    ti_c: Optional[float]
    to_c: Optional[float]

    # ------------------------------------------------------------------
    # Fabric
    # ------------------------------------------------------------------
    construction_refs: Optional[str]
    u_value_w_m2k: Optional[float]

    # ------------------------------------------------------------------
    # Ventilation
    # ------------------------------------------------------------------
    ach_1_h: Optional[float]

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    heat_loss_w: Optional[float]

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    state: str
    # Expected values:
    # "NO_ROOM"
    # "MISSING_INTENT"
    # "READY_TO_RUN"
    # "STALE"
    # "UP_TO_DATE"
