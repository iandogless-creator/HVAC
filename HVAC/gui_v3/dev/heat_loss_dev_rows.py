# ======================================================================
# HVAC/gui_v3/dev/heat_loss_dev_rows.py
# ======================================================================
# DEV — Heat-Loss Worksheet Bootstrap Rows
# Status: TEMPORARY (Phase F)
# ======================================================================

from HVAC.gui_v3.dto.heat_loss_worksheet_row_dto import (
    HeatLossWorksheetRowDTO,
)


def build_dev_rows(*, room_id: str) -> list[HeatLossWorksheetRowDTO]:
    """
    DEV-ONLY worksheet bootstrap rows.

    Purpose
    -------
    • Provide visible worksheet content
    • Enable HLPE click → overlay → cancel/apply spine
    • Prove non-positional signal routing

    Rules
    -----
    • No ProjectState mutation
    • No calculations
    • Deterministic values
    • REMOVE once engine produces real worksheet rows
    """

    return [
        HeatLossWorksheetRowDTO(
            room_id=room_id,
            element_id="dev-wall-001",
            element_name="External Wall",
            area_m2=12.00,
            delta_t_k=20.0,
            u_value_w_m2k=0.35,
            qf_w=84.0,  # visually plausible, NOT authoritative
        )
    ]
