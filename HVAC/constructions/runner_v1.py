# ======================================================================
# HVAC/constructions/runner_v1.py
# ======================================================================

"""
HVACgooee — Construction Resolution Runner v1 (CANONICAL)

Purpose
-------
Resolve declared construction intent into authoritative U-values.

This step freezes construction physics inputs for heat-loss v1.

LOCKED RULES
------------
• No geometry
• No ΔT
• No heat-loss
• No hydronics
• No GUI imports
• Registry is the sole authority
"""

from __future__ import annotations

from typing import List

from HVAC.constructions.registry_v2 import CONSTRUCTION_REGISTRY_V2
from HVAC.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC.constructions.construction_preset import SurfaceClass


def resolve_constructions_v1(project) -> None:
    """
    Resolve construction presets into U-values and attach results
    to the project.

    Mutates:
        project.constructions.results
        project.constructions.valid
    """

    # ------------------------------------------------------------------
    # Preconditions
    # ------------------------------------------------------------------
    if project.constructions is None:
        raise RuntimeError("Project has no constructions section")

    presets = project.constructions.presets
    if not presets:
        raise RuntimeError("No construction presets declared")

    results: List[ConstructionUValueResultDTO] = []

    # ------------------------------------------------------------------
    # Resolution loop (authoritative)
    # ------------------------------------------------------------------
    for surface_class, preset_ref in presets.items():

        if not isinstance(surface_class, SurfaceClass):
            raise TypeError(
                f"Invalid surface class key: {surface_class}"
            )

        if not preset_ref:
            raise RuntimeError(
                f"No preset ref for surface class {surface_class}"
            )

        dto = CONSTRUCTION_REGISTRY_V2.build_uvalue_result(
            surface_class=surface_class,
            preset_ref=preset_ref,
        )

        results.append(dto)

    # ------------------------------------------------------------------
    # Commit results
    # ------------------------------------------------------------------
    project.constructions.results = results
    project.constructions.valid = True
