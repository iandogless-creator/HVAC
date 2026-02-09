# ======================================================================
# HVAC/hydronics/adapters/sized_pipe_to_dto_v1.py
# ======================================================================

"""
HVACgooee — Sized Pipe Segment → Pipe Sizing DTO Adapter v1
-----------------------------------------------------------

Pure translation layer from domain sizing objects to GUI-facing DTOs.

RULES
-----
• NO calculations
• NO mutation
• NO GUI imports
• NO inference

All numeric values must already be resolved by engines.
"""

from __future__ import annotations

from typing import Optional

from HVAC_legacy.hydronics.pipes.models.sized_pipe_segment_v1 import (
    SizedPipeSegmentV1,
)
from HVAC_legacy.hydronics.dto.pipe_sizing_dto_v1 import (
    PipeSizingDTOv1,
)


def build_pipe_sizing_dto_v1(
    *,
    segment: SizedPipeSegmentV1,
    segment_id: str,
    leg_id: Optional[str] = None,
    subleg_id: Optional[str] = None,
    subleg_flow_kg_s: Optional[float] = None,
    subleg_dn_mm: Optional[int] = None,
    leg_flow_kg_s: Optional[float] = None,
    leg_dn_mm: Optional[int] = None,
) -> PipeSizingDTOv1:
    """
    Build a PipeSizingDTOv1 from a SizedPipeSegmentV1.

    Parameters
    ----------
    segment:
        Domain-sized pipe segment (authoritative).

    segment_id:
        Stable identifier used by GUI / reports.

    leg_id:
        Optional parent leg identifier.

    subleg_id:
        Optional sub-leg identifier (branch context).

    subleg_flow_kg_s / subleg_dn_mm:
        Branch-level flow and governing DN.
        Must be supplied explicitly by caller if required.

    leg_flow_kg_s / leg_dn_mm:
        Full leg flow and governing DN.
        Must be supplied explicitly by caller if required.

    Returns
    -------
    PipeSizingDTOv1
        GUI-facing sizing representation.
    """

    return PipeSizingDTOv1(
        # ------------------------------------------------------------
        # Identity / context
        # ------------------------------------------------------------
        segment_id=segment_id,
        leg_id=leg_id,
        subleg_id=subleg_id,

        # ------------------------------------------------------------
        # Local segment
        # ------------------------------------------------------------
        flow_rate_kg_s=segment.flow_kg_s,
        selected_pipe_dn_mm=segment.dn_mm,

        # ------------------------------------------------------------
        # Accumulated (upstream at this segment)
        # ------------------------------------------------------------
        accumulated_flow_rate_kg_s=segment.accumulated_flow_kg_s,
        required_pipe_dn_mm=segment.accumulated_dn_mm,

        # ------------------------------------------------------------
        # Sub-leg context (optional)
        # ------------------------------------------------------------
        subleg_flow_rate_kg_s=subleg_flow_kg_s,
        subleg_pipe_dn_mm=subleg_dn_mm,

        # ------------------------------------------------------------
        # Full leg context (optional)
        # ------------------------------------------------------------
        leg_flow_rate_kg_s=leg_flow_kg_s,
        leg_pipe_dn_mm=leg_dn_mm,
    )
