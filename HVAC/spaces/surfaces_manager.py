"""
surfaces_manager.py
-------------------

HVACgooee — Surfaces Manager v1

This module manages Surface objects for each Space.
In v1 it is structural only — geometry does NOT populate
surfaces yet. It is simply preparing the engine for
future geometry → surface decomposition.

SurfacesManager responsibilities:
    - store surfaces
    - associate surfaces with spaces
    - allow creation/removal later
    - provide lookup for heat-loss in v1.2+
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from HVAC_legacy.spaces.surface_types import Surface, SurfaceType


class SurfacesManager:
    """
    Structural manager for all surfaces.
    Compatible with future geometry engines.

    In v1.x:
        - Surfaces list is empty
        - No geometry logic
        - No heat-loss hooks (yet)
    """

    def __init__(self):
        # Mapping: space_id → list of surfaces
        self._surfaces: Dict[str, List[Surface]] = {}

    # --------------------------------------------------------------
    # Basic CRUD operations
    # --------------------------------------------------------------

    def add_surface(self, space_id: str, surface: Surface):
        """Add a surface to a space."""
        if space_id not in self._surfaces:
            self._surfaces[space_id] = []
        self._surfaces[space_id].append(surface)

    def clear_surfaces(self, space_id: str):
        """Remove all surfaces for given space."""
        self._surfaces[space_id] = []

    def remove_surface(self, space_id: str, surface_id: str):
        """Remove a single surface identified by its ID."""
        if space_id not in self._surfaces:
            return
        self._surfaces[space_id] = [
            s for s in self._surfaces[space_id]
            if s.surface_id != surface_id
        ]

    # --------------------------------------------------------------
    # Lookups
    # --------------------------------------------------------------

    def get_surfaces(self, space_id: str) -> List[Surface]:
        """Return list of surfaces for space. May be empty."""
        return self._surfaces.get(space_id, [])

    def all_surfaces(self) -> Dict[str, List[Surface]]:
        """Return mapping of all spaces to their surfaces."""
        return self._surfaces

    # --------------------------------------------------------------
    # Serialization (preparing for save/load)
    # --------------------------------------------------------------

    def to_dict(self) -> Dict[str, List[dict]]:
        """Convert surfaces to dict for saving project."""
        out = {}
        for space_id, surfaces in self._surfaces.items():
            out[space_id] = [s.to_dict() for s in surfaces]
        return out

    def load_from_dict(self, data: Dict[str, List[dict]]):
        """Restore surfaces from saved structure."""
        from HVAC_legacy.spaces.surface_types import Surface  # local import to avoid circularity
        self._surfaces = {}
        for sid, items in data.items():
            self._surfaces[sid] = [Surface.from_dict(d) for d in items]
