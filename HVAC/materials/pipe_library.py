"""
pipe_library.py
----------------

HVACgooee — Pipe Library v3 (linked to materials_database)

Purpose
=======
Provide a clean, unified, extensible registry of pipe specifications.
Each specification includes:

    - Outside diameter (mm)
    - Inside diameter (mm)
    - Wall thickness (mm)
    - Roughness (mm) (inherited from material)
    - Material reference (string → materials_database)
    - Pressure rating (bar)
    - Wave-speed data (if given by material)
    - Meta fields (BSP nominal size, notes)

This module centralises physical pipe data for:

    • Hydronics (pressure-drop / velocity / Reynolds)
    • Pipe sizing engine
    • Hammer prediction plugin
    • BIM/DXF geometry
    • Acoustics add-on
    • Pump selection engine
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from HVAC_legacy.materials.materials_database import (
    PipeMaterial,
    get_material,
)


# =====================================================================
# Dataclass for pipe specification
# =====================================================================

@dataclass
class PipeSpec:
    """
    One physical pipe definition.
    """
    name: str                          # "15x1", "22x0.9", "1_inch_medium"
    material: str                      # key into materials_database
    od_mm: float                       # outside diameter
    id_mm: float                       # inside diameter
    wall_mm: float                     # wall thickness
    roughness_mm: float                # inherited from material
    pressure_rating_bar: Optional[float] = None
    bsp_nominal: Optional[str] = None  # e.g. "1/2", "3/4"
    notes: str = ""


# =====================================================================
# Internal registry
# =====================================================================

PIPE_LIBRARY: Dict[str, PipeSpec] = {}


def register_pipe(spec: PipeSpec) -> None:
    """
    Register a pipe. If material reference is invalid, raise early.
    """
    mat = get_material(spec.material)
    if mat is None:
        raise ValueError(
            f"Pipe {spec.name} references unknown material '{spec.material}'"
        )

    # Inherit roughness directly from material
    rough = getattr(mat, "roughness_mm", None)
    if rough is None:
        raise ValueError(
            f"Material '{spec.material}' has no roughness_mm defined."
        )

    spec.roughness_mm = float(rough)
    PIPE_LIBRARY[spec.name] = spec


def get_pipe(name: str) -> Optional[PipeSpec]:
    return PIPE_LIBRARY.get(name)


# =====================================================================
# Helper for creating pipe specs safely
# =====================================================================

def _pipe(name: str,
          material: str,
          od_mm: float,
          id_mm: float,
          pressure: float,
          bsp: Optional[str] = None,
          notes: str = "",
          ) -> PipeSpec:
    """
    Convenience factory for consistent definitions.
    """
    return PipeSpec(
        name=name,
        material=material,
        od_mm=float(od_mm),
        id_mm=float(id_mm),
        wall_mm=float((od_mm - id_mm) / 2.0),
        pressure_rating_bar=float(pressure),
        roughness_mm=0.0,  # overwritten in register_pipe
        bsp_nominal=bsp,
        notes=notes,
    )


# =====================================================================
# COPPER (EN 1057) — typical UK HVAC sizes
# =====================================================================

# All reference material "COPPER_EN1057" from materials_database

register_pipe(_pipe("10x0.7", "COPPER_EN1057", 10.0, 8.6, 25))
register_pipe(_pipe("12x0.7", "COPPER_EN1057", 12.0, 10.6, 25))
register_pipe(_pipe("15x0.7", "COPPER_EN1057", 15.0, 13.6, 25))
register_pipe(_pipe("22x0.9", "COPPER_EN1057", 22.0, 20.2, 25))
register_pipe(_pipe("28x0.9", "COPPER_EN1057", 28.0, 26.2, 25))
register_pipe(_pipe("35x1.0", "COPPER_EN1057", 35.0, 33.0, 25))
register_pipe(_pipe("42x1.2", "COPPER_EN1057", 42.0, 39.6, 25))
register_pipe(_pipe("54x1.2", "COPPER_EN1057", 54.0, 51.6, 25))


# =====================================================================
# PEX / MLCP
# =====================================================================

# Uses "PEX_MULTILAYER"

register_pipe(_pipe("16x2", "PEX_MULTILAYER", 16.0, 12.0, 10))
register_pipe(_pipe("20x2", "PEX_MULTILAYER", 20.0, 16.0, 10))
register_pipe(_pipe("26x3", "PEX_MULTILAYER", 26.0, 20.0, 10))
register_pipe(_pipe("32x3", "PEX_MULTILAYER", 32.0, 26.0, 10))


# =====================================================================
# CARBON STEEL (EN 10255 / BS 1387) — BSP nominal sizes
# =====================================================================

# Uses material "STEEL_MEDIUM"

register_pipe(_pipe("1/2_m", "STEEL_MEDIUM", 21.3, 18.3, 16, bsp="1/2"))
register_pipe(_pipe("3/4_m", "STEEL_MEDIUM", 26.9, 23.7, 16, bsp="3/4"))
register_pipe(_pipe("1_m",   "STEEL_MEDIUM", 33.7, 30.5, 16, bsp="1"))
register_pipe(_pipe("1_1/4_m","STEEL_MEDIUM",42.4, 39.2, 16, bsp="1-1/4"))
register_pipe(_pipe("1_1/2_m","STEEL_MEDIUM",48.3, 45.1, 16, bsp="1-1/2"))
register_pipe(_pipe("2_m",   "STEEL_MEDIUM", 60.3, 56.1, 16, bsp="2"))


# =====================================================================
# STAINLESS STEEL (Press-fit)
# =====================================================================

# A2 (304) and A4 (316) share dimensions; materials differ.

register_pipe(_pipe("22x1_SS304", "STAINLESS_A2_304", 22.0, 20.0, 16))
register_pipe(_pipe("28x1_SS304", "STAINLESS_A2_304", 28.0, 26.0, 16))

register_pipe(_pipe("22x1_SS316", "STAINLESS_A4_316", 22.0, 20.0, 16))
register_pipe(_pipe("28x1_SS316", "STAINLESS_A4_316", 28.0, 26.0, 16))


# =====================================================================
# Export list
# =====================================================================

__all__ = [
    "PipeSpec",
    "PIPE_LIBRARY",
    "register_pipe",
    "get_pipe",
]
