# ======================================================================
# HVAC/io_v3/serializer_v3.py
# ======================================================================

"""
Project Serializer v3

LOCKED:
• Pure ProjectModelV3 ⇄ dict
• No filesystem access
"""

from __future__ import annotations
from typing import Dict, Any

from HVAC.project_v3.model_v3 import ProjectModelV3


def project_to_dict(project: ProjectModelV3) -> Dict[str, Any]:
    return {
        "schema_version": project.identity.schema_version,
        "identity": {
            "project_id": project.identity.project_id,
            "name": project.identity.name,
            "units": vars(project.identity.units),
        },
        "intent": {
            "spaces": project.intent.spaces,
            "constructions": project.intent.constructions,
            "design_conditions": project.intent.design_conditions,
            "hydronic_intent": project.intent.hydronic_intent,
        },
        "results": {
            "heatloss_result": project.results.heatloss_result,
            "hydronics_result": project.results.hydronics_result,
            "pump_result": project.results.pump_result,
        },
        "validity": {
            "heatloss_valid": project.validity.heatloss_valid,
            "hydronics_valid": project.validity.hydronics_valid,
            "pump_valid": project.validity.pump_valid,
        },
    }


def project_from_dict(data: Dict[str, Any]) -> ProjectModelV3:
    from HVAC.project_v3.model_v3 import (
        ProjectIdentityV3,
        ProjectUnitsV3,
        ProjectDeclaredIntentV3,
        ProjectDerivedResultsV3,
        ProjectValidityV3,
    )

    identity = ProjectIdentityV3(
        project_id=data["identity"]["project_id"],
        name=data["identity"]["name"],
        schema_version=data.get("schema_version", "3.1"),
        units=ProjectUnitsV3(**data["identity"]["units"]),
    )

    project = ProjectModelV3(identity=identity)

    project.intent = ProjectDeclaredIntentV3(
        spaces=data["intent"].get("spaces", []),
        constructions=data["intent"].get("constructions", {}),
        design_conditions=data["intent"].get("design_conditions", {}),
        hydronic_intent=data["intent"].get("hydronic_intent", {}),
    )

    project.results = ProjectDerivedResultsV3(**data.get("results", {}))
    project.validity = ProjectValidityV3(**data.get("validity", {}))

    return project
