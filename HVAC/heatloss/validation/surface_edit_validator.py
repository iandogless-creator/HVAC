from __future__ import annotations

from typing import List, Any

from HVAC.heatloss.validation.validation_dto import (
    ValidationIssue,
    ValidationReport,
    ValidationStatus,
    ValidationSeverity,
)


class SurfaceEditValidator:
    """
    Pre-commit validation for overlay edits.
    """

    # ------------------------------------------------------------------
    # ENTRY
    # ------------------------------------------------------------------

    def validate(
        self,
        ctx: Any,
        values: dict,
        project: Any,
    ) -> ValidationReport:

        if ctx.kind == "surface":
            return self._validate_surface(values)

        if ctx.kind == "geometry":
            return self._validate_geometry(values)

        if ctx.kind == "ach":
            return self._validate_ach(values)

        return ValidationReport(
            status=ValidationStatus.FAIL,
            fatal_issues=(
                ValidationIssue(
                    code="UNKNOWN_KIND",
                    severity=ValidationSeverity.FATAL,
                    subject="context",
                    message=f"Unknown edit kind: {ctx.kind}",
                ),
            ),
            warnings=(),
        )

    # ------------------------------------------------------------------
    # RESULT BUILDER
    # ------------------------------------------------------------------

    def _result(self, issues: List[ValidationIssue]) -> ValidationReport:
        fatals = tuple(i for i in issues if i.severity == ValidationSeverity.FATAL)
        warnings = tuple(i for i in issues if i.severity == ValidationSeverity.WARNING)

        return ValidationReport(
            status=ValidationStatus.FAIL if fatals else ValidationStatus.PASS,
            fatal_issues=fatals,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # SURFACE
    # ------------------------------------------------------------------

    def _validate_surface(self, values: dict) -> ValidationReport:
        issues: List[ValidationIssue] = []

        A = values.get("area_m2")
        U = values.get("u_value")

        if not isinstance(A, (int, float)):
            issues.append(ValidationIssue(
                code="AREA_TYPE",
                severity=ValidationSeverity.FATAL,
                subject="area_m2",
                message="Area must be numeric",
            ))
        elif A <= 0:
            issues.append(ValidationIssue(
                code="AREA_INVALID",
                severity=ValidationSeverity.FATAL,
                subject="area_m2",
                message="Area must be > 0",
            ))

        if not isinstance(U, (int, float)):
            issues.append(ValidationIssue(
                code="U_TYPE",
                severity=ValidationSeverity.FATAL,
                subject="u_value",
                message="U-value must be numeric",
            ))
        elif U <= 0:
            issues.append(ValidationIssue(
                code="U_INVALID",
                severity=ValidationSeverity.FATAL,
                subject="u_value",
                message="U-value must be > 0",
            ))
        elif U > 10:
            issues.append(ValidationIssue(
                code="U_HIGH",
                severity=ValidationSeverity.WARNING,
                subject="u_value",
                message="U-value unusually high",
            ))

        return self._result(issues)

    # ------------------------------------------------------------------
    # GEOMETRY
    # ------------------------------------------------------------------

    def _validate_geometry(self, values: dict) -> ValidationReport:
        issues: List[ValidationIssue] = []

        L = values.get("length_m")
        W = values.get("width_m")
        H = values.get("height_m")

        if not isinstance(L, (int, float)):
            issues.append(ValidationIssue(
                code="LENGTH_TYPE",
                severity=ValidationSeverity.FATAL,
                subject="length_m",
                message="Length must be numeric",
            ))
        elif L <= 0:
            issues.append(ValidationIssue(
                code="LENGTH_INVALID",
                severity=ValidationSeverity.FATAL,
                subject="length_m",
                message="Length must be > 0",
            ))

        if not isinstance(W, (int, float)):
            issues.append(ValidationIssue(
                code="WIDTH_TYPE",
                severity=ValidationSeverity.FATAL,
                subject="width_m",
                message="Width must be numeric",
            ))
        elif W <= 0:
            issues.append(ValidationIssue(
                code="WIDTH_INVALID",
                severity=ValidationSeverity.FATAL,
                subject="width_m",
                message="Width must be > 0",
            ))

        if not isinstance(H, (int, float)):
            issues.append(ValidationIssue(
                code="HEIGHT_TYPE",
                severity=ValidationSeverity.FATAL,
                subject="height_m",
                message="Height must be numeric",
            ))
        elif H <= 0:
            issues.append(ValidationIssue(
                code="HEIGHT_INVALID",
                severity=ValidationSeverity.FATAL,
                subject="height_m",
                message="Height must be > 0",
            ))
        elif H > 6:
            issues.append(ValidationIssue(
                code="HEIGHT_HIGH",
                severity=ValidationSeverity.WARNING,
                subject="height_m",
                message="Height unusually large",
            ))

        return self._result(issues)

    # ------------------------------------------------------------------
    # ACH
    # ------------------------------------------------------------------

    def _validate_ach(self, values: dict) -> ValidationReport:
        issues: List[ValidationIssue] = []

        ach = values.get("ach")

        if not isinstance(ach, (int, float)):
            issues.append(ValidationIssue(
                code="ACH_TYPE",
                severity=ValidationSeverity.FATAL,
                subject="ach",
                message="ACH must be numeric",
            ))
        elif ach < 0:
            issues.append(ValidationIssue(
                code="ACH_INVALID",
                severity=ValidationSeverity.FATAL,
                subject="ach",
                message="ACH must be ≥ 0",
            ))
        elif ach > 10:
            issues.append(ValidationIssue(
                code="ACH_HIGH",
                severity=ValidationSeverity.WARNING,
                subject="ach",
                message="ACH unusually high",
            ))

        return self._result(issues)