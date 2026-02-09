"""
constructions.py
----------------

HVACgooee — Construction Engine (2025 edition)

Defines the canonical Construction model:

    • Layers with λ, ρ, c, thickness
    • Computes:
        - layer resistances
        - R_total
        - U_value
        - C_areal (areal heat capacity, J/m²K)
    • Provides helper functions for GUI and controllers.

This is a CORE physics engine and must remain GPL / immutable.

Explicit BEGIN/END markers are included for readability.
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

# NO imports from u_value_engine
# END IMPORTS
# ================================================================



# ================================================================
# BEGIN DATA STRUCTURES
# ================================================================

# ------------------------------------------------------------
# BEGIN CLASS: Construction
# ------------------------------------------------------------
# ------------------------------------------------------------
# BEGIN CLASS: Layer
# ------------------------------------------------------------
@dataclass
class Layer:
    """
    Single material layer in a construction.

    Parameters:
        name: material name
        thickness_m: layer thickness [m]
        conductivity_W_mK: thermal conductivity λ [W/m·K]
        density_kg_m3: bulk density [kg/m³] (optional, for Y-value engine)
        heat_capacity_J_kgK: specific heat capacity [J/kgK] (optional)
    """
    name: str
    thickness_m: float
    conductivity_W_mK: float
    density_kg_m3: float | None = None
    heat_capacity_J_kgK: float | None = None
# ------------------------------------------------------------
# END CLASS: Layer
# ------------------------------------------------------------

@dataclass
class Construction:
    """
    A multi-layer fabric construction.

    Layers are ordered from inside → outside.
    """
    name: str
    layers: List[Layer] = field(default_factory=list)

    Rsi: float = 0.13
    Rse: float = 0.04

    R_total: float = 0.0
    U_value: float = 0.0
    C_areal: float = 0.0     # J/m²K (for Y-engine)

    # BEGIN METHOD: recalc
    def recalc(self) -> None:
        """
        Recalculate R_total, U_value, and C_areal from layers.
        """
        self.R_total = self._compute_R_total()
        self.U_value = 0.0 if self.R_total <= 0 else 1.0 / self.R_total
        self.C_areal = self._compute_C_areal()
    # END METHOD: recalc

    # BEGIN METHOD: _compute_R_total
    def _compute_R_total(self) -> float:
        """
        Internal helper to compute total thermal resistance.
        """
        if not self.layers:
            return 0.0

        R_layers = 0.0
        for layer in self.layers:
            if layer.conductivity_W_mK <= 0 or layer.thickness_m <= 0:
                continue
            R_layers += layer.thickness_m / layer.conductivity_W_mK

        return self.Rsi + R_layers + self.Rse
    # END METHOD: _compute_R_total

    # BEGIN METHOD: _compute_C_areal
    def _compute_C_areal(self) -> float:
        """
        Compute areal heat capacity:

            C_areal = Σ(ρ * c * d) over all layers
        """
        C = 0.0
        for layer in self.layers:
            if layer.density_kg_m3 is None or layer.heat_capacity_J_kgK is None:
                continue
            if layer.thickness_m <= 0:
                continue
            C += layer.density_kg_m3 * layer.heat_capacity_J_kgK * layer.thickness_m
        return C
    # END METHOD: _compute_C_areal

# ------------------------------------------------------------
# END CLASS: Construction
# ------------------------------------------------------------

# ================================================================
# END DATA STRUCTURES
# ================================================================



# ================================================================
# BEGIN SECTION: HELPER FUNCTIONS
# ================================================================

# ------------------------------------------------------------
# BEGIN FUNCTION: make_construction
# ------------------------------------------------------------
def make_construction(
    name: str,
    layers: List[Layer],
    Rsi: float = 0.13,
    Rse: float = 0.04,
) -> Construction:
    """
    Convenience function to build a new Construction,
    compute its derived properties, and return it.
    """
    cons = Construction(name=name, layers=layers, Rsi=Rsi, Rse=Rse)
    cons.recalc()
    return cons
# ------------------------------------------------------------
# END FUNCTION: make_construction
# ------------------------------------------------------------

# ================================================================
# END SECTION: HELPER FUNCTIONS
# ================================================================
