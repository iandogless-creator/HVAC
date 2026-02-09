"""
HVACgooee — Construction Builder (Heat-Loss Core v1)
===================================================

Purpose
-------
Provides a universal engine for:

- Layer-by-layer construction assembly
- R-layer summation
- Internal/external surface films
- Bridging fractions (timber/metal studs)
- U-value calculation
- Educational output
- Simple/Advanced/Educational modes

Works for:
    • Walls
    • Floors
    • Ceilings
    • Roofs (non-pitched — pitched has separate module)
    • Any multi-layer build-up

Design Rules
------------
- Pure backend physics.
- No GUI / DXF imports.
- Uses MaterialsDatabase for conductivity (optional).
- Flexible enough for legacy ENV build-ups and modern layered systems.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ConstructionLayer:
    """
    Represents a single layer in a construction.
    """
    name: str
    thickness_m: float
    conductivity_W_mK: float
    density_kg_m3: Optional[float] = None
    specific_heat_J_kgK: Optional[float] = None


@dataclass
class Construction:
    """
    Represents an entire wall/floor/roof construction.
    """
    layers: List[ConstructionLayer] = field(default_factory=list)

    internal_surface_resistance: float = 0.13   # m²K/W
    external_surface_resistance: float = 0.04   # m²K/W

    bridging_fraction: float = 0.0              # fraction (0–1)
    bridging_conductivity: float = 0.0          # e.g. timber ~0.13, steel ~50

    mode: str = "advanced"                      # simple/advanced/educational


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def layer_resistance(layer: ConstructionLayer) -> float:
    """
    R = thickness / conductivity
    """
    return layer.thickness_m / layer.conductivity_W_mK


def parallel_path_resistance(
    layers: List[ConstructionLayer],
    bridging_fraction: float,
    bridging_k: float
) -> float:
    """
    Calculates effective resistance using parallel paths:
        - insulation path
        - bridging path (timber/steel)
    """
    R_ins = sum(layer_resistance(L) for L in layers)
    R_bridge = sum(L.thickness_m / bridging_k for L in layers)

    f = bridging_fraction
    if f <= 0:
        return R_ins

    return 1.0 / ((f / R_bridge) + ((1 - f) / R_ins))


# ---------------------------------------------------------------------------
# U-value Calculation
# ---------------------------------------------------------------------------

def construction_u_value(con: Construction) -> float:
    """
    Calculate U-value for a layered construction.
    Applies bridging if mode = advanced/educational.
    """
    # Surface resistance (internal)
    R_total = con.internal_surface_resistance

    # Layers
    if con.mode == "simple" or con.bridging_fraction == 0:
        R_layers = sum(layer_resistance(l) for l in con.layers)
    else:
        R_layers = parallel_path_resistance(
            con.layers,
            con.bridging_fraction,
            con.bridging_conductivity
        )

    R_total += R_layers

    # Surface resistance (external)
    R_total += con.external_surface_resistance

    U = 1.0 / R_total
    return U


# ---------------------------------------------------------------------------
# Educational Breakdown
# ---------------------------------------------------------------------------

def diagnostic_construction_breakdown(con: Construction) -> Dict[str, float]:
    """
    Returns intermediate values for Educational mode.
    """
    breakdown = {}
    R_total = 0.0

    # Internal surface
    breakdown["R_internal_surface"] = con.internal_surface_resistance
    R_total += con.internal_surface_resistance

    # Pure insulation path
    R_ins_list = [layer_resistance(L) for L in con.layers]
    breakdown["R_layers_insulation_path"] = sum(R_ins_list)

    # Bridging path (if applicable)
    if con.bridging_fraction > 0:
        R_bridge_list = [
            L.thickness_m / con.bridging_conductivity for L in con.layers
        ]
        breakdown["R_layers_bridged_path"] = sum(R_bridge_list)
        R_parallel = parallel_path_resistance(
            con.layers,
            con.bridging_fraction,
            con.bridging_conductivity
        )
        breakdown["R_effective_parallel"] = R_parallel
        R_total += R_parallel
    else:
        breakdown["R_effective_parallel"] = breakdown["R_layers_insulation_path"]
        R_total += breakdown["R_layers_insulation_path"]

    # External surface
    breakdown["R_external_surface"] = con.external_surface_resistance
    R_total += con.external_surface_resistance

    breakdown["R_total"] = R_total
    breakdown["U_value"] = 1.0 / R_total

    return breakdown


# ---------------------------------------------------------------------------
# Builder API
# ---------------------------------------------------------------------------

def build_construction_from_specs(
    specs: List[Dict],
    bridging_fraction: float = 0.0,
    bridging_conductivity: float = 0.0,
    mode: str = "advanced"
) -> Construction:
    """
    Build a Construction object from a list of dict specifications.

    specs example:
        [
            {"name": "brick", "thickness_m": 0.1, "k": 0.77},
            {"name": "insulation", "thickness_m": 0.12, "k": 0.035},
            {"name": "plasterboard", "thickness_m": 0.013, "k": 0.19},
        ]

    Conductivity field may be:
    - "conductivity"
    - "k"
    - "lambda" (legacy)
    """
    layers = []
    for s in specs:
        k = (
            s.get("conductivity")
            or s.get("k")
            or s.get("lambda")
        )
        if k is None:
            raise ValueError(f"Missing conductivity for layer: {s}")

        layers.append(
            ConstructionLayer(
                name=s.get("name", "layer"),
                thickness_m=float(s["thickness_m"]),
                conductivity_W_mK=float(k),
                density_kg_m3=s.get("density"),
                specific_heat_J_kgK=s.get("specific_heat"),
            )
        )

    return Construction(
        layers=layers,
        bridging_fraction=bridging_fraction,
        bridging_conductivity=bridging_conductivity,
        mode=mode
    )
