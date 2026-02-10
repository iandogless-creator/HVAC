# ======================================================================
# HVAC/hydronics_v3/engines/balancing_target_engine_v1.py
# ======================================================================

"""
HVACgooee — Balancing Target Engine v1

Purpose
-------
Declaratively derives balancing targets from an authoritative
IndexPathResultDTO.

This engine:
• Consumes IndexPathResultDTO
• Emits BalancingTargetDTO
• Performs ONLY validation and target declaration
• Enforces strict red-stop rules

It does NOT:
• calculate pressure drops
• size valves
• iterate hydraulics
• infer topology
• mutate any DTOs
"""

from __future__ import annotations

from typing import List

from HVAC.hydronics_v3.dto.index_path_result_dto import (
    IndexPathResultDTO,
)
from HVAC.hydronics_v3.dto.balancing_target_dto import (
    BalancingTargetDTO,
    TerminalBalanceTargetDTO,
    BalancingPolicy,
)


# ----------------------------------------------------------------------
# BalancingTargetEngineV1
# ----------------------------------------------------------------------


class BalancingTargetEngineV1:
    """
    Canonical balancing target declaration engine.

    LOCKED BEHAVIOUR
    ----------------
    • Deterministic
    • Pure (DTO-in / DTO-out)
    • Fail-fast on any structural or data violation
    • No side effects
    """

    @staticmethod
    def run(index_result: IndexPathResultDTO) -> BalancingTargetDTO:
        """
        Produce a BalancingTargetDTO from an IndexPathResultDTO.

        RED-STOP CONDITIONS
        -------------------
        • Missing index leg
        • Empty path
        • Non-positive Δp
        • Inconsistent index reference
        """

        # ------------------------------------------------------------
        # Guard: index leg must be declared
        # ------------------------------------------------------------
        if not index_result.index_leg_id:
            raise ValueError("IndexPathResultDTO.index_leg_id is required")

        # ------------------------------------------------------------
        # Guard: path must exist
        # ------------------------------------------------------------
        if not index_result.path_legs:
            raise ValueError("Index path is empty — cannot derive balancing targets")

        # ------------------------------------------------------------
        # Guard: total Δp must be positive
        # (zero Δp systems cannot be balanced)
        # ------------------------------------------------------------
        if index_result.total_dp_pa <= 0:
            raise ValueError(
                "Index path total_dp_pa must be > 0 for balancing"
            )

        # ------------------------------------------------------------
        # Guard: index leg must be terminal of the path
        # ------------------------------------------------------------
        terminal_leg_id = index_result.path_legs[-1].leg_id
        if terminal_leg_id != index_result.index_leg_id:
            raise ValueError(
                "Index leg must be the terminal leg of the index path"
            )

        # ------------------------------------------------------------
        # Declare terminal targets (equal-to-index policy)
        # ------------------------------------------------------------
        terminal_targets: List[TerminalBalanceTargetDTO] = [
            TerminalBalanceTargetDTO(
                terminal_leg_id=index_result.index_leg_id,
                target_dp_pa=index_result.total_dp_pa,
                weight=1.0,
                note="Index path terminal (governing leg)",
            )
        ]

        # ------------------------------------------------------------
        # Emit BalancingTargetDTO
        # ------------------------------------------------------------
        return BalancingTargetDTO(
            system_id=index_result.system_id,
            index_leg_id=index_result.index_leg_id,
            index_dp_pa=index_result.total_dp_pa,
            policy=BalancingPolicy.EQUAL_TO_INDEX,
            terminal_targets=terminal_targets,
            note="Declared from index path result (BalancingTargetEngineV1)",
        )
