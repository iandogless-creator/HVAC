"""
heatloss_payload_v1.py
----------------------

HVACgooee — HeatLossPayload v1 (Fabric Only)

Purpose
-------
Provide a SINGLE, SOLVER-FACING data structure containing
all steady-state fabric heat-loss coefficients (W/K)
for a space.

This version includes:
    • Walls (by façade)
    • Openings (windows / doors, by façade)

Future versions will extend with:
    • Floors
    • Roofs
    • Thermal bridges (ψ)
    • Dynamic terms

Design Rules (v1.5)
------------------
✔ Immutable payload
✔ Solver-agnostic
✔ No geometry
✔ No climate
✔ No ΔT
✔ Safe for core
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
# Geometry
from __future__ import annotations

from HVAC.geometry.opening_placement_v1 import (
    OpeningPlacement,
    resolve_all_openings,
)

# Heat-loss attribution (SURFACES — not engines)
from HVAC.heatloss.surfaces.opening_attribution_v1 import (
    attribute_openings_for_heatloss,
)

from HVAC.heatloss.surfaces.wall_attribution_v1 import (
    attribute_walls_for_heatloss,
)

from HVAC.heatloss.surfaces.wall_uvalue_application_v1 import (
    apply_uvalues_to_walls,
)

from dataclasses import dataclass
from typing import Dict, Literal



# END IMPORTS
# ================================================================

Facade = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


# ================================================================
# BEGIN DATA MODELS
# ================================================================
@dataclass(frozen=True)
class OpeningHeatLossCoefficient:
    """
    Heat-loss coefficient for a single opening type on a façade.

    heat_loss_w_per_k = U × Area
    """

    opening_type: str
    facade: Facade
    u_value_w_m2k: float
    area_m2: float
    heat_loss_w_per_k: float


@dataclass(frozen=True)
class HeatLossPayload:
    """
    Canonical payload passed into heat-loss solvers.
    """

    wall_losses: Dict[Facade, WallHeatLossCoefficient]
    opening_losses: Dict[Facade, Dict[str, OpeningHeatLossCoefficient]]

    total_wall_heat_loss_w_per_k: float
    total_opening_heat_loss_w_per_k: float
    total_fabric_heat_loss_w_per_k: float


# END DATA MODELS
# ================================================================


# ================================================================
# BEGIN PAYLOAD BUILDERS
# ================================================================
def build_opening_heat_loss_coefficients(
    opening_attributions: list[OpeningHeatLossAttribution],
    opening_uvalues: Dict[str, float],
) -> Dict[Facade, Dict[str, OpeningHeatLossCoefficient]]:
    """
    Apply U-values to opening attributions.

    opening_uvalues:
        Dict mapping opening_type -> U-value (W/m²K)
        e.g. { "window": 1.2, "door": 1.8 }
    """

    results: Dict[Facade, Dict[str, OpeningHeatLossCoefficient]] = {}

    for o in opening_attributions:
        if o.opening_type not in opening_uvalues:
            raise KeyError(
                f"No U-value provided for opening type '{o.opening_type}'"
            )

        u = float(opening_uvalues[o.opening_type])
        heat_loss = u * o.area_m2

        by_facade = results.setdefault(o.facade, {})
        by_facade[o.opening_type] = OpeningHeatLossCoefficient(
            opening_type=o.opening_type,
            facade=o.facade,
            u_value_w_m2k=u,
            area_m2=o.area_m2,
            heat_loss_w_per_k=heat_loss,
        )

    return results


def build_heatloss_payload(
    wall_losses: Dict[Facade, WallHeatLossCoefficient],
    opening_attributions: list[OpeningHeatLossAttribution],
    opening_uvalues: Dict[str, float],
) -> HeatLossPayload:
    """
    Build the canonical HeatLossPayload v1.
    """

    opening_losses = build_opening_heat_loss_coefficients(
        opening_attributions=opening_attributions,
        opening_uvalues=opening_uvalues,
    )

    total_wall = sum(
        w.heat_loss_w_per_k for w in wall_losses.values()
    )

    total_opening = sum(
        ol.heat_loss_w_per_k
        for by_facade in opening_losses.values()
        for ol in by_facade.values()
    )

    total_fabric = total_wall + total_opening

    return HeatLossPayload(
        wall_losses=wall_losses,
        opening_losses=opening_losses,
        total_wall_heat_loss_w_per_k=total_wall,
        total_opening_heat_loss_w_per_k=total_opening,
        total_fabric_heat_loss_w_per_k=total_fabric,
    )


# END PAYLOAD BUILDERS
# ================================================================
