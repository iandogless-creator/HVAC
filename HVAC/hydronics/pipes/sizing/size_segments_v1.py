# ======================================================================
# HVAC/hydronics/pipes/sizing/size_segments_v1.py
# ======================================================================

"""
HVACgooee — Pipe Sizing Adapter v1
---------------------------------

Contract adapter that bridges:
    PipeSegmentV1  →  SizedPipeSegmentV1

This module:
• Enforces the sizing I/O contract
• Adapts PipeSegmentV1 to legacy sizing internals
• Prevents mutation of authoritative inputs
• Returns DTOs only

NO physics is implemented here.
NO legacy code is modified here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from HVAC_legacy.hydronics.pipes.dto.pipe_segment_v1 import PipeSegmentV1
from HVAC_legacy.hydronics.pipes.dto.sized_pipe_segment_v1 import SizedPipeSegmentV1


# ----------------------------------------------------------------------
# Configuration DTO (minimal placeholder)
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SizingRulesV1:
    """
    Configuration for pipe sizing.

    This is intentionally minimal and may be expanded later
    without changing the adapter signature.
    """
    sizing_method: str
    max_velocity_m_s: Optional[float] = None
    max_dp_pa_per_m: Optional[float] = None


# ----------------------------------------------------------------------
# Public Adapter API
# ----------------------------------------------------------------------

def size_segments_v1(
    *,
    segments: List[PipeSegmentV1],
    rules: SizingRulesV1,
) -> List[SizedPipeSegmentV1]:
    """
    Size pipe segments using legacy or modern sizing logic
    via an adapter layer.

    PARAMETERS
    ----------
    segments:
        List of PipeSegmentV1 (authoritative, immutable).

    rules:
        SizingRulesV1 defining limits and method.

    RETURNS
    -------
    List[SizedPipeSegmentV1]

    NOTES
    -----
    • This function MUST NOT mutate inputs.
    • One output is returned per input segment.
    • Deterministic for identical inputs + rules.
    """

    if not segments:
        return []

    results: List[SizedPipeSegmentV1] = []

    for seg in segments:
        # --------------------------------------------------------------
        # Guardrails
        # --------------------------------------------------------------
        if seg.design_flow_lps <= 0.0:
            raise RuntimeError(
                f"Invalid design flow for segment '{seg.segment_id}'."
            )

        if seg.length_m <= 0.0:
            raise RuntimeError(
                f"Invalid length for segment '{seg.segment_id}'."
            )

        # --------------------------------------------------------------
        # ADAPT INPUT → legacy sizing call
        # --------------------------------------------------------------
        #
        # TODO:
        #   • Convert seg to the form expected by legacy sizing code
        #   • Call existing sizing logic
        #   • Capture results WITHOUT mutating seg
        #
        # Example placeholders below:
        #

        # --- BEGIN PLACEHOLDER ---
        nominal_dn_mm = 0.0
        internal_d_mm = 0.0
        velocity_m_s = 0.0
        reynolds = 0.0
        friction_factor = 0.0
        dp_pa_per_m = 0.0
        # --- END PLACEHOLDER ---

        # --------------------------------------------------------------
        # Build DTO result (OUTPUT ONLY)
        # --------------------------------------------------------------
        results.append(
            SizedPipeSegmentV1(
                segment_id=seg.segment_id,
                leg_id=seg.leg_id,
                nominal_diameter_mm=nominal_dn_mm,
                internal_diameter_mm=internal_d_mm,
                velocity_m_s=velocity_m_s,
                reynolds_number=reynolds,
                friction_factor=friction_factor,
                pressure_drop_Pa_per_m=dp_pa_per_m,
                sizing_method=rules.sizing_method,
            )
        )

    return results
