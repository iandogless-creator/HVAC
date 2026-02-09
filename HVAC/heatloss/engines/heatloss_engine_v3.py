# ======================================================================
# BEGIN FILE: HVAC/heatloss/engines/heatloss_engine_v3.py
# ======================================================================
"""
heatloss_engine_v3.py
---------------------

HVACgooee — Heat-Loss Engine v3 (Domain)

Purpose
-------
Compute room heat loss using:
    • Fabric: Σ(U * A * ΔT)
    • Ventilation (v3): ACH → W using ρ·cp·Vdot·ΔT

RULES
-----
• Domain-only (NO GUI, NO DTOs)
• Uses ConstructionPreset (resolved U-values)
• Returns engine-owned result objects
• No project I/O
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from HVAC_legacy.constructions.construction_preset import ConstructionPreset


# ----------------------------------------------------------------------
# Constants (v3)
# ----------------------------------------------------------------------

AIR_DENSITY_KG_M3: float = 1.20     # kg/m³ (dry air ~20°C, sea level)
AIR_CP_J_KG_K: float = 1006.0       # J/(kg·K)


# ----------------------------------------------------------------------
# Inputs (domain)
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryHeatLossInput:
    element_type: str
    area_m2: float
    construction: ConstructionPreset


@dataclass(frozen=True)
class RoomHeatLossInput:
    room_name: str
    internal_temp_c: float
    external_temp_c: float
    boundaries: List[BoundaryHeatLossInput]

    # ventilation (optional)
    room_volume_m3: Optional[float] = None
    ventilation_ach: Optional[float] = None
    ventilation_method: str = "ACH (v3)"


# ----------------------------------------------------------------------
# Results (engine-owned)
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryHeatLossResult:
    element_type: str
    area_m2: float
    u_value: float
    construction_ref: str
    construction_name: str
    delta_t_k: float
    heat_loss_w: float


@dataclass(frozen=True)
class VentilationHeatLossResult:
    method: str
    ach: float
    volume_m3: float
    delta_t_k: float
    heat_loss_w: float


@dataclass(frozen=True)
class RoomHeatLossResult:
    room_name: str
    internal_temp_c: float
    external_temp_c: float

    boundaries: List[BoundaryHeatLossResult]

    total_fabric_heat_loss_w: float

    # ventilation
    ventilation: Optional[VentilationHeatLossResult]
    ventilation_heat_loss_w: float

    # totals
    total_heat_loss_w: float


# ----------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------

class HeatLossEngineV3:
    """
    Domain heat-loss engine (v3).

    Fabric:
        Qt_fabric = Σ(U * A * ΔT)

    Ventilation (v3):
        Vdot = ACH * FREEZE_INDEX.md / 3600   (m³/s)
        Qv   = ρ * cp * Vdot * ΔT
    """

    def compute_room(self, room: RoomHeatLossInput) -> RoomHeatLossResult:
        delta_t_k = max(0.0, float(room.internal_temp_c) - float(room.external_temp_c))

        # ----------------------------
        # Fabric
        # ----------------------------
        boundary_results: List[BoundaryHeatLossResult] = []
        q_fabric_total = 0.0

        for b in room.boundaries:
            u = float(b.construction.u_value)
            a = float(b.area_m2)
            q = u * a * delta_t_k

            boundary_results.append(
                BoundaryHeatLossResult(
                    element_type=str(b.element_type),
                    area_m2=a,
                    u_value=u,
                    construction_ref=str(b.construction.ref),
                    construction_name=str(b.construction.name),
                    delta_t_k=delta_t_k,
                    heat_loss_w=q,
                )
            )
            q_fabric_total += q

        # ----------------------------
        # Ventilation (ACH → W)
        # ----------------------------
        vent_result: Optional[VentilationHeatLossResult] = None
        q_vent = 0.0

        if (
            room.room_volume_m3 is not None
            and room.ventilation_ach is not None
            and delta_t_k > 0.0
        ):
            vol_m3 = float(room.room_volume_m3)
            ach = float(room.ventilation_ach)

            if vol_m3 > 0.0 and ach > 0.0:
                vdot_m3_s = ach * vol_m3 / 3600.0
                q_vent = AIR_DENSITY_KG_M3 * AIR_CP_J_KG_K * vdot_m3_s * delta_t_k

                vent_result = VentilationHeatLossResult(
                    method=str(room.ventilation_method or "ACH (v3)"),
                    ach=ach,
                    volume_m3=vol_m3,
                    delta_t_k=delta_t_k,
                    heat_loss_w=q_vent,
                )

        total = q_fabric_total + q_vent

        return RoomHeatLossResult(
            room_name=str(room.room_name),
            internal_temp_c=float(room.internal_temp_c),
            external_temp_c=float(room.external_temp_c),
            boundaries=boundary_results,
            total_fabric_heat_loss_w=q_fabric_total,
            ventilation=vent_result,
            ventilation_heat_loss_w=q_vent,
            total_heat_loss_w=total,
        )


# ======================================================================
# END FILE: HVAC/heatloss/engines/heatloss_engine_v3.py
# ======================================================================
