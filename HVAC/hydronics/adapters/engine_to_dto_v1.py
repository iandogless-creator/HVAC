# ======================================================================
# HVAC/hydronics/adapters/engine_to_dto_v1.py
# ======================================================================

"""
HVACgooee — Hydronics Engine → DTO Adapter v1
--------------------------------------------

Pure translation layer.
"""

from __future__ import annotations

from HVAC.hydronics.run.hydronics_run_result_v1 import HydronicsRunResultV1
from HVAC.hydronics.dto.hydronics_results_dto_v1 import (
    HydronicsResultsDTO,
    PathPressureDropDTO,
    PumpDutyDTO,
    BalancingRowDTO,
)


def build_hydronics_results_dto_v1(
    result: HydronicsRunResultV1,
) -> HydronicsResultsDTO:
    """
    Translate domain result into GUI-facing DTO.
    """

    paths = [
        PathPressureDropDTO(
            terminal_id=k,
            total_dp_pa=v.total_dp_pa,
        )
        for k, v in result.pressure_drop_paths.items()
    ]

    pump = PumpDutyDTO(
        flow_l_s=result.pump_result.flow_l_s,
        head_m=result.pump_result.head_m,
        electrical_power_w=result.pump_result.electrical_power_w,
    )

    balancing = None
    if result.balancing:
        balancing = [
            BalancingRowDTO(
                terminal_id=t.terminal_id,
                setting=t.selection.setting if t.selection else None,
                dp_added_pa=t.selection.dp_valve_pa if t.selection else 0.0,
                residual_pa=t.residual_pa,
            )
            for t in result.balancing.terminals
        ]

    return HydronicsResultsDTO(
        paths=paths,
        pump=pump,
        balancing=balancing,
    )
