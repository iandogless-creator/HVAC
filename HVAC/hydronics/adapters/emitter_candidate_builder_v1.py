# ======================================================================
# HVAC/hydronics/adapters/emitter_candidate_builder_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.hydronics.emitter_v1 import EmitterV1


class EmitterCandidateBuilderV1:
    """
    Hydronics H-C — default terminal emitter candidate bootstrap.

    Responsibilities
    ----------------
    • Create one default emitter candidate for each room that has none
    • Preserve existing emitters
    • Support future multiple emitters per room

    Explicitly forbidden
    --------------------
    • no heat-loss calculation
    • no radiator sizing
    • no air-system sizing
    • no pipe sizing
    • no pump sizing
    • no pressure-loss calculation
    """

    def ensure_default_emitters(self, project: ProjectState) -> int:
        """
        Create one default radiator candidate for each room that has no emitters.

        Returns
        -------
        int
            Number of emitters created.
        """
        created = 0

        rooms = getattr(project, "rooms", {}) or {}
        emitters = getattr(project, "emitters", {}) or {}

        for room_id, room in rooms.items():
            # --------------------------------------------------
            # A room may have many emitters later.
            # H-C creates one default candidate only if none exist.
            # --------------------------------------------------
            if any(
                getattr(emitter, "room_id", None) == room_id
                for emitter in emitters.values()
            ):
                continue

            room_name = (
                getattr(room, "name", None)
                or getattr(room, "label", None)
                or room_id
            )

            emitter_id = self._make_emitter_id(project, room_id)

            project.emitters[emitter_id] = EmitterV1(
                emitter_id=emitter_id,
                room_id=room_id,
                name=f"Emitter — {room_name}",
                emitter_type="radiator",
                design_output_W=None,
                flow_temp_C=None,
                return_temp_C=None,
                room_temp_C=None,
                notes="Default H-C emitter candidate",
            )

            created += 1

        return created

    def _make_emitter_id(
        self,
        project: ProjectState,
        room_id: str,
    ) -> str:
        base = f"emitter-rad-{room_id}-001"

        emitters = getattr(project, "emitters", {}) or {}
        if base not in emitters:
            return base

        index = 2
        while True:
            candidate = f"emitter-rad-{room_id}-{index:03d}"
            if candidate not in emitters:
                return candidate

            index += 1