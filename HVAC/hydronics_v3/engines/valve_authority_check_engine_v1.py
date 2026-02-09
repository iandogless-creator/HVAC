# ======================================================================
# HVAC/hydronics_v3/engines/valve_authority_check_engine_v1.py
# ======================================================================

"""
HVACgooee — Valve Authority Check Engine v1

Purpose
-------
Verifies that valve authority meets minimum acceptable limits
for all terminals.

This engine:
• Consumes DTOs only
• Performs no sizing or iteration
• Fails hard if authority is unacceptable
• Enforces 'red anywhere means stop'
"""

from __future__ import annotations

from typing import Dict

from HVAC_legacy.hydronics_v3.dto.balancing_target_dto import BalancingTargetDTO
from HVAC_legacy.hydronics_v3.dto.valve_authority_input_dto import (
    ValveAuthorityInputDTO,
)


class ValveAuthorityCheckEngineV1:
    """
    Guard-only valve authority checker.
    """

    # Canonical minimum authority (LOCKED for v1)
    MIN_AUTHORITY = 0.3

    @staticmethod
    def run(
        balancing_target: BalancingTargetDTO,
        authority_input: ValveAuthorityInputDTO,
    ) -> None:
        """
        Perform authority checks.

        RED-STOP CONDITIONS
        -------------------
        • Missing terminal data
        • Non-positive Δp values
        • Authority < MIN_AUTHORITY
        """

        if balancing_target.system_id != authority_input.system_id:
            raise ValueError("System ID mismatch between DTOs")

        # Build lookup for authority data
        authority_map: Dict[str, float] = {}

        for t in authority_input.terminals:
            if t.valve_dp_pa <= 0:
                raise ValueError(
                    f"Valve Δp must be > 0 for terminal {t.terminal_leg_id}"
                )
            if t.system_dp_pa < 0:
                raise ValueError(
                    f"System Δp must be >= 0 for terminal {t.terminal_leg_id}"
                )

            total_dp = t.valve_dp_pa + t.system_dp_pa
            authority_map[t.terminal_leg_id] = t.valve_dp_pa / total_dp

        # ------------------------------------------------------------
        # Authority checks per balancing target
        # ------------------------------------------------------------

        for target in balancing_target.terminal_targets:
            if target.terminal_leg_id not in authority_map:
                raise ValueError(
                    f"Missing valve authority data for terminal {target.terminal_leg_id}"
                )

            authority = authority_map[target.terminal_leg_id]

            if authority < ValveAuthorityCheckEngineV1.MIN_AUTHORITY:
                raise ValueError(
                    f"Valve authority too low for terminal "
                    f"{target.terminal_leg_id}: "
                    f"{authority:.2f} < {ValveAuthorityCheckEngineV1.MIN_AUTHORITY}"
                )
