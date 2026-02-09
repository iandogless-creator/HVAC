"""
project_factory_v3.py
---------------------

HVACgooee — Project Factory v3 (Design-Level Aware)

ASSEMBLY ONLY.
This module resolves declared project intent into explicit,
engine-ready inputs using the project-wide Design Level.

• No physics calculations
• No engine calls
• No GUI imports
• One canonical execution path per domain

Supersedes all pre-V3 project factories.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Protocol, Any, List, Tuple

from HVAC_legacy.core.resolution_registry import ResolutionRegistry

# ============================================================
# Design Level (Project-wide single source of truth)
# ============================================================

class DesignLevel(str, Enum):
    NOVICE = "novice"
    SIMPLE = "simple"
    ADVANCED = "advanced"
    TECHNICAL = "technical"


# ============================================================
# Core "Declared Intent" Models (user-facing intent)
# ============================================================

Point = Tuple[float, float]


@dataclass(slots=True)
class SpaceIntent:
    """
    User-declared intent for a space.
    No physics. No derived numbers.
    """
    name: str
    footprint: List[Point]
    height_m: float = 2.4
    design_temp_C: float = 21.0
    outside_temp_C: float = -3.0  # boundary reference until adjacency exists
    orientation_deg: float = 0.0

    # Ventilation intent (can be sparse in novice/simple)
    ach: Optional[float] = None
    ventilation_method: Optional[str] = None  # e.g. "ACH", "Infiltration+Extract", etc.


@dataclass(slots=True)
class ProjectIntent:
    """
    Project intent = what the user chose/declared.
    This is not yet 'fully explicit' until resolved.
    """
    name: str
    design_level: DesignLevel
    units: str = "metric"
    spaces: List[SpaceIntent] = field(default_factory=list)

    # Global construction intent (might be minimal in novice/simple)
    period_of_construction: Optional[str] = None
    upgrade_status: Optional[str] = None

    # In advanced/technical, user may explicitly pick presets or constructions
    construction_preset_id: Optional[str] = None

# ============================================================
# Explicit Engine Inputs (resolver output, engine-ready)
# ============================================================

@dataclass(slots=True)
class ResolvedSurfaceInput:
    """
    Canonical, explicit surface input for Heat-Loss engine.
    No origin metadata required by engine; provenance stays outside.
    """
    name: str
    area_m2: float
    u_value: float
    delta_t_C: float
    kind: str  # "wall", "window", "roof", "floor", etc.


@dataclass(slots=True)
class ResolvedVentilationInput:
    volume_m3: float
    ach: float
    delta_t_C: float


@dataclass(slots=True)
class ResolvedSpaceHeatlossInputs:
    space_name: str
    surfaces: List[ResolvedSurfaceInput]
    ventilation: ResolvedVentilationInput


@dataclass(slots=True)
class ResolvedProjectInputs:
    """
    What engines consume.
    Still no calculations here — just explicit inputs.
    """
    project_name: str
    design_level: DesignLevel
    spaces: List[ResolvedSpaceHeatlossInputs]

    # Future: hydronics explicit demands, system intent bundles, etc.
    # hydronics: Optional[ResolvedHydronicsInputs] = None


# ============================================================
# Assumption Resolver Protocol
# ============================================================

class AssumptionResolver(Protocol):
    """
    Resolve ProjectIntent into explicit engine inputs.
    NO physics calculations. NO engine calls.
    """

    def resolve(self, intent: ProjectIntent, registry: Any) -> ResolvedProjectInputs:
        ...


# ============================================================
# Resolver Implementations (knowledge paths)
# ============================================================

class NoviceResolver:
    """
    Maximum automation.
    Uses safe defaults and coarse presets.
    Must still output explicit surfaces, U-values, and ACH.
    """

    def resolve(self, intent: ProjectIntent, registry: Any) -> ResolvedProjectInputs:
        resolved_spaces: List[ResolvedSpaceHeatlossInputs] = []

        for sp in intent.spaces:
            # Resolve defaults
            ach = sp.ach if sp.ach is not None else registry.defaults.novice_ach()

            # Resolve constructions/presets (coarse)
            preset = registry.presets.novice_default()

            # Build explicit surfaces from geometry templates (no subtraction logic required yet)
            surfaces = registry.geometry.build_surfaces_from_footprint(
                footprint=sp.footprint,
                height_m=sp.height_m,
                preset=preset,
            )

            delta_t = sp.design_temp_C - sp.outside_temp_C
            explicit_surfaces = [
                ResolvedSurfaceInput(
                    name=s.name,
                    area_m2=s.area_m2,
                    u_value=s.u_value,
                    delta_t_C=delta_t,
                    kind=s.kind,
                )
                for s in surfaces
            ]

            volume = registry.geometry.volume_from_footprint(sp.footprint, sp.height_m)

            resolved_spaces.append(
                ResolvedSpaceHeatlossInputs(
                    space_name=sp.name,
                    surfaces=explicit_surfaces,
                    ventilation=ResolvedVentilationInput(
                        volume_m3=volume,
                        ach=ach,
                        delta_t_C=delta_t,
                    ),
                )
            )

        return ResolvedProjectInputs(
            project_name=intent.name,
            design_level=intent.design_level,
            spaces=resolved_spaces,
        )


class SimpleResolver:
    """
    Standards-guided resolution (Part-L-ish policy).
    User chooses period/upgrade; resolver selects explicit presets.
    Outputs explicit U-values, ACH, and surface list.
    """

    def resolve(self, intent: ProjectIntent, registry: Any) -> ResolvedProjectInputs:
        resolved_spaces: List[ResolvedSpaceHeatlossInputs] = []

        preset = registry.presets.from_period_and_upgrade(
            period=intent.period_of_construction,
            upgrade=intent.upgrade_status,
        )

        for sp in intent.spaces:
            ach = sp.ach if sp.ach is not None else registry.defaults.simple_ach(preset)

            surfaces = registry.geometry.build_surfaces_from_footprint(
                footprint=sp.footprint,
                height_m=sp.height_m,
                preset=preset,
            )

            delta_t = sp.design_temp_C - sp.outside_temp_C
            explicit_surfaces = [
                ResolvedSurfaceInput(
                    name=s.name,
                    area_m2=s.area_m2,
                    u_value=s.u_value,
                    delta_t_C=delta_t,
                    kind=s.kind,
                )
                for s in surfaces
            ]

            volume = registry.geometry.volume_from_footprint(sp.footprint, sp.height_m)

            resolved_spaces.append(
                ResolvedSpaceHeatlossInputs(
                    space_name=sp.name,
                    surfaces=explicit_surfaces,
                    ventilation=ResolvedVentilationInput(
                        volume_m3=volume,
                        ach=ach,
                        delta_t_C=delta_t,
                    ),
                )
            )

        return ResolvedProjectInputs(
            project_name=intent.name,
            design_level=intent.design_level,
            spaces=resolved_spaces,
        )


class AdvancedResolver:
    """
    User designs inputs.
    Exposes full construction selection and explicit ventilation method.
    Still outputs explicit surfaces + u-values (from presets/registry), not calculations.
    """

    def resolve(self, intent: ProjectIntent, registry: Any) -> ResolvedProjectInputs:
        resolved_spaces: List[ResolvedSpaceHeatlossInputs] = []

        preset = registry.presets.get(intent.construction_preset_id)

        for sp in intent.spaces:
            if sp.ach is None:
                raise ValueError("Advanced mode requires explicit ACH (or explicit ventilation method).")

            surfaces = registry.geometry.build_surfaces_from_footprint(
                footprint=sp.footprint,
                height_m=sp.height_m,
                preset=preset,
            )

            delta_t = sp.design_temp_C - sp.outside_temp_C
            explicit_surfaces = [
                ResolvedSurfaceInput(
                    name=s.name,
                    area_m2=s.area_m2,
                    u_value=s.u_value,
                    delta_t_C=delta_t,
                    kind=s.kind,
                )
                for s in surfaces
            ]

            volume = registry.geometry.volume_from_footprint(sp.footprint, sp.height_m)

            resolved_spaces.append(
                ResolvedSpaceHeatlossInputs(
                    space_name=sp.name,
                    surfaces=explicit_surfaces,
                    ventilation=ResolvedVentilationInput(
                        volume_m3=volume,
                        ach=sp.ach,
                        delta_t_C=delta_t,
                    ),
                )
            )

        return ResolvedProjectInputs(
            project_name=intent.name,
            design_level=intent.design_level,
            spaces=resolved_spaces,
        )


class TechnicalResolver(AdvancedResolver):
    """
    Same explicitness as Advanced, plus audit metadata (outside engine).
    In V3, audit details should live in reports/DTO provenance, not engine inputs.
    """
    # You can extend to output an additional "provenance bundle" for reporting,
    # while keeping engine inputs identical to Advanced.


# ============================================================
# Project Factory (V3) — select resolver based on design level
# ============================================================

class ProjectFactoryV3:
    """
    Single entry point: creates ResolvedProjectInputs from ProjectIntent
    using the project's design_level.
    """

    def __init__(self, registry: Any):
        self._registry = registry
        self._resolvers: Dict[DesignLevel, AssumptionResolver] = {
            DesignLevel.NOVICE: NoviceResolver(),
            DesignLevel.SIMPLE: SimpleResolver(),
            DesignLevel.ADVANCED: AdvancedResolver(),
            DesignLevel.TECHNICAL: TechnicalResolver(),
        }

    def build(self, intent: ProjectIntent) -> ResolvedProjectInputs:
        if not intent.spaces:
            raise ValueError("ProjectIntent must contain at least one SpaceIntent.")

        resolver = self._resolvers[intent.design_level]
        return resolver.resolve(intent, self._registry)
