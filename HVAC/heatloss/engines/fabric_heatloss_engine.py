# ======================================================================
# HVAC/heatloss/engines/fabric_heatloss_engine.py
# ======================================================================
"""
HVACgooee — Fabric Heat Loss Engine (v1)

Pure physics engine.

Inputs
------
List[FabricSurfaceInputDTO]

Computes
--------
Q = U × A × ΔT

Returns row results for aggregation by the controller/orchestrator.

Rules
-----
• No ProjectState imports
• No GUI logic
• No persistence
• Pure calculation only
"""

from __future__ import annotations

from typing import Iterable, List

from HVAC.heatloss.dto.fabric_inputs import FabricSurfaceInputDTO


# ======================================================================
# Engine
# ======================================================================

class FabricHeatLossEngine:
    """
    Fabric heat-loss physics engine.

    Stateless pure calculation.
    """

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def run(
        self,
        surfaces: Iterable[FabricSurfaceInputDTO],
    ) -> list[dict]:

        results: List[dict] = []

        for s in surfaces:

            q = (
                float(s.u_value_W_m2K)
                * float(s.area_m2)
                * float(s.delta_t_K)
            )

            results.append(
                {
                    "surface_id": s.surface_id,
                    "room_id": s.room_id,
                    "surface_class": s.surface_class,
                    "area_m2": s.area_m2,
                    "u_value_W_m2K": s.u_value_W_m2K,
                    "delta_t_K": s.delta_t_K,
                    "q_fabric_W": q,
                }
            )

        return results