# ======================================================================
# HVAC/project_v3/project_factory_v3.py
# ======================================================================

"""
HVACgooee — Project Factory v3 (CANONICAL, MINIMAL)

Responsibilities
----------------
• Sole authority for ProjectV3 creation
• Headless (NO GUI imports)
• No calculations
• No persistence
• Safe empty-project creation for GUI boot
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from HVAC_legacy.project_v3.project_models_v3 import (
    ProjectV3,
    ProjectMetaV3,
    ConstructionsV3,
    HeatLossV3,
    HydronicsV3,
)


class ProjectFactoryV3:
    """
    Canonical v3 project factory.

    This class is the ONLY authority allowed to create ProjectV3
    instances for GUI and runners.
    """

    # ------------------------------------------------------------------
    # Empty project (GUI boot path)
    # ------------------------------------------------------------------
    @classmethod
    def create_empty(cls) -> ProjectV3:
        """
        Create a valid but empty ProjectV3.

        Guarantees:
        • GUI can load without special-casing
        • No rooms
        • No constructions
        • No results
        • All subsystems present and marked invalid
        """

        meta = ProjectMetaV3(
            project_id="NEW",
            name="Untitled Project",
            description="Empty HVACgooee project",
            created_uk="",
            schema_version="project_v3",
            status="draft",
        )

        return ProjectV3(
            project_meta=meta,
            project_info={},
            spaces=[],
            constructions=ConstructionsV3(
                presets={},
                results=[],
                valid=False,
            ),
            heatloss=HeatLossV3(
                valid=False,
                qt_w=None,
                results=None,
            ),
            hydronics=HydronicsV3(
                valid=False,
                system_type="two_pipe_direct_return",
                emitters=[],
                results=None,
            ),
            project_state=None,
            project_dir=None,
        )

    # ------------------------------------------------------------------
    # Placeholder for future loaders (LOCKED boundary)
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, project_dir: Path) -> ProjectV3:
        """
        Load a ProjectV3 from disk.

        NOTE:
        This is intentionally NOT implemented in the minimal factory.
        """
        raise NotImplementedError(
            "ProjectFactoryV3.load() not implemented in minimal v1"
        )
