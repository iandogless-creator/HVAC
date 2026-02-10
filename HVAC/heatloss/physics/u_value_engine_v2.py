"""
u_value_engine_v2.py
--------------------

HVACgooee — U-Value Engine v2

Scope (safe start)
==================
- Define basic layer + construction dataclasses
- Compute U-values for layered constructions
- Provide a helper to associate U-values with Surfaces

This module does NOT:
    - change HeatLossController yet
    - change Surface dataclass itself
    - compute any Q = U × A × ΔT

It is a standalone engine that other parts of the system
can call as needed.

Assumptions
===========
- Thickness in metres (m)
- Conductivity in W/m·K
- Rsi, Rse in m²K/W (internal/external surface resistances)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from HVAC.spaces.surface_engine_v1 import Surface, SurfaceType


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Layer:
    """
    Single fabric layer in a construction build-up.

    thickness_m:           layer thickness [m]
    conductivity_W_mK:     thermal conductivity λ [W/m·K]
    """
    name: str
    thickness_m: float
    conductivity_W_mK: float

    @property
    def resistance_m2K_W(self) -> float:
        """
        R_layer = thickness / λ
        """
        if self.conductivity_W_mK <= 0.0:
            raise ValueError(f"Layer '{self.name}' has non-positive conductivity.")
        return self.thickness_m / self.conductivity_W_mK


@dataclass
class Construction:
    """
    Multi-layer construction for a surface.

    Includes:
        - layers
        - internal surface resistance Rsi
        - external surface resistance Rse

    U-value calculation:
        R_total = Rsi + Σ(thickness/λ) + Rse
        U       = 1 / R_total
    """
    id: str
    name: str
    layers: List[Layer]

    Rsi_m2K_W: float = 0.13  # typical internal
    Rse_m2K_W: float = 0.04  # typical external

    def total_resistance_m2K_W(self) -> float:
        """
        Compute total thermal resistance including surface films.
        """
        R_layers = sum(layer.resistance_m2K_W for layer in self.layers)
        return self.Rsi_m2K_W + R_layers + self.Rse_m2K_W

    def u_value_W_m2K(self) -> float:
        """
        Compute U-value (W/m²K).
        """
        R_total = self.total_resistance_m2K_W()
        if R_total <= 0.0:
            raise ValueError(f"Construction '{self.id}' has non-positive total resistance.")
        return 1.0 / R_total


@dataclass
class SurfaceWithU:
    """
    Wrapper around a geometric Surface with an assigned construction
    and resulting U-value.

    This avoids modifying the original Surface dataclass (for now).
    """
    surface: Surface
    construction_id: str
    u_value_W_m2K: float


# ---------------------------------------------------------------------------
# Core Engine Functions
# ---------------------------------------------------------------------------

def compute_u_values_for_constructions(
    constructions: Dict[str, Construction]
) -> Dict[str, float]:
    """
    Given a mapping id -> Construction, return a mapping id -> U-value.

    Useful for caching U-values from a constructions library.
    """
    u_map: Dict[str, float] = {}
    for cid, cons in constructions.items():
        u_map[cid] = cons.u_value_W_m2K()
    return u_map


def assign_u_values_to_surfaces(
    surfaces: List[Surface],
    default_construction_by_type: Dict[SurfaceType, Construction],
) -> List[SurfaceWithU]:
    """
    Assign U-values to surfaces using a simple rule:

        - each SurfaceType gets a default Construction
        - we compute U for that Construction
        - we return a list of SurfaceWithU wrappers

    This is deliberately simple for v2:
        - no per-surface overrides
        - no adjacency logic
        - no dynamic Y-values

    Parameters
    ----------
    surfaces : List[Surface]
        Surfaces from Surface Engine v1.
    default_construction_by_type : Dict[SurfaceType, Construction]
        Mapping from surface type to a default construction.

    Returns
    -------
    List[SurfaceWithU]
    """
    results: List[SurfaceWithU] = []

    # Precompute U-values for efficiency
    u_cache: Dict[str, float] = {}

    for surf in surfaces:
        cons = default_construction_by_type.get(surf.surface_type)
        if cons is None:
            # No construction defined for this type; skip for now.
            # In future we might raise, log, or mark as UNKNOWN.
            continue

        if cons.id not in u_cache:
            u_cache[cons.id] = cons.u_value_W_m2K()

        u_val = u_cache[cons.id]
        results.append(
            SurfaceWithU(
                surface=surf,
                construction_id=cons.id,
                u_value_W_m2K=u_val,
            )
        )

    return results
