# ======================================================================
# HVAC/project_v3/models/project_model_v3.py
# ======================================================================

"""
HVACgooee — ProjectModelV3 (CANONICAL)

Status: 🔒 LOCKED — PROJECT AUTHORITY
Scope: project_v3 (Project model, lifecycle, validation)

Purpose
-------
Defines what a Project is in HVACgooee.

This model is the single authoritative layer that:
• Declares design intent
• Stores derived engineering results
• Enforces lifecycle validity (via explicit flags, not inference)
• Separates engines from orchestration
• Acts as the only integration boundary between domains

RULES (LOCKED)
--------------
• Data-only (no calculations)
• No engine imports
• No GUI imports
• Results are written only by orchestrators
• Validity flags are explicit, never inferred
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# ----------------------------------------------------------------------
# Identity
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ProjectIdentityV3:
    project_id: str
    name: str
    schema_version: str
    units: str  # e.g. "SI", "UK", "IP" (string by design, versionable)


# ----------------------------------------------------------------------
# Declared Intent (domain-agnostic containers)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class DeclaredIntentV3:
    """
    Domain-agnostic containers.

    NOTE:
    These are intentionally permissive "payload buckets" at Project Core level.
    The *shape* is enforced by validators and domain-specific DTO adapters,
    not by engines and not by the ProjectModel itself.
    """
    spaces: Dict[str, Any] = field(default_factory=dict)
    constructions: Dict[str, Any] = field(default_factory=dict)
    design_conditions: Dict[str, Any] = field(default_factory=dict)
    hydronic_intent: Dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------
# Derived Results (written by orchestrators only)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class DerivedResultsV3:
    heatloss_result: Optional[Dict[str, Any]] = None
    hydronics_result: Optional[Dict[str, Any]] = None
    pump_result: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------
# Validity Flags (explicit, never inferred)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ValidityFlagsV3:
    heatloss_valid: bool = False
    hydronics_valid: bool = False
    pump_valid: bool = False


# ----------------------------------------------------------------------
# ProjectModelV3 (authoritative, serialisable)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ProjectModelV3:
    """
    Canonical Project Core model (v3).

    A Project is:
    • versioned, serialisable declaration of design intent and derived results
    • explicit validity state for lifecycle gating

    A Project is NOT:
    • a GUI
    • an engine
    • a calculator
    • a runner
    • a persistence mechanism
    • a workflow controller
    """
    identity: ProjectIdentityV3
    intent: DeclaredIntentV3 = field(default_factory=DeclaredIntentV3)
    results: DerivedResultsV3 = field(default_factory=DerivedResultsV3)
    validity: ValidityFlagsV3 = field(default_factory=ValidityFlagsV3)

    # ------------------------------------------------------------
    # Invalidation (LOCKED behaviour)
    # ------------------------------------------------------------

    def invalidate_heatloss(self, reason: str = "") -> None:
        """
        Invalidates heat-loss and everything downstream.

        LOCKED:
        • explicit only
        • never inferred
        """
        self.validity.heatloss_valid = False
        self.results.heatloss_result = None

        # downstream
        self.invalidate_hydronics(reason=f"heatloss invalidated: {reason}".strip())
        # invalidate_hydronics will invalidate pump too

    def invalidate_hydronics(self, reason: str = "") -> None:
        """
        Invalidates hydronics and everything downstream.

        LOCKED:
        • explicit only
        • never inferred
        """
        self.validity.hydronics_valid = False
        self.results.hydronics_result = None

        # downstream
        self.invalidate_pump(reason=f"hydronics invalidated: {reason}".strip())

    def invalidate_pump(self, reason: str = "") -> None:
        """
        Invalidates pump/system sizing.

        LOCKED:
        • explicit only
        • never inferred
        """
        self.validity.pump_valid = False
        self.results.pump_result = None
