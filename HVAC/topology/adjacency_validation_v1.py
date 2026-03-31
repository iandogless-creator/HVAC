from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List


# ----------------------------------------------------------------------
# Severity
# ----------------------------------------------------------------------

class AdjacencySeverity:
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


# ----------------------------------------------------------------------
# Result DTO (per segment)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class AdjacencyValidationResult:
    surface_id: str
    severity: str                 # OK | WARNING | ERROR
    message: Optional[str] = None