"""
pipe_materials_library.py

Standardised pipe material database for HVACgooee.

Contains:
    - PipeMaterial: roughness, conductivity
    - PipeSize: DN, OD, ID
    - Library of common materials:
        * Copper EN 1057
        * Carbon steel (medium / heavy)
        * MLCP
        * PEX / PEX-AL-PEX
        * PVC/ABS (future duct use)
    - Lookup utilities:
        * get_internal_diameter(material, nominal_size)
        * get_roughness(material)
        * list_nominal_sizes(material)
        * nearest_size(material, inner_diameter)

These values match typical UK/EU HVAC design references (BSRIA, CIBSE).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class PipeSize:
    dn: int             # DN15, DN20, etc
    od_mm: float        # outside diameter
    id_mm: float        # internal diameter
    thickness_mm: float


@dataclass
class PipeMaterial:
    name: str
    roughness_mm: float
    conductivity_W_mK: float
    density_kg_m3: float
    sizes: Dict[int, PipeSize]   # key: DN (15, 20, 25, ...)


# ---------------------------------------------------------------------------
# LIBRARY DATA
# ---------------------------------------------------------------------------

# Values based on EN 1057 — typical plumbing copper sizes
COPPER_EN1057 = PipeMaterial(
    name="Copper EN1057",
    roughness_mm=0.0015,
    conductivity_W_mK=380.0,
    density_kg_m3=8900.0,
    sizes={
        10: PipeSize(10, 12.0, 10.0, 1.0),
        15: PipeSize(15, 15.0, 13.0, 1.0),
        22: PipeSize(22, 22.0, 20.0, 1.0),
        28: PipeSize(28, 28.0, 26.0, 1.0),
        35: PipeSize(35, 35.0, 32.0, 1.5),
        42: PipeSize(42, 42.0, 38.0, 2.0),
        54: PipeSize(54, 54.0, 50.0, 2.0),
    }
)

# Carbon steel rough estimate (medium wall)
STEEL_MEDIUM = PipeMaterial(
    name="Steel Medium",
    roughness_mm=0.045,
    conductivity_W_mK=50.0,
    density_kg_m3=7850.0,
    sizes={
        15: PipeSize(15, 21.3, 17.0, 2.15),
        20: PipeSize(20, 26.9, 21.6, 2.65),
        25: PipeSize(25, 33.7, 27.2, 3.25),
        32: PipeSize(32, 42.4, 35.1, 3.65),
        40: PipeSize(40, 48.3, 40.8, 3.75),
        50: PipeSize(50, 60.3, 52.5, 3.9),
        65: PipeSize(65, 76.1, 66.7, 4.7),
        80: PipeSize(80, 88.9, 78.1, 5.4),
    }
)

# PEX / MLCP typical manufacturer values
MLCP = PipeMaterial(
    name="MLCP",
    roughness_mm=0.007,
    conductivity_W_mK=0.4,
    density_kg_m3=940.0,
    sizes={
        16: PipeSize(16, 16.0, 12.0, 2.0),
        20: PipeSize(20, 20.0, 16.0, 2.0),
        26: PipeSize(26, 26.0, 20.0, 3.0),
        32: PipeSize(32, 32.0, 26.0, 3.0),
    }
)

PEX_AL_PEX = PipeMaterial(
    name="PEX-AL-PEX",
    roughness_mm=0.007,
    conductivity_W_mK=0.4,
    density_kg_m3=940.0,
    sizes={
        16: PipeSize(16, 16.0, 12.0, 2.0),
        20: PipeSize(20, 20.0, 16.0, 2.0),
        26: PipeSize(26, 26.0, 20.0, 3.0),
    }
)

PVC_ABS = PipeMaterial(
    name="PVC/ABS",
    roughness_mm=0.009,
    conductivity_W_mK=0.17,
    density_kg_m3=1400.0,
    sizes={
        50: PipeSize(50, 50.0, 46.0, 2.0),
        63: PipeSize(63, 63.0, 58.0, 2.5),
        75: PipeSize(75, 75.0, 70.0, 2.5),
    }
)


# ---------------------------------------------------------------------------
# MASTER LIBRARY
# ---------------------------------------------------------------------------

PIPE_LIBRARY = {
    "copper": COPPER_EN1057,
    "steel": STEEL_MEDIUM,
    "mlcp": MLCP,
    "pex": PEX_AL_PEX,
    "pvc": PVC_ABS,
}


# ---------------------------------------------------------------------------
# LOOKUP FUNCTIONS
# ---------------------------------------------------------------------------

def get_material(name: str) -> Optional[PipeMaterial]:
    return PIPE_LIBRARY.get(name.lower())


def list_materials() -> List[str]:
    return list(PIPE_LIBRARY.keys())


def list_nominal_sizes(material: str) -> List[int]:
    m = get_material(material)
    if not m:
        return []
    return list(m.sizes.keys())


def get_internal_diameter(material: str, dn: int) -> Optional[float]:
    m = get_material(material)
    if not m:
        return None
    if dn not in m.sizes:
        return None
    return m.sizes[dn].id_mm


def get_roughness(material: str) -> Optional[float]:
    m = get_material(material)
    if not m:
        return None
    return m.roughness_mm


def nearest_size(material: str, id_mm: float) -> Optional[int]:
    """
    Returns DN nearest to a given inner diameter.
    Used when solver produces unusual pipe sizes.
    """
    m = get_material(material)
    if not m:
        return None

    best_dn = None
    best_err = 1e99

    for dn, size in m.sizes.items():
        err = abs(size.id_mm - id_mm)
        if err < best_err:
            best_err = err
            best_dn = dn

    return best_dn
