# ======================================================================
# HVAC/project_v3/model_v3.py
# ======================================================================

"""
HVACgooee — Project Model v3 (CANONICAL, DATA-ONLY)

Timestamp (UK): Monday 26 January 2026, 03:10 am

LOCKED
------
• No calculations
• No engine imports
• No GUI imports
• Results written only by orchestrators
• Validity flags are explicit, never inferred
• Project is domain-agnostic container of intent + results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ----------------------------------------------------------------------
# Identity & units
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ProjectUnitsV3:
    """
    Units / conventions used for declared intent & reporting.

    Keep this minimal and stable. Add fields only when truly global.
    """
    temperature: str = "C"
    length: str = "m"
    area: str = "m2"
    volume: str = "m3"
    power: str = "W"
    pressure: str = "Pa"


@dataclass(frozen=True, slots=True)
class ProjectIdentityV3:
    project_id: str
    name: str
    schema_version: str = "3.1"
    units: ProjectUnitsV3 = field(default_factory=ProjectUnitsV3)


# ----------------------------------------------------------------------
# Declared intent (domain-agnostic containers)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ProjectDeclaredIntentV3:
    """
    Declared design intent.

    NOTE:
    - These are intentionally generic containers so Project Core does not
      depend on domain packages.
    - Orchestrators/adapters are responsible for mapping to/from domain DTOs.
    """
    spaces: List[Dict[str, Any]] = field(default_factory=list)
    constructions: Dict[str, Any] = field(default_factory=dict)
    design_conditions: Dict[str, Any] = field(default_factory=dict)
    hydronic_intent: Dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------
# Derived results (opaque payloads owned by orchestrators)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ProjectDerivedResultsV3:
    """
    Derived results written by orchestrators.

    These should be:
    - serialisable
    - deterministic snapshots
    - DTO-ish payloads (dict/dataclass -> dict) from engines/runners

    Project Core does not interpret them.
    """
    heatloss_result: Optional[Dict[str, Any]] = None
    hydronics_result: Optional[Dict[str, Any]] = None
    pump_result: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------
# Validity flags (explicit, never inferred)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ProjectValidityV3:
    heatloss_valid: bool = False
    hydronics_valid: bool = False
    pump_valid: bool = False


# ----------------------------------------------------------------------
# The Project Model (single source of truth)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class ProjectModelV3:
    """
    Canonical project-wide engineering state (v3).

    LOCKED:
    • Data-only container
    • No calculations
    • Validity flags are explicit
    """
    identity: ProjectIdentityV3
    intent: ProjectDeclaredIntentV3 = field(default_factory=ProjectDeclaredIntentV3)
    results: ProjectDerivedResultsV3 = field(default_factory=ProjectDerivedResultsV3)
    validity: ProjectValidityV3 = field(default_factory=ProjectValidityV3)

    # ------------------------------------------------------------------
    # Invalidation helpers (PROJECT CORE OWNS THESE RULES)
    # ------------------------------------------------------------------

    def invalidate_heatloss(self) -> None:
        """
        Heat-loss invalidation cascades downstream.

        LOCKED:
        • If heatloss invalidated -> hydronics & pump invalid
        • Results may be cleared (deterministic safety)
        """
        self.validity.heatloss_valid = False
        self.results.heatloss_result = None

        # cascade
        self.invalidate_hydronics()

    def invalidate_hydronics(self) -> None:
        self.validity.hydronics_valid = False
        self.results.hydronics_result = None

        # cascade
        self.invalidate_pump()

    def invalidate_pump(self) -> None:
        self.validity.pump_valid = False
        self.results.pump_result = None

    # ------------------------------------------------------------------
    # Intent mutation helpers (OPTIONAL but useful)
    # ------------------------------------------------------------------

    def note_geometry_changed(self) -> None:
        """
        Call when spaces/geometry changes.
        LOCKED invalidation: geometry -> heatloss invalid (cascades).
        """
        self.invalidate_heatloss()

    def note_constructions_changed(self) -> None:
        """
        Call when constructions change.
        LOCKED invalidation: constructions -> heatloss invalid (cascades).
        """
        self.invalidate_heatloss()

    def note_design_conditions_changed(self) -> None:
        """
        Call when design conditions change.
        LOCKED invalidation: design conditions -> heatloss invalid (cascades).
        """
        self.invalidate_heatloss()

    def note_hydronic_intent_changed(self) -> None:
        """
        Call when hydronic intent changes.
        LOCKED invalidation: hydronic intent -> hydronics invalid (cascades pump).
        """
        self.invalidate_hydronics()
