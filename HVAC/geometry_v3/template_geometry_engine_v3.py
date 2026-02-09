"""
HVACgooee — Template Geometry Engine (v3, v1-restricted)

Deterministic surface generator from declarative templates.

RULES (LOCKED — v1):
• RECT_0–RECT_3 only
• Rectangular enclosure only
• No geometry subtraction
• No airflow
• No physics
"""

from __future__ import annotations

from typing import List

from HVAC_legacy.geometry_v3.geometry_templates import (
    TemplateType,
    RectangularRoomParams,
)
from HVAC_legacy.project_v3.project_models_v3 import SurfaceV3


class TemplateGeometryEngineV3:
    """
    Convert enclosure templates into SurfaceV3 objects.

    This engine:
    • validates geometry intent
    • generates canonical rectangular surfaces
    • performs NO subtraction or inference
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_surfaces(
        self,
        *,
        template: TemplateType,
        params: RectangularRoomParams,
    ) -> List[SurfaceV3]:
        """
        Generate enclosure surfaces for a geometry template.
        """

        # --------------------------------------------------------------
        # v1 validation (intent-level only)
        # --------------------------------------------------------------

        if not template.startswith("RECT_"):
            raise ValueError(f"Unsupported geometry template '{template}'")

        try:
            required_cutouts = int(template[-1])
        except ValueError:
            raise ValueError(f"Invalid RECT template '{template}'")

        if params.corner_cutouts != required_cutouts:
            raise ValueError(
                f"Template {template} requires {required_cutouts} corner cut-outs "
                f"(got {params.corner_cutouts})"
            )

        if params.corner_cutouts > 3:
            raise ValueError("v1 supports up to 3 corner cut-outs only")

        # --------------------------------------------------------------
        # Surface generation (rectangular enclosure)
        # --------------------------------------------------------------

        return self._rectangular_room(params)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rectangular_room(
        self,
        params: RectangularRoomParams,
    ) -> List[SurfaceV3]:
        """
        Generate surfaces for a simple rectangular enclosure.

        NOTE:
        • Floor is always generated in v1
        • Suppression / substitution is deferred
        """

        L = params.length_m
        W = params.width_m
        H = params.height_m

        surfaces: List[SurfaceV3] = []

        # Walls
        surfaces.append(
            SurfaceV3(kind="WALL", area_m2=L * H, orientation="N")
        )
        surfaces.append(
            SurfaceV3(kind="WALL", area_m2=W * H, orientation="E")
        )
        surfaces.append(
            SurfaceV3(kind="WALL", area_m2=L * H, orientation="S")
        )
        surfaces.append(
            SurfaceV3(kind="WALL", area_m2=W * H, orientation="W")
        )

        # Ceiling
        surfaces.append(
            SurfaceV3(kind="CEILING", area_m2=L * W)
        )

        # Floor (always present in v1 geometry engine)
        surfaces.append(
            SurfaceV3(kind="FLOOR", area_m2=L * W)
        )

        return surfaces
