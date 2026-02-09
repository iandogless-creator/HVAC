from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class HeatLossEngineResult:
    """
    Canonical heat-loss engine output.

    Authoritative for downstream systems.
    """

    # ---- Totals (authoritative) ----
    total_heat_loss_w: float

    # ---- Optional breakdowns (education / reporting) ----
    fabric_heat_loss_w: Optional[float] = None
    ventilation_heat_loss_w: Optional[float] = None

    # ---- Optional per-element detail ----
    elements: Optional[list] = None
