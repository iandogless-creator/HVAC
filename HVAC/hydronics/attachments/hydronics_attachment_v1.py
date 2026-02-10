"""
hydronics_attachment_v1.py
--------------------------

HVACgooee — Hydronics Attachment v1

Purpose
-------
Attach hydronics calculations to a project using:
✔ adjusted QT (from sizing intent)
✔ schematic distribution (duct 1.5 equivalent)
✔ basic emitter sizing (radiators v1)

This module orchestrates hydronics WITHOUT embedding physics
into the project factory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from HVAC.hydronics.config.system_sizing_intent_v1 import SystemSizingIntent
from HVAC.hydronics.distribution.hydronics_distribution_result_v1 import (
    HydronicsDistributionResult,
)
from HVAC.hydronics.emitters.emitter_result_v1 import EmitterResult
from HVAC.hydronics.emitters.radiator_sizer_v1 import RadiatorSizerV1

from HVAC.project.project_factory_v1_LEGACY import apply_system_sizing_intent
from HVAC.heatloss.heatloss_payload_v1 import HeatLossPayload


# ================================================================
# RESULT CONTAINER
# ================================================================
@dataclass(frozen=True)
class HydronicsAttachmentResultV1:
    distribution: HydronicsDistributionResult
    emitters: List[EmitterResult]


# ================================================================
# ATTACHMENT ENTRY POINT
# ================================================================
def attach_hydronics_v1(
    *,
    heatloss_payload: HeatLossPayload,
    sizing_intent: Optional[SystemSizingIntent],
    design_deltaT_K: float = 20.0,
) -> HydronicsAttachmentResultV1:
    """
    Attach hydronics calculations to a project (v1).

    Parameters
    ----------
    heatloss_payload:
        Fabric heat-loss payload (QT source).

    sizing_intent:
        User-defined oversizing intent (applied once).

    design_deltaT_K:
        Chosen system ΔT for hydronics (K).
    """

    # ------------------------------------------------------------
    # 1) Base QT from heat-loss
    # ------------------------------------------------------------
    QT_base_W = heatloss_payload.design_heat_loss_W

    # ------------------------------------------------------------
    # 2) Apply sizing intent (ONCE)
    # ------------------------------------------------------------
    QT_emitters_W, QT_boiler_W = apply_system_sizing_intent(
        QT_W=QT_base_W,
        sizing_intent=sizing_intent,
    )

    # ------------------------------------------------------------
    # 3) Duct 1.5 / distribution estimate
    # ------------------------------------------------------------
    # Q = rho * cp * Vdot * ΔT
    # Use water defaults for v1
    rho = 998.0          # kg/m³
    cp = 4180.0          # J/kg·K

    flow_rate_m3_s = QT_emitters_W / (rho * cp * design_deltaT_K)

    distribution = HydronicsDistributionResult(
        required_output_W=QT_emitters_W,
        design_deltaT_K=design_deltaT_K,
        required_flow_rate_m3_s=flow_rate_m3_s,
        notes="Schematic distribution (v1)",
    )

    # ------------------------------------------------------------
    # 4) Emitters (Radiators v1)
    # ------------------------------------------------------------
    radiator_sizer = RadiatorSizerV1()

    radiator = radiator_sizer.size_emitter(
        required_output_W=QT_emitters_W,
        flow_rate_m3_s=flow_rate_m3_s,
        available_pressure_Pa=5000.0,  # schematic allowance
        mean_water_deltaT_K=design_deltaT_K,
    )

    # ------------------------------------------------------------
    # 5) Return attachment result
    # ------------------------------------------------------------
    return HydronicsAttachmentResultV1(
        distribution=distribution,
        emitters=[radiator],
    )
