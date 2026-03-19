# ======================================================================
# HVAC/heatloss/resolution/fabric_resolver_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.heatloss.fabric.resolved_fabric_surface import ResolvedFabricSurface
from HVAC.core.value_resolution import resolve_effective_height_m


class FabricResolverV1:
    """
    Minimal topology → fabric derivation.

    Responsibilities
    ----------------
    • Reads boundary_segments
    • Uses effective height resolution helper
    • Derives wall areas (length × height)
    • Emits ResolvedFabricSurface
    • Attaches to rooms

    Does NOT:
    • Perform validation
    • Assign U-values
    • Calculate heat-loss
    """

    @staticmethod
    def resolve(project_state: ProjectState) -> None:

        # ------------------------------------------------------------
        # Clear existing derived surfaces
        # ------------------------------------------------------------
        for room in project_state.rooms.values():
            room.fabric_surfaces = []

        boundary_segments = getattr(project_state, "boundary_segments", None)
        if not boundary_segments:
            return

        # ------------------------------------------------------------
        # Process boundary segments
        # ------------------------------------------------------------
        for segment_id, segment in boundary_segments.items():

            owner_id = segment.get("owner_room_id")
            length_m = segment.get("length_m")
            kind = segment.get("boundary_kind")

            if owner_id not in project_state.rooms:
                continue

            if not length_m or float(length_m) <= 0.0:
                continue

            room = project_state.rooms[owner_id]

            # --------------------------------------------------------
            # Height resolution via helper (CLEAN)
            # --------------------------------------------------------
            height_m = resolve_effective_height_m(project_state, room)
            if height_m is None or float(height_m) <= 0.0:
                continue

            area_m2 = float(length_m) * float(height_m)

            # --------------------------------------------------------
            # Minimal scope: EXTERNAL only (IV-A)
            # --------------------------------------------------------
            if kind == "EXTERNAL":

                surface = ResolvedFabricSurface(
                    surface_id=segment_id,
                    room_id=owner_id,
                    surface_class="external_wall",
                    area_m2=area_m2,
                    u_value_W_m2K=None,
                )

                room.fabric_surfaces.append(surface)