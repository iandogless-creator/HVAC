# ======================================================================
# HVAC/hydronics_v3/engines/balancing_target_engine_v1.py
# ======================================================================

"""
HVACgooee — Balancing Target Engine v1 (Parallel-Aware)

Purpose
-------
Declare balancing targets for ALL terminal legs using the
discovered index-path Δp.

Index path defines the governing Δp.
All other terminals must be raised to match it.

Still:
• No maths
• No iteration
• No valve logic
• Red-stop only
"""

from __future__ import annotations

from typing import List

from HVAC_legacy.hydronics_v3.dto.index_path_result_dto import IndexPathResultDTO
from HVAC_legacy.hydronics_v3.dto.balancing_target_dto import (
    BalancingTargetDTO,
    TerminalBalanceTargetDTO,
    BalancingPolicy,
)


class BalancingTargetEngineV1:
    """
    Canonical balancing target declaration engine (parallel-safe).

    Deterministic.
    DTO-in / DTO-out.
    Fail-fast.
    """

    @staticmethod
    def run(index_result: IndexPathResultDTO) -> BalancingTargetDTO:
        # ------------------------------------------------------------
        # Guards — red anywhere means stop
        # ------------------------------------------------------------

        if not index_result.index_leg_id:
            raise ValueError("index_leg_id is required")

        if not index_result.path_legs:
            raise ValueError("index path is empty")

        if index_result.total_dp_pa <= 0:
            raise ValueError("Index path total_dp_pa must be > 0")

        if not index_result.terminal_leg_ids:
            raise ValueError("No terminal_leg_ids declared in IndexPathResultDTO")

        if index_result.index_leg_id not in index_result.terminal_leg_ids:
            raise ValueError("Index leg must be included in terminal_leg_ids")

        # ------------------------------------------------------------
        # Declare balancing targets
        # ------------------------------------------------------------

        terminal_targets: List[TerminalBalanceTargetDTO] = []

        for leg_id in index_result.terminal_leg_ids:
            terminal_targets.append(
                TerminalBalanceTargetDTO(
                    terminal_leg_id=leg_id,
                    target_dp_pa=index_result.total_dp_pa,
                    weight=1.0,
                    note=(
                        "Index path terminal (governing leg)"
                        if leg_id == index_result.index_leg_id
                        else "Non-index terminal balanced up to index Δp"
                    ),
                )
            )

        # ------------------------------------------------------------
        # Emit DTO
        # ------------------------------------------------------------

        return BalancingTargetDTO(
            system_id=index_result.system_id,
            index_leg_id=index_result.index_leg_id,
            index_dp_pa=index_result.total_dp_pa,
            policy=BalancingPolicy.EQUAL_TO_INDEX,
            terminal_targets=terminal_targets,
            note="Declared for all terminals from index path (parallel branches)",
        )
