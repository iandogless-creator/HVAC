"""
project_factory_v1_LEGACY.py
---------------------
# ⚠️ FROZEN — DO NOT EXTEND

HVACgooee — Project Factory v1 (Single Space, Schematic)

Canonical ENTRY POINT for a new project/job.

• One space only
• Schematic geometry
• Fabric heat-loss derived automatically
• Hydronics can attach later (parallel)

NO GUI
NO CAD
NO persistence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Tuple

# ---- Geometry / openings ----
from HVAC_legacy.geometry.opening_placement_v1 import (
    OpeningPlacement,
    resolve_all_openings,
)

# ---- Heat-loss attribution ----
from HVAC_legacy.heatloss.opening_attribution_v1 import (
    attribute_openings_for_heatloss,
)
from HVAC_legacy.heatloss.wall_attribution_v1 import (
    attribute_walls_for_heatloss,
)
from HVAC_legacy.heatloss.wall_uvalue_application_v1 import (
    apply_uvalues_to_walls,
)
from HVAC_legacy.heatloss.heatloss_payload_v1 import (
    HeatLossPayload,
    build_heatloss_payload,
)


Point = Tuple[float, float]


# ================================================================
# DATA MODELS
# ================================================================
@dataclass
class SpaceV1:
    footprint: List[Point]
    height_m: float
    orientation_deg: float
    openings: List[OpeningPlacement] = field(default_factory=list)


@dataclass
class ConstructionSetV1:
    wall_uvalues_by_facade: dict
    opening_uvalues_by_type: dict
    default_window_height_m: float = 1.2
    default_door_height_m: float = 2.0


@dataclass
class ProjectV1:
    name: str
    units: str = "metric"

    space: Optional[SpaceV1] = None
    constructions: Optional[ConstructionSetV1] = None

    # Derived (never edited directly)
    heatloss_payload: Optional[HeatLossPayload] = None


# ================================================================
# FACTORY FUNCTIONS
# ================================================================
def create_new_project(name: str) -> ProjectV1:
    return ProjectV1(name=name)


def attach_space(
    project: ProjectV1,
    *,
    footprint: List[Point],
    height_m: float,
    orientation_deg: float,
) -> None:
    project.space = SpaceV1(
        footprint=footprint,
        height_m=float(height_m),
        orientation_deg=float(orientation_deg),
    )


def attach_constructions(
    project: ProjectV1,
    *,
    wall_uvalues_by_facade: dict,
    opening_uvalues_by_type: dict,
    default_window_height_m: float = 1.2,
    default_door_height_m: float = 2.0,
) -> None:
    project.constructions = ConstructionSetV1(
        wall_uvalues_by_facade=wall_uvalues_by_facade,
        opening_uvalues_by_type=opening_uvalues_by_type,
        default_window_height_m=default_window_height_m,
        default_door_height_m=default_door_height_m,
    )


# ================================================================
# LIFECYCLE HELPERS
# ================================================================
def is_heatloss_ready(project: ProjectV1) -> bool:
    return project.space is not None and project.constructions is not None


def build_heatloss_if_ready(project: ProjectV1) -> None:
    """
    FULL fabric pipeline.
    """

    if not is_heatloss_ready(project):
        project.heatloss_payload = None
        return

    space = project.space
    cons = project.constructions

    # ---- Resolve openings geometry ----
    resolved_openings = resolve_all_openings(
        footprint=space.footprint,
        openings=space.openings,
        space_orientation_deg=space.orientation_deg,
    )

    # ---- Opening heat-loss attribution ----
    opening_attribs = attribute_openings_for_heatloss(
        resolved_openings,
        default_height_m=cons.default_window_height_m,
    )

    # ---- Wall gross/net attribution ----
    wall_attribs = attribute_walls_for_heatloss(
        footprint=space.footprint,
        space_orientation_deg=space.orientation_deg,
        space_height_m=space.height_m,
        opening_attributions=opening_attribs,
    )

    # ---- Apply wall U-values ----
    wall_losses = apply_uvalues_to_walls(
        wall_attributions=wall_attribs,
        wall_uvalues=cons.wall_uvalues_by_facade,
    )

    # ---- Build final payload ----
    project.heatloss_payload = build_heatloss_payload(
        wall_losses=wall_losses,
        opening_attributions=opening_attribs,
        opening_uvalues=cons.opening_uvalues_by_type,
    )


# ================================================================
# DEBUG / REPORT
# ================================================================
def describe_project(project: ProjectV1) -> str:
    lines = [
        f"Project: {project.name}",
        f"Units: {project.units}",
    ]

    if project.space:
        s = project.space
        lines.extend(
            [
                "Space:",
                f"  Height: {s.height_m} m",
                f"  Orientation: {s.orientation_deg}°",
                f"  Footprint points: {len(s.footprint)}",
                f"  Openings: {len(s.openings)}",
            ]
        )

    if project.heatloss_payload:
        p = project.heatloss_payload
        lines.extend(
            [
                "Fabric heat-loss:",
                f"  Walls: {p.total_wall_heat_loss_w_per_k:.2f} W/K",
                f"  Openings: {p.total_opening_heat_loss_w_per_k:.2f} W/K",
                f"  TOTAL: {p.total_fabric_heat_loss_w_per_k:.2f} W/K",
            ]
        )

    return "\n".join(lines)
