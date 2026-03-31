# ======================================================================
# HVACgooee — Validation DTOs
# Status: CANONICAL
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


# ----------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------

class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class ValidationSeverity(str, Enum):
    FATAL = "FATAL"
    WARNING = "WARNING"


# ----------------------------------------------------------------------
# DTOs
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: ValidationSeverity
    subject: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    status: ValidationStatus
    fatal_issues: Tuple[ValidationIssue, ...]
    warnings: Tuple[ValidationIssue, ...]