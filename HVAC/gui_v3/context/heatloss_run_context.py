# HVAC/gui_v3/context/heatloss_run_context.py

from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class HeatLossRunContext:
    internal_design_temp_C: Optional[float] = None