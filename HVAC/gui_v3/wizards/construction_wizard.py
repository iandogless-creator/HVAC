# ======================================================================
# HVAC/gui_v3/wizards/construction_wizard.py
#
# Phase: IV-B — Construction Assignment (Topology-driven)
# Status: CANONICAL
#
# Purpose
# -------
# Assign construction_id to topology-derived surfaces.
#
# Authority Rules
# ---------------
# • DOES NOT create FabricElementV1
# • DOES NOT write geometry
# • DOES NOT compute physics
#
# • Writes ONLY:
#       → surface-level construction assignments (via ProjectState)
#
# Future
# ------
# • Will integrate with UI selection / surface targeting
# • Will support batch assignment (all external walls, etc.)
# ======================================================================

from __future__ import annotations

from typing import Optional, Iterable


# ======================================================================
# ConstructionWizard
# ======================================================================

class ConstructionWizard:
    """
    Assigns construction_id to topology-derived surfaces.

    This replaces legacy FabricElement authoring.
    """

    # ------------------------------------------------------------------
    # Construction assignment (single surface)
    # ------------------------------------------------------------------

    def assign_to_surface(
        self,
        *,
        project_state,
        room_id: str,
        surface_id: str,
        construction_id: str,
    ) -> None:
        """
        Assign a construction_id to a single surface.
        """

        if project_state is None:
            return

        if construction_id not in project_state.constructions:
            raise ValueError(f"Unknown construction_id: {construction_id}")

        # --------------------------------------------------
        # Ensure surface assignment store exists
        # --------------------------------------------------

        if not hasattr(project_state, "surface_construction_map"):
            project_state.surface_construction_map = {}

        # --------------------------------------------------
        # Assign
        # --------------------------------------------------

        project_state.surface_construction_map[surface_id] = construction_id

        # --------------------------------------------------
        # Mark dirty
        # --------------------------------------------------

        if hasattr(project_state, "mark_heatloss_dirty"):
            project_state.mark_heatloss_dirty()

    # ------------------------------------------------------------------
    # Batch assignment (by element type)
    # ------------------------------------------------------------------

    def assign_by_element(
        self,
        *,
        project_state,
        room,
        element: str,
        construction_id: str,
    ) -> None:
        """
        Assign construction to all surfaces of a given type.

        Example:
            element = "external_wall"
        """

        if project_state is None or room is None:
            return

        if construction_id not in project_state.constructions:
            raise ValueError(f"Unknown construction_id: {construction_id}")

        if not hasattr(project_state, "surface_construction_map"):
            project_state.surface_construction_map = {}

        # --------------------------------------------------
        # Iterate topology-derived rows
        # --------------------------------------------------

        from HVAC.heatloss.fabric.fabric_from_segments_v1 import (
            FabricFromSegmentsV1,
        )

        rows = FabricFromSegmentsV1.build_rows_for_room(project_state, room)

        for r in rows:
            if r.element == element:
                project_state.surface_construction_map[r.surface_id] = construction_id

        if hasattr(project_state, "mark_heatloss_dirty"):
            project_state.mark_heatloss_dirty()

    # ------------------------------------------------------------------
    # Batch assignment (all surfaces in room)
    # ------------------------------------------------------------------

    def assign_all(
        self,
        *,
        project_state,
        room,
        construction_id: str,
    ) -> None:
        """
        Assign same construction to all surfaces in room.
        """

        if project_state is None or room is None:
            return

        if construction_id not in project_state.constructions:
            raise ValueError(f"Unknown construction_id: {construction_id}")

        if not hasattr(project_state, "surface_construction_map"):
            project_state.surface_construction_map = {}

        from HVAC.heatloss.fabric.fabric_from_segments_v1 import (
            FabricFromSegmentsV1,
        )

        rows = FabricFromSegmentsV1.build_rows_for_room(project_state, room)

        for r in rows:
            project_state.surface_construction_map[r.surface_id] = construction_id

        if hasattr(project_state, "mark_heatloss_dirty"):
            project_state.mark_heatloss_dirty()

    # ------------------------------------------------------------------
    # Read helper (used by adapters)
    # ------------------------------------------------------------------

    @staticmethod
    def get_surface_construction(
        project_state,
        surface_id: str,
    ) -> Optional[str]:
        """
        Returns assigned construction_id for a surface.
        """

        if project_state is None:
            return None

        mapping = getattr(project_state, "surface_construction_map", None)
        if not mapping:
            return None

        return mapping.get(surface_id)

    # ------------------------------------------------------------------
    # Static entry point (used by UI / MainWindow)
    # ------------------------------------------------------------------
    @staticmethod
    def set_surface_construction(
        project_state,
        surface_id: str,
        construction_id: str,
    ) -> None:
        """
        Static convenience wrapper for assignment.

        Keeps UI code simple and avoids needing instance creation.
        """

        wizard = ConstructionWizard()

        wizard.assign_to_surface(
            project_state=project_state,
            room_id="",  # not used in current logic
            surface_id=surface_id,
            construction_id=construction_id,
        )