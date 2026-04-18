# ======================================================================
# HVAC/heatloss/dto/fabric_surface_row_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


@dataclass(slots=True)
class FabricSurfaceRowV1:
    """
    Canonical fabric row used by:

    • FabricFromSegmentsV1 (builder)
    • HeatLossPanelAdapter (projection)
    • Engines (read-only)

    Notes
    -----
    • Physics fields are authoritative inputs to engines
    • parent_surface_id is UI-only (hierarchy)
    """

    # --------------------------------------------------
    # Identity
    # --------------------------------------------------
    surface_id: str
    room_id: str

    # --------------------------------------------------
    # Classification
    # --------------------------------------------------
    element: str

    # --------------------------------------------------
    # Physics inputs
    # --------------------------------------------------
    area_m2: float
    u_value_W_m2K: Optional[float]
    delta_t_K: Optional[float]

    # --------------------------------------------------
    # Result (optional pre-calc)
    # --------------------------------------------------
    qf_W: Optional[float]

    # --------------------------------------------------
    # Construction
    # --------------------------------------------------
    construction_id: Optional[str]

    # --------------------------------------------------
    # Phase IV-D — hierarchy (UI only)
    # --------------------------------------------------
    parent_surface_id: Optional[str] = None
    _segment: Optional[BoundarySegmentV1] = None
