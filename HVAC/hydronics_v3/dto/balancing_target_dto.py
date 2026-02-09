# ======================================================================
# HVAC/hydronics_v3/dto/balancing_target_dto.py
# ======================================================================

"""
HVACgooee — Balancing Target DTO (v1)

Purpose
-------
Declarative "what we want to achieve" contract for hydronic balancing.

This DTO does NOT:
• calculate Δp
• size valves
• infer topology
• mutate system objects
• import GUI / Qt / ProjectState

It exists so BalancingTargetEngineV1 can be:
• deterministic
• DTO-in / DTO-out
• test-first
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


# ----------------------------------------------------------------------
# Balancing policy (declarative)
# ----------------------------------------------------------------------


class BalancingPolicy(str, Enum):
    """
    How targets should be interpreted.

    EQUAL_TO_INDEX:
        Every terminal path is targeted to match the discovered index-path Δp.

    EXPLICIT_TERMINAL_TARGETS:
        Each terminal has its own target Δp (e.g., design specs / legacy rule sets).
    """

    EQUAL_TO_INDEX = "equal_to_index"
    EXPLICIT_TERMINAL_TARGETS = "explicit_terminal_targets"


# ----------------------------------------------------------------------
# Terminal target row (declarative)
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TerminalBalanceTargetDTO:
    """
    Declarative target for a single terminal leg/path.

    Notes
    -----
    • terminal_leg_id is a LABEL (must exist in topology).
    • target_dp_pa is an engineering *intent* for balancing engines.
    • weight allows prioritisation when compromises are required
      (e.g., legacy practice or staged commissioning).
    """

    terminal_leg_id: str
    target_dp_pa: float
    weight: float = 1.0
    note: str = ""


# ----------------------------------------------------------------------
# BalancingTargetDTO (top-level contract)
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BalancingTargetDTO:
    """
    Balancing "goal sheet" produced AFTER pressure-drop estimation and
    index-path discovery, consumed by balancing / valve-related engines.

    LOCKED RULES
    ------------
    • Pure data only
    • Engine may READ, must NOT mutate
    • No topology inference: ids must refer to existing legs
    • No physics: dp values are inputs from earlier engines

    Typical flow (future)
    ---------------------
    PressureDropPathEngineV1  -> PressureDropPathDTO
    IndexPathEngineV1         -> IndexPathResultDTO
    BalancingTargetEngineV1   -> BalancingTargetDTO   (this DTO)
    Valve engines             -> sizing/authority DTOs
    """

    system_id: str

    # The discovered index leg/path (label reference only).
    index_leg_id: str

    # Index Δp in Pascals (from PressureDropPath results).
    index_dp_pa: float

    # Policy describing how terminal targets are derived/interpreted.
    policy: BalancingPolicy = BalancingPolicy.EQUAL_TO_INDEX

    # If policy == EXPLICIT_TERMINAL_TARGETS, these are used directly.
    # If policy == EQUAL_TO_INDEX, engines may populate these with
    # terminal targets equal to index_dp_pa for transparency/reporting.
    terminal_targets: List[TerminalBalanceTargetDTO] = None  # type: ignore[assignment]

    # Acceptable error band for "balanced" determination (Pa).
    tolerance_pa: float = 50.0

    # Optional guardrails for iterative engines (still declarative).
    max_iterations: int = 50

    # Optional human/context note (reporting only).
    note: str = ""

    def __post_init__(self) -> None:
        # Maintain immutability while ensuring terminal_targets is always a list.
        if self.terminal_targets is None:
            object.__setattr__(self, "terminal_targets", [])

        if self.index_dp_pa < 0:
            raise ValueError("index_dp_pa must be >= 0")

        if self.tolerance_pa < 0:
            raise ValueError("tolerance_pa must be >= 0")

        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be > 0")

        for t in self.terminal_targets:
            if t.target_dp_pa < 0:
                raise ValueError("terminal target_dp_pa must be >= 0")
            if t.weight <= 0:
                raise ValueError("terminal weight must be > 0")
