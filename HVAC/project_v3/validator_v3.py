# ======================================================================
# HVAC/project_v3/validator_v3.py
# ======================================================================

"""
HVACgooee — Project Validator v3 (CANONICAL)

Purpose
-------
Enforces structural correctness and lifecycle invariants.

LOCKED
------
• Returns diagnostics only
• Never mutates ProjectModelV3
• Validity is explicit; validator checks consistency with rules
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from HVAC.project_v3.diagnostics_v3 import DiagnosticV3, SeverityV3
from HVAC.project_v3.model_v3 import ProjectModelV3


@dataclass(frozen=True, slots=True)
class ProjectValidatorV3:
    """
    Stateless validator.
    """

    def validate(self, project: ProjectModelV3) -> List[DiagnosticV3]:
        diags: List[DiagnosticV3] = []

        # ----------------------------
        # Structural checks
        # ----------------------------
        if not project.identity.project_id:
            diags.append(DiagnosticV3(
                severity=SeverityV3.ERROR,
                code="PROJECT_ID_MISSING",
                message="Project identity.project_id must be non-empty.",
                path="identity.project_id",
            ))

        if not project.identity.name:
            diags.append(DiagnosticV3(
                severity=SeverityV3.ERROR,
                code="PROJECT_NAME_MISSING",
                message="Project identity.name must be non-empty.",
                path="identity.name",
            ))

        # ----------------------------
        # Lifecycle prerequisites (v3.1 bootstrap)
        # ----------------------------
        has_spaces = len(project.intent.spaces) >= 1
        has_constructions = bool(project.intent.constructions)
        has_design_conditions = bool(project.intent.design_conditions)
        has_hydronic_intent = bool(project.intent.hydronic_intent)

        # Heat-loss validity consistency
        if project.validity.heatloss_valid:
            if not has_spaces:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.ERROR,
                    code="HEATLOSS_VALID_BUT_NO_SPACES",
                    message="heatloss_valid=True requires ≥1 space declared.",
                    path="validity.heatloss_valid",
                ))
            if not has_constructions:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.ERROR,
                    code="HEATLOSS_VALID_BUT_NO_CONSTRUCTIONS",
                    message="heatloss_valid=True requires constructions declared.",
                    path="validity.heatloss_valid",
                ))
            if not has_design_conditions:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.ERROR,
                    code="HEATLOSS_VALID_BUT_NO_DESIGN_CONDITIONS",
                    message="heatloss_valid=True requires design conditions declared.",
                    path="validity.heatloss_valid",
                ))
            if project.results.heatloss_result is None:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.WARNING,
                    code="HEATLOSS_VALID_BUT_NO_RESULT",
                    message="heatloss_valid=True but heatloss_result is missing (expected result snapshot).",
                    path="results.heatloss_result",
                ))

        # Hydronics validity consistency
        if project.validity.hydronics_valid:
            if not project.validity.heatloss_valid:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.ERROR,
                    code="HYDRONICS_VALID_BUT_HEATLOSS_INVALID",
                    message="hydronics_valid=True requires heatloss_valid=True.",
                    path="validity.hydronics_valid",
                ))
            if not has_hydronic_intent:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.ERROR,
                    code="HYDRONICS_VALID_BUT_NO_HYDRONIC_INTENT",
                    message="hydronics_valid=True requires hydronic intent to be declared.",
                    path="intent.hydronic_intent",
                ))
            if project.results.hydronics_result is None:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.WARNING,
                    code="HYDRONICS_VALID_BUT_NO_RESULT",
                    message="hydronics_valid=True but hydronics_result is missing (expected result snapshot).",
                    path="results.hydronics_result",
                ))

        # Pump validity consistency
        if project.validity.pump_valid:
            if not project.validity.hydronics_valid:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.ERROR,
                    code="PUMP_VALID_BUT_HYDRONICS_INVALID",
                    message="pump_valid=True requires hydronics_valid=True.",
                    path="validity.pump_valid",
                ))
            if project.results.pump_result is None:
                diags.append(DiagnosticV3(
                    severity=SeverityV3.WARNING,
                    code="PUMP_VALID_BUT_NO_RESULT",
                    message="pump_valid=True but pump_result is missing (expected result snapshot).",
                    path="results.pump_result",
                ))

        return diags
