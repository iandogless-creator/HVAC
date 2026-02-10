# ======================================================================
# HVAC/hydronics_v3/engines/iterative_balancing_engine_v1.py
# ======================================================================

from __future__ import annotations

import math
from typing import List

from HVAC.hydronics_v3.dto.balancing_target_dto import BalancingTargetDTO
from HVAC.hydronics_v3.dto.valve_catalog_dto import ValveCatalogDTO
from HVAC.hydronics_v3.dto.iterative_balancing_input_dto import (
    IterativeBalancingInputDTO,
)
from HVAC.hydronics_v3.dto.iterative_balancing_result_dto import (
    IterativeBalancingResultDTO,
    IterativeBalancingTerminalResultDTO,
)


class IterativeBalancingEngineV1:
    """
    Deterministic Kv refinement engine.

    No topology.
    No mutation.
    Hard red-stop on failure.
    """

    @staticmethod
    def run(
        balancing_target: BalancingTargetDTO,
        balancing_input: IterativeBalancingInputDTO,
        catalog: ValveCatalogDTO,
    ) -> IterativeBalancingResultDTO:

        if balancing_target.system_id != balancing_input.system_id:
            raise ValueError("System ID mismatch")

        kv_options = sorted(
            catalog.kv_options, key=lambda o: o.kv_m3_h
        )

        results: List[IterativeBalancingTerminalResultDTO] = []

        for target in balancing_target.terminal_targets:
            leg_id = target.terminal_leg_id

            if leg_id not in balancing_input.terminals:
                raise ValueError(
                    f"Missing balancing input for terminal {leg_id}"
                )

            terminal = balancing_input.terminals[leg_id]

            converged = False
            iterations = 0

            for option in kv_options[: balancing_input.max_iterations]:
                iterations += 1

                # Δp via Kv equation
                dp_bar = (terminal.design_flow_m3_h / option.kv_m3_h) ** 2
                valve_dp_pa = dp_bar * 1e5

                total_dp = valve_dp_pa + terminal.system_dp_pa
                authority = valve_dp_pa / total_dp

                # Check authority + target Δp
                if (
                    authority >= balancing_input.min_authority
                    and abs(valve_dp_pa - target.target_dp_pa)
                    <= balancing_target.tolerance_pa
                ):
                    converged = True

                    results.append(
                        IterativeBalancingTerminalResultDTO(
                            terminal_leg_id=leg_id,
                            selected_kv_m3_h=option.kv_m3_h,
                            valve_dp_pa=valve_dp_pa,
                            authority=authority,
                            iterations_used=iterations,
                            converged=True,
                            note="Kv refined successfully",
                        )
                    )
                    break

            if not converged:
                raise ValueError(
                    f"Iterative balancing failed for terminal {leg_id}"
                )

        return IterativeBalancingResultDTO(
            system_id=balancing_target.system_id,
            terminals=results,
        )
