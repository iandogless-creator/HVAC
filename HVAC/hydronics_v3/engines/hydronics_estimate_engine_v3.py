# ======================================================================
# HVAC/hydronics_v3/engines/hydronics_estimate_engine_v3.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics_v3.dto.hydronics_estimate_input_dto import (
    HydronicsEstimateInputDTO,
)
from HVAC.hydronics_v3.dto.hydronics_estimate_result_dto import (
    HydronicsEstimateResultDTO,
)


class HydronicsEstimateEngineV3:
    """
    PURE hydronics estimate engine (v3).

    • No ProjectState
    • No GUI
    • Deterministic
    """

    @staticmethod
    def run(
        intent: HydronicsEstimateInputDTO,
    ) -> HydronicsEstimateResultDTO:

        # ------------------------------------------------------------
        # Extract declared intent (EXPLICIT)
        # ------------------------------------------------------------
        qt_w = intent.design_heat_load_w
        flow_temp_c = intent.flow_temp_c
        return_temp_c = intent.return_temp_c
        delta_t_k = flow_temp_c - return_temp_c

        if delta_t_k <= 0.0:
            raise ValueError("Invalid temperature regime (ΔT ≤ 0)")

        # ------------------------------------------------------------
        # Placeholder physics (LOCKED v1)
        # ------------------------------------------------------------
        cp = 4180.0  # J/kg·K (water)
        flow_kg_s = qt_w / (cp * delta_t_k)
        flow_l_s = flow_kg_s  # density ≈ 1 kg/L

        dp_pa = 0.0
        pump_power_w = None

        # ------------------------------------------------------------
        # Result DTO
        # ------------------------------------------------------------
        return HydronicsEstimateResultDTO(
            design_heat_load_w=qt_w,

            design_flow_rate_l_s=flow_l_s,
            design_flow_rate_m3_h=flow_l_s * 3.6,

            flow_temp_c=flow_temp_c,
            return_temp_c=return_temp_c,
            delta_t_k=delta_t_k,

            estimated_system_pressure_drop_pa=dp_pa,
            estimated_system_pressure_drop_m=dp_pa / (1000.0 * 9.81),

            estimated_pump_power_w=pump_power_w,
            calculation_notes="Hydronics estimate v3 placeholder",
            estimate_valid=True,
        )
