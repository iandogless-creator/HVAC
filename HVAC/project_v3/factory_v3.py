# ======================================================================
# HVAC/project_v3/factory_v3.py
# ======================================================================

"""
HVACgooee — Project Factory v3 (CANONICAL)

Purpose
-------
Creates empty or minimally valid projects.

LOCKED
------
• No calculations
• No derived results
• No engine imports
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from HVAC.project_v3.model_v3 import (
    ProjectModelV3,
    ProjectIdentityV3,
    ProjectUnitsV3,
    ProjectDeclaredIntentV3,
    ProjectDerivedResultsV3,
    ProjectValidityV3,
)


@dataclass(frozen=True, slots=True)
class ProjectFactoryV3:
    schema_version: str = "3.1"

    def new_empty(self, name: str = "Untitled Project") -> ProjectModelV3:
        """
        Creates an empty project.
        Validity flags all False.
        """
        identity = ProjectIdentityV3(
            project_id=str(uuid4()),
            name=name,
            schema_version=self.schema_version,
            units=ProjectUnitsV3(),
        )
        return ProjectModelV3(
            identity=identity,
            intent=ProjectDeclaredIntentV3(),
            results=ProjectDerivedResultsV3(),
            validity=ProjectValidityV3(
                heatloss_valid=False,
                hydronics_valid=False,
                pump_valid=False,
            ),
        )

    def new_minimal_heatloss_ready(self, name: str = "Heatloss Ready Project") -> ProjectModelV3:
        """
        Creates a minimally structured project intended to be *ready for input*,
        not "valid". It does NOT set validity flags True.

        Adds empty containers, and a single placeholder space dict
        so GUI/testing has something to bind to.
        """
        p = self.new_empty(name=name)
        p.intent.spaces.append({"space_id": "SPACE_001", "name": "Room 1"})
        p.intent.constructions = {}
        p.intent.design_conditions = {}
        # hydronic_intent intentionally empty
        return p
