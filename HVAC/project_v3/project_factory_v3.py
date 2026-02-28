# ======================================================================
# HVACgooee — ProjectFactoryV3
# Phase: I/J — Intent Assembly Only
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from uuid import uuid4
from HVAC.project.project_state import ProjectState


class ProjectFactoryV3:
    """
    Authoritative ProjectState factory.

    RULES:
    - Factory MAY create empty ProjectState
    - Factory MUST NOT load from disk
    - GUI loads ProjectState directly
    """

    @classmethod
    def create_empty(cls) -> ProjectState:
        """
        Create a minimal, valid empty ProjectState.
        """
        return ProjectState(
            project_id=str(uuid4()),
            name="Untitled Project",
        )

    @classmethod
    def load(cls, *args, **kwargs):
        raise NotImplementedError(
            "ProjectFactoryV3.load() is intentionally unavailable in Phase I/J"
        )
