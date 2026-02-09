# ======================================================================
# HVAC/hydronics/committed/committed_hydronic_leg.py
# ======================================================================

"""
HVACgooee — Committed Hydronic Leg DTO (v1)
------------------------------------------

Authoritative representation of a hydronic leg AFTER commitment.

This object:
• Locks topology
• Locks flow
• Is eligible for sizing and ΔP solvers
• Is immutable once created
• Represents explicit engineering intent

RULES
-----
• NO provisional values
• NO auto-derivation
• NO mutation
• NO GUI ownership
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class CommittedHydronicLeg:
    """
    Authoritative hydronic leg definition for sizing stages.
    """

    # --------------------------------------------------------------
    # Identity
    # --------------------------------------------------------------
    leg_id: str
    leg_name: str

    # --------------------------------------------------------------
    # Topology (LOCKED)
    # --------------------------------------------------------------
    parent_leg_id: Optional[str]
    depth_from_source: int

    # --------------------------------------------------------------
    # Hydraulic intent (LOCKED)
    # --------------------------------------------------------------
    design_flow_lps: float
    design_heat_w: float

    # --------------------------------------------------------------
    # Geometric intent (LOCKED, but minimal)
    # --------------------------------------------------------------
    nominal_length_m: float

    # --------------------------------------------------------------
    # Flags / options (DEFAULTED — must come AFTER all required)
    # --------------------------------------------------------------
    is_index_leg: bool = False

    # --------------------------------------------------------------
    # Metadata / audit (DEFAULTED)
    # --------------------------------------------------------------
    committed_by: Optional[str] = None
    committed_at_utc: Optional[str] = None
    notes: Optional[str] = None
