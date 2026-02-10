# ======================================================================
# HVAC/hydronics/adapters/valve_location_adapter_v1.py
# ======================================================================

"""
HVACgooee — Valve Location Hydraulics Adapter v1
------------------------------------------------

Extracts hydraulics at the lockshield valve location
(last pipe segment on terminal leg).

Pure adapter. No mutation.
"""

from __future__ import annotations

from typing import Dict

from HVAC.hydronics.balancing.engines.balancing_engine_v1 import (
    ValveLocationHydraulicsV1,
)
from HVAC.hydronics.legs.models.committed_leg_geometry_v1 import (
    CommittedLegGeometryV1,
)
from HVAC.hydronics.pipes.models.sized_pipe_segment_v1 import (
    SizedPipeSegmentV1,
)


def extract_valve_hydraulics_v1(
    terminal_leg_geometries: Dict[str, CommittedLegGeometryV1],
    sized_pipe_segments: Dict[str, SizedPipeSegmentV1],
) -> Dict[str, ValveLocationHydraulicsV1]:
    """
    Determine valve hydraulics for each terminal leg.

    Rule:
    - Use the LAST pipe segment in the terminal leg geometry.
    """

    result: Dict[str, ValveLocationHydraulicsV1] = {}

    for terminal_id, geom in terminal_leg_geometries.items():
        if not geom.segments:
            continue

        last_seg_id = geom.segments[-1]
        seg = sized_pipe_segments.get(last_seg_id)

        if seg is None:
            continue

        result[terminal_id] = ValveLocationHydraulicsV1(
            dn_mm=seg.dn_mm,
            rho_kg_m3=seg.rho_kg_m3,
            v_m_s=seg.velocity_m_s,
        )

    return result
