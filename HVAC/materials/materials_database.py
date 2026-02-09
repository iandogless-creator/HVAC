"""
materials_database.py
---------------------

HVACgooee — Unified Materials Database (v1)

Purpose
=======
Provide a central, extensible, data-driven materials database for all
subsystems:

    • Heat-loss (U-values, Y-values)
    • Constructions and layers
    • Hydronic materials (pipe wall, roughness, wave speed, density)
    • Acoustics add-ons (future)
    • Fire resistance / lighting (future plugins)

Design
------
This file exposes:

    • Base class:     Material
    • Sub-classes:    LayerMaterial (heat-loss), PipeMaterial (hydronics)
    • Registry:       MATERIALS_DB  (dict[name → Material])
    • Loader API:     register_material(), get_material()

Plugins may register their own materials without modifying this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any


# ============================================================================
# Base material type
# ============================================================================

@dataclass
class Material:
    """
    Base material object — minimal common core.
    """
    name: str
    category: str                   # "pipe", "layer", "insulation", "metal", …
    density_kg_m3: Optional[float] = None
    thermal_conductivity_W_mK: Optional[float] = None
    notes: str = ""


# ============================================================================
# Heat-loss specific material (U-value layers)
# ============================================================================

@dataclass
class LayerMaterial(Material):
    """
    Layer used in heat-loss U-value calculations (ISO 6946).
    """
    specific_heat_J_kgK: Optional[float] = None
    vapour_resistance_MNs_g: Optional[float] = None


# ============================================================================
# Pipe material — hydronic properties
# ============================================================================

@dataclass
class PipeMaterial(Material):
    """
    Material used for hydronic pipe physics.

    These values can be refined later or made temperature-dependent.
    """
    roughness_mm: float = 0.0
    elastic_modulus_GPa: Optional[float] = None
    wave_speed_m_s: Optional[float] = None
    corrosion_note: str = ""        # compatibility hint (for plugins)


# ============================================================================
# Registry
# ============================================================================

MATERIALS_DB: Dict[str, Material] = {}


def register_material(mat: Material) -> None:
    """
    Register or replace a material safely.
    """
    MATERIALS_DB[mat.name] = mat


def get_material(name: str) -> Optional[Material]:
    """
    Retrieve a material by name.
    """
    return MATERIALS_DB.get(name)


# ============================================================================
# Preload core materials
# ============================================================================

# --- Copper (EN 1057) ---
register_material(
    PipeMaterial(
        name="COPPER_EN1057",
        category="pipe",
        density_kg_m3=8900,
        thermal_conductivity_W_mK=385,
        roughness_mm=0.0015,
        elastic_modulus_GPa=110,
        wave_speed_m_s=1100,
        corrosion_note="Incompatible with galvanised steel in shared loop (risk of galvanic cell)",
        notes="Standard refrigeration/heating copper."
    )
)

# --- PEX / MLCP ---
register_material(
    PipeMaterial(
        name="PEX_MULTILAYER",
        category="pipe",
        density_kg_m3=950,
        thermal_conductivity_W_mK=0.35,
        roughness_mm=0.007,
        elastic_modulus_GPa=0.5,
        wave_speed_m_s=350,
        corrosion_note="Always use oxygen-barrier grade (EVOH).",
        notes="Plastic multilayer pipe (PEX-Al-PEX)."
    )
)

# --- Carbon steel (EN 10255 / BS1387 medium) ---
register_material(
    PipeMaterial(
        name="STEEL_MEDIUM",
        category="pipe",
        density_kg_m3=7850,
        thermal_conductivity_W_mK=50,
        roughness_mm=0.045,
        elastic_modulus_GPa=200,
        wave_speed_m_s=1200,
        corrosion_note="Requires inhibitor with aluminium circuits. Can cause magnetite.",
        notes="Common for commercial/plant rooms."
    )
)

# --- Stainless steel AISI 304 ---
register_material(
    PipeMaterial(
        name="STAINLESS_A2_304",
        category="pipe",
        density_kg_m3=8000,
        thermal_conductivity_W_mK=16,
        roughness_mm=0.015,
        elastic_modulus_GPa=193,
        wave_speed_m_s=5000,
        corrosion_note="OK with copper. Avoid chloride-rich environments.",
        notes="A2 stainless, architectural / general use."
    )
)

# --- Stainless steel AISI 316 (marine grade) ---
register_material(
    PipeMaterial(
        name="STAINLESS_A4_316",
        category="pipe",
        density_kg_m3=8000,
        thermal_conductivity_W_mK=14,
        roughness_mm=0.015,
        elastic_modulus_GPa=190,
        wave_speed_m_s=4800,
        corrosion_note="Excellent corrosion resistance. Safe with copper + aluminium.",
        notes="Marine grade. Good for aggressive water chemistry."
    )
)

# --- Simple insulation sample (heat-loss) ---
register_material(
    LayerMaterial(
        name="MINERAL_WOOL",
        category="layer",
        density_kg_m3=30,
        thermal_conductivity_W_mK=0.035,
        specific_heat_J_kgK=840,
        notes="General thermal insulation."
    )
)

# --- Dense masonry (heat-loss) ---
register_material(
    LayerMaterial(
        name="DENSE_BLOCK",
        category="layer",
        density_kg_m3=1800,
        thermal_conductivity_W_mK=1.1,
        specific_heat_J_kgK=840,
        notes="Dense concrete block for fabric calculations."
    )
)

# ============================================================================
# Future expansion points (kept blank intentionally)
# ============================================================================

# AcousticMaterial (RT60 modelling plugin)
# LightingMaterial (LOR, CCT, CRI, lens profile)
# FireMaterial (EN 13501-1 classes)
# MoistureMaterial (vapour diffusion studies)

