# ======================================================================
# HVAC/project_v3/diagnostics_v3.py
# ======================================================================

"""
HVACgooee — Project Diagnostics v3 (DATA-ONLY)

Purpose
-------
Structured diagnostics returned by validators.

LOCKED
------
• No mutation of projects
• Pure data
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SeverityV3(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class DiagnosticV3:
    severity: SeverityV3
    code: str
    message: str
    path: Optional[str] = None  # e.g. "intent.spaces" or "validity.heatloss_valid"
