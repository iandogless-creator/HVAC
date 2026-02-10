# ======================================================================
# HVAC/hydronics_v3/runners/hydronics_estimate_runner_v3.py
# ======================================================================

"""
hydronics_estimate_runner_v3.py
-------------------------------

HVACgooee — Hydronics Estimate Runner v3

Purpose
-------
Project-level orchestration for first-pass hydronic estimates.

This stage converts declared intent into coarse system-level results.

RULES (LOCKED)
--------------
• Consumes HydronicsEstimateInputDTO
• Produces HydronicsEstimateResultDTO
• No GUI imports
• No project mutation here
• No topology
• No detailed pipe sizing
"""

from __future__ import annotations

from HVAC.hydronics_v3.dto.hydronics_estimate_input_dto import (
    HydronicsEstimateInputDTO,
)
from HVAC.hydronics_v3.dto.hydronics_estimate_result_dto import (
    HydronicsEstimateResultDTO,
)


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------

class HydronicsEstimateRunnerV3:
    """
    First-pass hydronics estimate runner (v3).

    This runner answers the question:
    “What order of magnitude system is required
     to serve this heat load?”
    """

    @staticmethod
    def run(
        dto: HydronicsEstimateInputDTO,
    ) -> HydronicsEstimateResultDTO:
        """
        Execute hydronic estimate from declared intent.

        Parameters
        ----------
        dto:
            HydronicsEstimateInputDTO

        Returns
        -------
        HydronicsEstimateResultDTO
        """

        # ------------------------------------------------------------
        # Extract declared intent
        # ------------------------------------------------------------
        qt_w = dto.design_heat_load_w
        flow_temp_c = dto.flow_temp_c
        return_temp_c = dto.return_temp_c
        delta_t_k = flow_temp_c - return_temp_c

        # ------------------------------------------------------------
        # PLACEHOLDER calculations (LOCKED v1)
        # ------------------------------------------------------------
        # NOTE:
        # • No physics implemented yet
        # • Values are intentionally conservative placeholders
        # • Replaced in v2 with real estimation logic

        design_flow_rate_l_s = 0.0
        design_flow_rate_m3_h = 0.0

        estimated_pressure_drop_pa = 0.0
        estimated_pressure_drop_m = 0.0

        estimated_pump_power_w = None

        notes = (
            "Hydronics estimate v1 placeholder. "
            "No hydraulic sizing performed."
        )

        # ------------------------------------------------------------
        # Assemble result DTO
        # ------------------------------------------------------------
        return HydronicsEstimateResultDTO(
            design_heat_load_w=qt_w,

            design_flow_rate_l_s=design_flow_rate_l_s,
            design_flow_rate_m3_h=design_flow_rate_m3_h,

            flow_temp_c=flow_temp_c,
            return_temp_c=return_temp_c,
            delta_t_k=delta_t_k,

            estimated_system_pressure_drop_pa=estimated_pressure_drop_pa,
            estimated_system_pressure_drop_m=estimated_pressure_drop_m,

            estimated_pump_power_w=estimated_pump_power_w,

            calculation_notes=notes,
            estimate_valid=True,
        )



