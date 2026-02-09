# ======================================================================
# HVACgooee — Heat-Loss Execution Validator
# Phase: Pre-G — Validation
# Version: V1
# Status: FROZEN
# ======================================================================

from __future__ import annotations

from typing import Any, List

from HVAC_legacy.heatloss.validation.validation_dto import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationStatus,
)


class HeatLossExecutionValidatorV1:
    """
    Minimal, read-only execution validator for heat-loss.
    """

    def validate(self, project_state: Any) -> ValidationReport:
        issues: List[ValidationIssue] = []

        # ---- Environment ------------------------------------------------
        if not self._has_external_design_temperature(project_state):
            issues.append(
                ValidationIssue(
                    code="ENV_EXT_TEMP_MISSING",
                    severity=ValidationSeverity.FATAL,
                    subject="environment",
                    message="External design temperature is missing.",
                )
            )

        # ---- Rooms ------------------------------------------------------
        rooms = getattr(project_state, "rooms", None)
        if not rooms:
            issues.append(
                ValidationIssue(
                    code="ROOMS_NONE",
                    severity=ValidationSeverity.FATAL,
                    subject="room",
                    message="No rooms are defined.",
                )
            )

        fatals = tuple(i for i in issues if i.severity == ValidationSeverity.FATAL)
        warnings = tuple(i for i in issues if i.severity == ValidationSeverity.WARNING)

        status = ValidationStatus.FAIL if fatals else ValidationStatus.PASS
        return ValidationReport(
            status=status,
            fatal_issues=fatals,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _has_external_design_temperature(self, ps: Any) -> bool:
        env = getattr(ps, "environment", None)
        if env is None:
            return False
        return getattr(env, "external_design_temperature_c", None) is not None
