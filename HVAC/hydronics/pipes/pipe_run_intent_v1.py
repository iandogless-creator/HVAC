# ======================================================================
# HVAC/hydronics/pipes/pipe_run_intent_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class PipeRunIntentV1:
    """
    Declarative hydronic pipe-run intent.

    Authority
    ---------
    • Represents pipe intent derived from hydronic skeleton legs
    • No pipe sizing
    • No pressure loss
    • No velocity calculation
    • No pump calculation
    """

    pipe_run_id: str
    leg_id: str
    from_node_id: str
    to_node_id: str
    circuit_type: str  # "supply" | "return"

    length_m: Optional[float] = None
    material_id: Optional[str] = None
    nominal_diameter_mm: Optional[float] = None
    notes: str = ""
