"""
construction_tree.py
--------------------

HVACgooee — Construction Tree v1 (LOCKED)

Pure organisational hierarchy for ConstructionPreset selection.

RULES (V3 LOCKED)
----------------
• No physics
• No GUI imports
• No engine imports
• Tree stores *preset refs only*
• Registry remains authoritative for data
• Two levels max below SurfaceClass

Hierarchy:
    SurfaceClass
        → Family
            → Variant
                → preset_ref
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


from HVAC.constructions.construction_preset import SurfaceClass


# ------------------------------------------------------------------
# Core Nodes
# ------------------------------------------------------------------

@dataclass(frozen=True)
class ConstructionVariant:
    """
    Leaf node.

    Holds exactly ONE reference to a ConstructionPreset (by ref).
    """
    name: str
    preset_ref: str


@dataclass(frozen=True)
class ConstructionFamily:
    """
    Groups similar construction variants.

    Example:
        "Masonry"
        "Timber Frame"
        "Metal Clad"
    """
    name: str
    variants: List[ConstructionVariant]


@dataclass(frozen=True)
class ConstructionSurfaceGroup:
    """
    Root grouping for a SurfaceClass.
    """
    surface_class: SurfaceClass
    families: List[ConstructionFamily]


# ------------------------------------------------------------------
# Tree Container
# ------------------------------------------------------------------

@dataclass(frozen=True)
class ConstructionTree:
    """
    Canonical Construction Tree (v1).

    Organises ConstructionPresets by:
        SurfaceClass → Family → Variant → preset_ref
    """
    surfaces: Dict[SurfaceClass, ConstructionSurfaceGroup]

    # --------------------------------------------------------------
    # Query helpers (GUI-safe)
    # --------------------------------------------------------------

    def list_surface_classes(self) -> List[SurfaceClass]:
        return list(self.surfaces.keys())

    def list_families(
        self, surface_class: SurfaceClass
    ) -> List[ConstructionFamily]:
        group = self.surfaces.get(surface_class)
        return group.families if group else []

    def list_variants(
        self, surface_class: SurfaceClass, family_name: str
    ) -> List[ConstructionVariant]:
        group = self.surfaces.get(surface_class)
        if not group:
            return []

        for fam in group.families:
            if fam.name == family_name:
                return fam.variants

        return []
