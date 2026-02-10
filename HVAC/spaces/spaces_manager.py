"""
spaces_manager.py
-----------------

HVACgooee — Spaces Manager v1 (Pipeline-Safe Extension)

This module provides the central registry for all Space objects
(Rooms, Cabins, Lofts, Pods, Workshops, etc.).

Responsibilities:
    - create spaces
    - delete spaces
    - rename spaces
    - list all spaces
    - fetch by ID
    - serialization (project save/load)
    - minimal v1 extension:
        • track an "active" space ID
        • assign geometry to the active space
        • bedsit fallback if geometry arrives before any spaces exist

Non-Responsibilities (strictly out of scope):
    - NO GUI imports
    - NO signals
    - NO heat-loss logic
    - NO templates
    - NO auto-splitting
    - NO controller side-effects
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Optional, List, Any, Tuple

from HVAC.spaces.space_types import Space, create_space


Point2D = Tuple[float, float]


class SpacesManager:
    """
    Central controller storing all Space objects in a project.
    Each space has a unique ID (S1, S2, ...).

    The GUI and other controllers interact with this manager
    rather than manipulating spaces directly.
    """

    def __init__(self):
        self._spaces: Dict[str, Space] = {}
        self._active_space_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Core Controls
    # ------------------------------------------------------------------

    def add_space(self, type_name: str, name: str) -> str:
        """
        Create a new space and return its ID (S1, S2, ...).
        Sets the new space as active.
        """
        space_id = self._next_space_id()
        self._spaces[space_id] = create_space(type_name=type_name, name=name)
        self._active_space_id = space_id
        return space_id

    def delete_space(self, space_id: str) -> bool:
        """
        Delete a space. Returns True if deleted, False if not found.
        If the active space is deleted, active space becomes:
            - another existing space (lowest ID), or None if none remain.
        """
        if space_id not in self._spaces:
            return False

        del self._spaces[space_id]

        if self._active_space_id == space_id:
            self._active_space_id = self._pick_default_active_space_id()

        return True

    def rename_space(self, space_id: str, new_name: str) -> bool:
        """Rename a space. Returns True if renamed, False if not found."""
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.name = new_name
        return True

    def list_space_ids(self) -> List[str]:
        """Return all space IDs in stable sorted order."""
        return sorted(self._spaces.keys(), key=self._space_sort_key)

    def get_space(self, space_id: str) -> Optional[Space]:
        """Fetch a Space by ID."""
        return self._spaces.get(space_id)

    def has_spaces(self) -> bool:
        return bool(self._spaces)

    # ------------------------------------------------------------------
    # Minimal v1 Extension: Active Space
    # ------------------------------------------------------------------

    def get_active_space_id(self) -> Optional[str]:
        return self._active_space_id

    def set_active_space(self, space_id: str) -> bool:
        """
        Set active space. Returns True if the ID exists, else False.
        """
        if space_id not in self._spaces:
            return False
        self._active_space_id = space_id
        return True

    def get_active_space(self) -> Optional[Space]:
        if self._active_space_id is None:
            return None
        return self._spaces.get(self._active_space_id)

    # ------------------------------------------------------------------
    # Minimal v1 Extension: Geometry Attachment
    # ------------------------------------------------------------------

    def assign_geometry_to_active_space(
        self,
        polygon: List[Point2D],
        height_m: Optional[float] = None,
    ) -> str:
        """
        Assign geometry to the active space.

        Bedsit-first fallback:
            - If no spaces exist yet, creates S1 as a default "Bedsit"
              and sets it active, then assigns geometry.

        This is pipeline-only. It MUST NOT trigger any other work.
        No signals. No heat-loss recompute. No templates.

        Returns:
            active space ID receiving the geometry.
        """
        if not polygon:
            raise ValueError("polygon is empty; refusing to assign geometry.")

        if not self._spaces:
            # Bedsit fallback (v1-safe default)
            space_id = self.add_space(type_name="bedsit", name="Bedsit")
        else:
            # Ensure we have a valid active space
            if self._active_space_id is None or self._active_space_id not in self._spaces:
                self._active_space_id = self._pick_default_active_space_id()

            if self._active_space_id is None:
                # Should be impossible because _spaces is non-empty, but keep it defensive.
                space_id = self.add_space(type_name="bedsit", name="Bedsit")
            else:
                space_id = self._active_space_id

        space = self._spaces[space_id]

        # Attach geometry (canonical v1 fields expected on Space)
        if not hasattr(space, "polygon"):
            raise AttributeError("Space object has no 'polygon' attribute (expected in v1).")
        space.polygon = list(polygon)

        if height_m is not None:
            if not hasattr(space, "height_m"):
                raise AttributeError("Space object has no 'height_m' attribute (expected in v1).")
            space.height_m = float(height_m)

        return space_id

    # ------------------------------------------------------------------
    # Serialization (Project Save/Load)
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize manager state.
        Backwards/forwards safe:
            - includes active_space_id (new)
            - stores spaces as {id: asdict(space)}
        """
        return {
            "spaces": {sid: asdict(space) for sid, space in self._spaces.items()},
            "active_space_id": self._active_space_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpacesManager":
        """
        Deserialize manager state.

        Backwards compatible:
            - if active_space_id missing, chooses a sensible default
        """
        mgr = cls()

        raw_spaces = (data or {}).get("spaces", {}) or {}
        for sid, sdata in raw_spaces.items():
            # Rehydrate using Space(**dict). This assumes Space is a dataclass
            # and the saved keys match the current v1 Space fields.
            mgr._spaces[sid] = Space(**sdata)

        mgr._active_space_id = (data or {}).get("active_space_id")

        # Repair active space if missing/invalid
        if mgr._active_space_id not in mgr._spaces:
            mgr._active_space_id = mgr._pick_default_active_space_id()

        return mgr

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _next_space_id(self) -> str:
        """
        Determine next space ID (S1, S2, ...), stable and monotonic
        based on existing IDs.
        """
        if not self._spaces:
            return "S1"

        max_n = 0
        for sid in self._spaces.keys():
            if sid.startswith("S"):
                try:
                    n = int(sid[1:])
                    max_n = max(max_n, n)
                except ValueError:
                    continue
        return f"S{max_n + 1}"

    def _pick_default_active_space_id(self) -> Optional[str]:
        """
        Choose a deterministic active space ID when needed:
            - lowest numeric S# if present
            - else lexicographically smallest key
            - else None
        """
        if not self._spaces:
            return None

        s_ids = list(self._spaces.keys())
        s_ids.sort(key=self._space_sort_key)
        return s_ids[0] if s_ids else None

    @staticmethod
    def _space_sort_key(space_id: str) -> Tuple[int, str]:
        """
        Sort primarily by numeric suffix for IDs like S12, else push nonconforming IDs later.
        """
        if space_id.startswith("S"):
            try:
                return (0, f"{int(space_id[1:]):09d}")
            except ValueError:
                pass
        return (1, space_id)
