# ======================================================================
# HVAC/project_v3/project_models_v3.py
# ======================================================================

"""
HVACgooee — Project Models v3 (CANONICAL)

Purpose
-------
Intent + results container models for Project v3.

LOCKED RULES
------------
• Data only (no physics)
• Safe to import from runners
• Supports single-file project.json authority
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from HVAC.constructions.construction_preset import SurfaceClass


# ---------------------------------------------------------------------
# Intent / Results containers
# ---------------------------------------------------------------------

@dataclass(slots=True)
class ConstructionsV3:
    """
    Declared construction intent + resolved results.

    presets: user intent (refs)
    results: resolved DTO list (filled by resolve_constructions_v1)
    valid: explicit validity flag
    """
    presets: Dict[SurfaceClass, str] = field(default_factory=dict)
    results: List[Any] = field(default_factory=list)   # DTOs live in constructions/dto
    valid: bool = False


@dataclass(slots=True)
class HeatLossV3:
    """
    Heat-loss result container (authoritative after commit).
    """
    valid: bool = False
    qt_w: Optional[float] = None
    results: Optional[Any] = None


@dataclass(slots=True)
class HydronicsV3:
    """
    Hydronics result container (authoritative after commit).
    """
    valid: bool = False
    system_type: str = "two_pipe_direct_return"
    emitters: List[Dict[str, Any]] = field(default_factory=list)
    results: Optional[Any] = None


# ---------------------------------------------------------------------
# Geometry / Room intent
# ---------------------------------------------------------------------

@dataclass(slots=True)
class RoomGeometryV3:
    length_m: float
    width_m: float
    height_m: float

    @property
    def floor_area_m2(self) -> float:
        return float(self.length_m) * float(self.width_m)

    @property
    def volume_m3(self) -> float:
        return self.floor_area_m2 * float(self.height_m)


@dataclass(slots=True)
class ApertureV3:
    """
    Aperture intent (v1 calls them 'openings' in JSON; we treat as apertures).
    These reduce areas only; they do not change perimeter/topology.
    """
    aperture_id: str
    type: str                 # "window", "internal_door", etc.
    area_m2: float
    surface_class: SurfaceClass


@dataclass(slots=True)
class SurfaceV3:
    """
    Derived surface for heat-loss runner consumption.
    (Created via template expansion; still no physics.)
    """
    surface_id: str
    surface_class: SurfaceClass
    area_m2: float
    construction_ref: str
    orientation: Optional[str] = None


@dataclass(slots=True)
class SpaceV3:
    """
    Declared thermal space (room).
    design_temp_C is set from HVAC.project.
 environment in v1 canonical.
    """
    space_id: str
    name: str
    design_temp_C: float
    geometry: RoomGeometryV3
    template: str
    apertures: List[ApertureV3] = field(default_factory=list)

    # Values consumed by existing HeatLossRunnerV3
    surfaces: List[SurfaceV3] = field(default_factory=list)

    # Optional ventilation support (HeatLossRunnerV3 checks hasattr)
    ventilation_ach: Optional[float] = None

    @property
    def volume_m3(self) -> float:
        return self.geometry.volume_m3


@dataclass(slots=True)
class ProjectMetaV3:
    project_id: str
    name: str
    description: str
    created_uk: str
    schema_version: str
    status: str


@dataclass(slots=True)
class ProjectV3:
    """
    Assembled Project v3 container.

    SINGLE authoritative runtime state lives in:
        project.project_state
    """
    project_meta: ProjectMetaV3
    project_info: Dict[str, Any]              # legacy-friendly keys for runners
    spaces: List[SpaceV3]
    constructions: ConstructionsV3
    heatloss: HeatLossV3
    hydronics: HydronicsV3

    project_state: Any                        # HVAC.project.project_state.ProjectState
    project_dir: Any                          # pathlib.Path
