# ======================================================================
# HVAC/hydronics/dto/pipe_sizing_dto_v1.py
# ======================================================================

"""
HVACgooee — Pipe Sizing DTO v1
------------------------------

GUI-facing representation of pipe sizing data derived from
SizedPipeSegmentV1 and related aggregation context.

This DTO contains:
- Local segment sizing
- Accumulated (upstream) requirements
- Sub-leg context
- Full leg context

NO calculations
NO engine imports
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class PipeSizingDTOv1:
    """
    Canonical pipe sizing presentation object (v1).

    All values are pre-calculated by domain engines.
    This object exists purely for display, reporting, and export.
    """

    # ------------------------------------------------------------
    # Identity / context
    # ------------------------------------------------------------
    segment_id: str
    leg_id: Optional[str] = None
    subleg_id: Optional[str] = None

    # ------------------------------------------------------------
    # Local segment (this segment only)
    # ------------------------------------------------------------
    flow_rate_kg_s: float
    selected_pipe_dn_mm: int

    # ------------------------------------------------------------
    # Accumulated (upstream at this segment)
    # ------------------------------------------------------------
    accumulated_flow_rate_kg_s: float
    required_pipe_dn_mm: int

    # ------------------------------------------------------------
    # Sub-leg context (branch-level)
    # ------------------------------------------------------------
    subleg_flow_rate_kg_s: Optional[float] = None
    subleg_pipe_dn_mm: Optional[int] = None

    # ------------------------------------------------------------
    # Full leg context (terminal → index)
    # ------------------------------------------------------------
    leg_flow_rate_kg_s: Optional[float] = None
    leg_pipe_dn_mm: Optional[int] = None
