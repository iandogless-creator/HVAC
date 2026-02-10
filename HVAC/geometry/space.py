# ================================================================
# BEGIN MODULE: space.py (Modern + TEI/t_ai-aware Ventilation)
# ================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Space:
    """
    HVACgooee — Space Model v1.4

    Temperature model:

        • design_temp_C
            Modern design internal temperature (T_design).
            This is ALWAYS what modern fabric heat-loss uses.

        • TEI / t_ai
            Optional environmental method:
                TEI  = environmental comfort target (°C)
                t_ai = calculated internal air temperature (°C)

            t_ai is computed externally (tei_tai_tools.compute_tai_C)
            and stored in tai_C when TEI is enabled for this space.

        • Ventilation
            Ventilation normally uses T_design.
            If use_tai_for_ventilation is True and tai_C is available,
            ventilation ΔT uses (t_ai - t_ao) instead.
    """

    # ------------------------------------------------------------
    # Basic Geometry
    # ------------------------------------------------------------
    name: str
    floor_area_m2: float
    height_m: float
    vertices: List[tuple[float, float]] = field(default_factory=list)

    # ------------------------------------------------------------
    # Modern Design Temperature (always used for fabric)
    # ------------------------------------------------------------
    use_project_default_temp: bool = True
    design_temp_C: float = 21.0          # T_design
    delta_T: Optional[float] = None      # computed in HeatLossController

    # ------------------------------------------------------------
    # Optional TEI / t_ai Environmental Method
    # ------------------------------------------------------------
    # When True, this space participates in TEI/t_ai calculation
    # and can display TEI / t_ai in the modern UI.
    enable_tei: bool = False

    # Optional explicit TEI override for this room.
    # If None, TEI will be resolved from HVAC.project.
 default or design_temp_C.
    tei_C: Optional[float] = None

    # Calculated internal air temperature (t_ai, °C) from TEI method.
    # This is filled by the controller / environmental helper,
    # never directly edited by the user.
    tai_C: Optional[float] = None

    # If True and tai_C is not None, ventilation requirements
    # for this space will use (t_ai - t_ao) instead of
    # (design_temp_C - t_ao).
    use_tai_for_ventilation: bool = False

    # ------------------------------------------------------------
    # Ventilation Metadata (inputs; passive until engine uses them)
    # ------------------------------------------------------------
    include_ventilation_loss: bool = False
    ach: float = 0.5                # air changes per hour
    custom_airflow_m3h: float = 0.0 # optional override, m³/h

    # ------------------------------------------------------------
    # Comfort Metadata (for modern comfort / PMV later, not legacy)
    # ------------------------------------------------------------
    use_project_clo: bool = True
    clo: float = 1.0
    use_project_met: bool = True
    met: float = 1.1

    # ------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------
    space_type: str = "generic"
    notes: str = ""

    # ------------------------------------------------------------
    # Derived geometry
    # ------------------------------------------------------------
    @property
    def volume_m3(self) -> float:
        """Simple volume = area × height. Complex geometry handled later."""
        return self.floor_area_m2 * self.height_m

# ================================================================
# END MODULE
# ================================================================
