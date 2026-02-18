# ======================================================================
# HVACgooee — Heat-Loss Worksheet Row DTO (GUI v3)
# ======================================================================

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HeatLossWorksheetRowDTO:
    """
    GUI-only worksheet row representation.

    Purpose
    -------
    • Populate Heat-Loss worksheet table
    • Act as HLPE interaction substrate
    • NEVER authoritative
    """

    # Identity
    room_id: str
    element_id: str
    element_name: str

    # Display values (pre-run or post-run)
    area_m2: float
    delta_t_k: float
    u_value_w_m2k: float
    qf_w: float
