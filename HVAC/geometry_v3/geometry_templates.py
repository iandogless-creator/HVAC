"""
HVACgooee — Geometry Templates (v3, v1-restricted)

Declarative enclosure templates that generate surfaces.

RULES (LOCKED — v1):
• Orthogonal rectangular rooms only
• Up to THREE corner cut-outs (intent only)
• No CAD
• No polygons
• No physics
• No surface subtraction (yet)

Corner cut-outs are declared intent and validated here.
They do NOT affect surface generation in v1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from HVAC.project_v3.project_models_v3 import SurfaceV3


# ---------------------------------------------------------------------
# Template identifiers (v1 scope)
# ---------------------------------------------------------------------

TemplateType = Literal[
    "RECT_0",  # rectangle
    "RECT_1",  # 1 corner cut-out
    "RECT_2",  # 2 corner cut-outs
    "RECT_3",  # 3 corner cut-outs
]


# ---------------------------------------------------------------------
# Parameter contract
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RectangularRoomParams:
    """
    Parameters for all v1 rectangular room templates.

    NOTE:
    corner_cutouts expresses INTENT only.
    Geometry subtraction is intentionally deferred.
    """

    length_m: float
    width_m: float
    height_m: float

    # Orientation is metadata only (no rotation here)
    orientation: str | None = None

    # v1: allowed values 0–3 only
    corner_cutouts: int = 0
