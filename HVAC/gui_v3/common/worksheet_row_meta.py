# ======================================================================
# HVAC/gui_v3/common/worksheet_row_meta.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict


# ======================================================================
# WorksheetCellMeta
# ======================================================================

@dataclass(slots=True)
class WorksheetCellMeta:
    """
    Metadata for a single editable/display cell.
    """

    field: Optional[str]          # e.g. "A", "U"
    editable: bool
    kind: str                     # "cell" | "readonly" | "derived"


# ======================================================================
# WorksheetRowMeta
# ======================================================================

@dataclass(slots=True)
class WorksheetRowMeta:
    """
    Metadata for a worksheet row (canonical UI contract).
    """

    surface_id: str
    element: str

    # --------------------------------------------------
    # Validation state (IV-C)
    # --------------------------------------------------
    state: str = "GREEN"          # GREEN | ORANGE | RED
    message: Optional[str] = None

    # --------------------------------------------------
    # Adjacency (IV-D)
    # --------------------------------------------------
    adjacency_editable: bool = False

    # --------------------------------------------------
    # Column definitions
    # --------------------------------------------------
    columns: Dict[int, WorksheetCellMeta] = field(default_factory=dict)