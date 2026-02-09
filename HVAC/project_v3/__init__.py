# ======================================================================
# HVAC/project_v3/__init__.py
# ======================================================================

"""
HVACgooee — Project Core v3 (PACKAGE)

LOCKED:
• ProjectModelV3 is data-only
• No engines, no GUI, no runners
• Validity is explicit (never inferred)
"""

from .model_v3 import (
    ProjectModelV3,
    ProjectIdentityV3,
    ProjectUnitsV3,
    ProjectValidityV3,
    ProjectDerivedResultsV3,
)
from .validator_v3 import ProjectValidatorV3
from .factory_v3 import ProjectFactoryV3
from .diagnostics_v3 import DiagnosticV3, SeverityV3

__all__ = [
    "ProjectModelV3",
    "ProjectIdentityV3",
    "ProjectUnitsV3",
    "ProjectValidityV3",
    "ProjectDerivedResultsV3",
    "ProjectValidatorV3",
    "ProjectFactoryV3",
    "DiagnosticV3",
    "SeverityV3",
]
