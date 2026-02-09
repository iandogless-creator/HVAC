"""
hydronics_to_pipes_v1.py
-----------------------

HVACgooee — Hydronics → Pipe sizing adapter (v1)

This module provides the ONLY legal handover from hydronics
payloads into the pipe sizing engine.

Rules:
• Pipes never import hydronics
• Hydronics engines never import heat-loss
• This adapter translates domain objects → numbers
"""

from __future__ import annotations

from HVAC_legacy.hydronics.hydronics_payload_v1 import HydronicsPayloadV1
from HVAC_legacy.hydronics.pipe_sizing_solver_v1 import (
    size_pipe_for_flow,
    PipeSizingResult,
)


def size_pipe_from_hydronics(
    hydronics: HydronicsPayloadV1,
    *,
    max_velocity_m_s: float = 0.8,
) -> PipeSizingResult:
    """
    Size a pipe based on a hydronics payload.

    Parameters
    ----------
    hydronics:
        HydronicsPayloadV1 containing design volume flow

    max_velocity_m_s:
        Maximum allowable velocity [m/s]

    Returns
    -------
    PipeSizingResult
    """

    return size_pipe_for_flow(
        volume_flow_m3_h=hydronics.volume_flow_m3_h,
        max_velocity_m_s=max_velocity_m_s,
    )
