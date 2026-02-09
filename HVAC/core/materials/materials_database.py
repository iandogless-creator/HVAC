"""
HVACgooee — Materials & Conductivity Database (Core v1)
=======================================================

This module provides:
- A structured material database
- Conductivities (λ), densities, specific heat
- Legacy ENV/CIBSE material set (Environmental-era)
- Modern material entries
- JSON import/export
- Simple/Advanced/Educational access patterns

Design Rules
------------
- Pure data + physics helpers.
- No GUI.
- No filepaths hardcoded; caller decides where to read/write JSON.
- Internal dict-based storage so plugin packs can add materials.

Future expansions:
------------------
- Hygroscopic parameters
- Moisture content corrections
- Proprietary insulation manufacturers (user-addons)
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
import json


# ---------------------------------------------------------------------------
# Data Structure
# ---------------------------------------------------------------------------

@dataclass
class Material:
    name: str
    lambda_W_mK: float                # thermal conductivity
    density_kg_m3: Optional[float]    # density
    specific_heat_J_kgK: Optional[float]  # specific heat capacity
    category: str = "generic"         # e.g. insulation, masonry, glazing, timber
    notes: str = ""                   # optional free text


# ---------------------------------------------------------------------------
# Default Material Library (Legacy + Modern Mixed)
# ---------------------------------------------------------------------------

def default_materials() -> Dict[str, Material]:
    """
    Combined legacy + modern baseline materials.
    These are intentionally minimal — larger tables will be loaded via JSON.
    """
    mats = {
        # --- Legacy environmental / CIBSE style entries ---
        "brick_solid": Material(
            name="Brick (solid)",
            lambda_W_mK=0.77,
            density_kg_m3=1800,
            specific_heat_J_kgK=840,
            category="masonry",
            notes="Legacy ENV typical value",
        ),
        "brick_hollow": Material(
            name="Brick (hollow)",
            lambda_W_mK=0.35,
            density_kg_m3=1200,
            specific_heat_J_kgK=840,
            category="masonry",
        ),
        "plasterboard": Material(
            name="Plasterboard",
            lambda_W_mK=0.19,
            density_kg_m3=950,
            specific_heat_J_kgK=1000,
            category="lining",
        ),
        "mineral_wool": Material(
            name="Mineral wool insulation",
            lambda_W_mK=0.035,
            density_kg_m3=30,
            specific_heat_J_kgK=840,
            category="insulation",
        ),
        "timber_softwood": Material(
            name="Timber (softwood)",
            lambda_W_mK=0.13,
            density_kg_m3=500,
            specific_heat_J_kgK=1600,
            category="timber",
            notes="Used for joist bridging calculations",
        ),

        # --- Modern common materials ---
        "xps": Material(
            name="XPS insulation",
            lambda_W_mK=0.030,
            density_kg_m3=35,
            specific_heat_J_kgK=1450,
            category="insulation",
        ),
        "eps": Material(
            name="EPS insulation",
            lambda_W_mK=0.031,
            density_kg_m3=15,
            specific_heat_J_kgK=1450,
            category="insulation",
        ),
        "celotex_pir": Material(
            name="PIR insulation (generic)",
            lambda_W_mK=0.022,
            density_kg_m3=32,
            specific_heat_J_kgK=1400,
            category="insulation",
            notes="Represents typical PIR e.g. Celotex, Kingspan",
        ),
        "gypsum_plaster": Material(
            name="Gypsum plaster",
            lambda_W_mK=0.52,
            density_kg_m3=900,
            specific_heat_J_kgK=840,
            category="lining",
        ),
        "concrete_dense": Material(
            name="Concrete (dense)",
            lambda_W_mK=1.75,
            density_kg_m3=2300,
            specific_heat_J_kgK=880,
            category="masonry",
        ),
    }
    return mats


# ---------------------------------------------------------------------------
# Materials Database Class
# ---------------------------------------------------------------------------

class MaterialsDatabase:
    """
    In-memory material library with add/remove/update functionality.

    Supports:
    - load from defaults
    - merge JSON material packs
    - export to JSON
    - lookup by key
    - search by category
    """

    def __init__(self):
        self._materials: Dict[str, Material] = default_materials()

    # ----- Core API ---------------------------------------------------------

    def list_keys(self) -> List[str]:
        return sorted(self._materials.keys())

    def get(self, key: str) -> Optional[Material]:
        return self._materials.get(key)

    def add(self, key: str, material: Material) -> None:
        self._materials[key] = material

    def remove(self, key: str) -> None:
        if key in self._materials:
            del self._materials[key]

    def search(self, category: str) -> Dict[str, Material]:
        return {k: v for k, v in self._materials.items() if v.category == category}

    # ----- JSON I/O ---------------------------------------------------------

    def load_json(self, json_str: str, overwrite: bool = False) -> None:
        """
        Load materials from a JSON string.

        If overwrite=True, replaces entire database.
        If overwrite=False, merges new keys (existing keys overridden).
        """
        data = json.loads(json_str)
        if overwrite:
            self._materials = {}

        for key, mat_dict in data.items():
            self._materials[key] = Material(**mat_dict)

    def to_json(self, indent: int = 2) -> str:
        """
        Export current materials to JSON.
        """
        data = {k: asdict(v) for k, v in self._materials.items()}
        return json.dumps(data, indent=indent)
