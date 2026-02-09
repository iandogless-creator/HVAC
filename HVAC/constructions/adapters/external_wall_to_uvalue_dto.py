# ======================================================================
# HVAC/constructions/adapters/external_wall_to_uvalue_dto.py
# ======================================================================

"""
HVACgooee — External Wall Adapter v1 (CANONICAL)
-----------------------------------------------

Brick outer leaf + insulated timber stud inner leaf.

Model:
• Parallel-path (area fraction) calculation
• Studs treated as repeating thermal bridge
• Simplified ISO 6946–style approach

RULES (LOCKED)
--------------
• Performs physics ONLY
• Emits ConstructionUValueResultDTO ONLY
• No geometry, ΔT, area, layers, or notes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC_legacy.constructions.construction_preset import SurfaceClass


# ----------------------------------------------------------------------
# Surface resistances (vertical wall — CIBSE typical)
# ----------------------------------------------------------------------

R_SI_WALL = 0.12
R_SE_WALL = 0.06


# ----------------------------------------------------------------------
# Internal layer representation (adapter-private)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class _Layer:
    """
    Minimal thermal layer definition for adapter use ONLY.
    """
    conductivity_w_mk: Optional[float]
    thickness_m: Optional[float]
    r_value_m2k_w: Optional[float]


# ----------------------------------------------------------------------
# Public adapter (CANONICAL)
# ----------------------------------------------------------------------

def build_external_wall_brick_stud_uvalue_dto(
    *,
    brick_layer: _Layer,
    stud_layer: _Layer,
    insulation_layer: _Layer,
    plasterboard_layer: _Layer,
    insulation_fraction: float,
    stud_fraction: float,
    construction_id: str = "wall.external.brick_stud.uk_typical",
    rsi: float = R_SI_WALL,
    rse: float = R_SE_WALL,
) -> ConstructionUValueResultDTO:
    """
    Build U-value for a brick outer / insulated stud inner wall
    using a parallel-path (area-weighted) method.
    """

    # ------------------------------------------------------------
    # HARD INPUT ASSERTIONS (LOCKED)
    # ------------------------------------------------------------

    if abs((insulation_fraction + stud_fraction) - 1.0) > 1e-6:
        raise ValueError(
            "Parallel-path fractions must sum to 1.0\n"
            f"  insulation_fraction = {insulation_fraction}\n"
            f"  stud_fraction       = {stud_fraction}"
        )

    # ------------------------------------------------------------
    # Layer resistances
    # ------------------------------------------------------------

    r_brick = _layer_r_value(brick_layer)
    r_stud = _layer_r_value(stud_layer)
    r_insulation = _layer_r_value(insulation_layer)
    r_plasterboard = _layer_r_value(plasterboard_layer)

    # Insulation path
    r_path_insulation = (
        rsi
        + r_brick
        + r_insulation
        + r_plasterboard
        + rse
    )

    # Stud path (thermal bridge)
    r_path_stud = (
        rsi
        + r_brick
        + r_stud
        + r_plasterboard
        + rse
    )

    # Area-weighted total resistance
    r_total = (
        insulation_fraction * r_path_insulation
        + stud_fraction * r_path_stud
    )

    if r_total <= 0.0:
        raise ValueError("Computed wall resistance must be positive.")

    u_value = 1.0 / r_total

    # ------------------------------------------------------------
    # DTO EMISSION (LOCKED)
    # ------------------------------------------------------------

    return ConstructionUValueResultDTO(
        surface_class=SurfaceClass.EXTERNAL_WALL,
        construction_ref=construction_id,
        u_value=u_value,
    )


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------

def _layer_r_value(layer: _Layer) -> float:
    """
    Return thermal resistance of a layer.

    Missing or invalid data ⇒ R = 0.0 (explicit).
    """
    if (
        layer.conductivity_w_mk is None
        or layer.thickness_m is None
        or layer.conductivity_w_mk <= 0.0
        or layer.thickness_m <= 0.0
    ):
        return 0.0

    return layer.thickness_m / layer.conductivity_w_mk
