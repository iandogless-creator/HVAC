"""
u_value_engine.py
-----------------

Legacy compatibility shim for older imports.

All real U-value logic now lives in:

    HVAC/heatloss/physics/constructions.py
    HVAC/heatloss/physics/u_value_engine_v2.py

This file exists ONLY to prevent import errors from older modules.
It exposes:

    • Layer   – imported from constructions.py
    • compute_u_for_layers – simple helper for legacy engines
"""

from __future__ import annotations

from typing import List

from HVAC_legacy.heatloss.physics.constructions import Construction, Layer


def compute_u_for_layers(layers: List[Layer], Rsi: float = 0.13, Rse: float = 0.04) -> float:
    """
    Legacy helper.

    Compute U-value of a list of layers using simple:

        R_total = Rsi + Σ(d/λ) + Rse
        U = 1 / R_total

    Used by older engines that imported compute_u_for_layers from here.
    """
    R_layers = 0.0
    for layer in layers:
        if layer.conductivity_W_mK > 0 and layer.thickness_m > 0:
            R_layers += layer.thickness_m / layer.conductivity_W_mK

    R_total = Rsi + R_layers + Rse
    return 1.0 / R_total if R_total > 0 else 0.0
S