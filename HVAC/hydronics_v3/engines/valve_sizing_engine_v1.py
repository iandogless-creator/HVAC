# ======================================================================
# HVAC/hydronics_v3/engines/valve_sizing_engine_v1.py
# ======================================================================

"""
HVACgooee — Valve Sizing Engine v1

Purpose
-------
Selects the smallest acceptable valve Kv that satisfies the
required pressure drop at design flow.

DTO-in / DTO-out.
No mutation.
No iteration.
Red-stop on failure.
"""

from __future__ import annotations

import math
from typing import List

from HVAC.hydronics_v3.dto.valve_catalog_dto import ValveCatalogDTO
from HVAC.hydronics_v3.dto.valve_sizing_input_dto import ValveSizingInputDTO
from HVAC.hydronics_v3.dto.valve_sizing_result_dto import ValveSizingResultDTO


class ValveSizingEngineV1:
    """
    Canonical Kv selection engine.
    """

    @staticmethod
    def run(
        sizing_input: ValveSizingInputDTO,
        catalog: ValveCatalogDTO,
    ) -> ValveSizingResultDTO:
        # ------------------------------------------------------------
        # Guards — red anywhere means stop
        # ------------------------------------------------------------

        if sizing_input.design_flow_m3_h <= 0:
            raise ValueError("Design flow must be > 0 m3/h")

        if sizing_input.required_valve_dp_pa <= 0:
            raise ValueError("Required valve Δp must be > 0 Pa")

        if not catalog.kv_options:
            raise ValueError("Valve catalog is empty")

        # ------------------------------------------------------------
        # Convert Pa → bar (Kv equation domain)
        # ------------------------------------------------------------

        required_dp_bar = sizing_input.required_valve_dp_pa / 1e5

        # ------------------------------------------------------------
        # Required Kv from equation
        # ------------------------------------------------------------

        required_kv = (
            sizing_input.design_flow_m3_h
            / math.sqrt(required_dp_bar)
        )

        # ------------------------------------------------------------
        # Select smallest Kv ≥ required_kv
        # ------------------------------------------------------------

        sorted_options = sorted(
            catalog.kv_options, key=lambda o: o.kv_m3_h
        )

        for option in sorted_options:
            if option.kv_m3_h >= required_kv:
                achieved_dp_bar = (
                    sizing_input.design_flow_m3_h / option.kv_m3_h
                ) ** 2
                achieved_dp_pa = achieved_dp_bar * 1e5

                return ValveSizingResultDTO(
                    terminal_leg_id=sizing_input.terminal_leg_id,
                    valve_ref=option.valve_ref,
                    selected_kv_m3_h=option.kv_m3_h,
                    achieved_valve_dp_pa=achieved_dp_pa,
                    note="Selected smallest Kv meeting required Δp",
                )

        # ------------------------------------------------------------
        # Red stop — no valve can meet requirement
        # ------------------------------------------------------------

        raise ValueError(
            f"No valve in catalog can meet required Kv "
            f"{required_kv:.3f} m3/h for terminal "
            f"{sizing_input.terminal_leg_id}"
        )
