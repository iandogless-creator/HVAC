# ============================================================
# HVACgooee — Heat-Loss Surfaces Manager v1
# File: HVAC/heatloss/surfaces/surfaces_manager_v1.py
# ============================================================

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from HVAC_legacy.heatloss.surfaces.surface_generation_v1 import (
    SurfaceV1,
    generate_surfaces_for_space_v1,
)


class HeatLossSurfacesManagerV1:
    """
    Stores heat-loss surfaces derived from space geometry (v1).

    v1 rules:
    - Surfaces are GENERATED, not edited
    - One surface set per space
    - No adjacency
    - No constructions
    - No U-values
    - No physics
    """

    def __init__(self):
        # key: space_id (e.g. "S1")
        self._surfaces_by_space: Dict[str, List[SurfaceV1]] = {}

    # --------------------------------------------------
    # Generation
    # --------------------------------------------------

    def generate_for_space(self, *, space, space_id: str) -> List[SurfaceV1]:
        """
        Generate and store surfaces for a single space.

        Existing surfaces for this space are replaced.
        """
        surfaces = generate_surfaces_for_space_v1(space, space_key=space_id)
        self._surfaces_by_space[space_id] = surfaces
        return surfaces

    def regenerate_all(self, *, spaces_manager) -> None:
        """
        Regenerate surfaces for ALL spaces in a project.

        v1 assumption:
        - Every space has external walls
        """
        self._surfaces_by_space.clear()

        for space_id in spaces_manager.list_space_ids():
            space = spaces_manager._spaces[space_id]
            self.generate_for_space(space=space, space_id=space_id)

    # --------------------------------------------------
    # Access
    # --------------------------------------------------

    def has_surfaces(self, space_id: str) -> bool:
        return space_id in self._surfaces_by_space

    def get_surfaces(self, space_id: str) -> List[SurfaceV1]:
        return list(self._surfaces_by_space.get(space_id, []))

    def get_all_surfaces(self) -> Dict[str, List[SurfaceV1]]:
        return {sid: list(surfs) for sid, surfs in self._surfaces_by_space.items()}

    # --------------------------------------------------
    # Serialization (v1-safe)
    # --------------------------------------------------

    def to_dict(self) -> dict:
        """
        Convert surfaces to plain Python data for project save.
        """
        return {
            "surfaces_by_space": {
                sid: [asdict(s) for s in surfaces]
                for sid, surfaces in self._surfaces_by_space.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> HeatLossSurfacesManagerV1:
        """
        Restore surfaces from saved project data.
        """
        mgr = cls()
        raw = data.get("surfaces_by_space", {}) or {}

        for sid, surface_dicts in raw.items():
            mgr._surfaces_by_space[sid] = [
                SurfaceV1(**sd) for sd in surface_dicts
            ]

        return mgr

    # --------------------------------------------------
    # Maintenance
    # --------------------------------------------------

    def clear(self) -> None:
        self._surfaces_by_space.clear()
