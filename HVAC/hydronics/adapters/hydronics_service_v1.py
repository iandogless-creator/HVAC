"""
hydronics_service_v1.py
-----------------------

HVACgooee — Hydronics v1 Service (Single Run)

Purpose
-------
Orchestrate hydronics v1 physics for ONE run:

QT → flow → pipe size → pressure drop → head

Rules
-----
• No GUI imports
• No legacy engines
• No networks
• No fallbacks
• Fail loudly if a canonical solver is missing
"""

from __future__ import annotations

from typing import Optional

from HVAC.hydronics.dto.hydronics_run_result_dto import (
    HydronicsRunInputDTO,
    HydronicsRunResultDTO,
)

# ------------------------------------------------------------------
# Physical constants (explicit v1 defaults)
# ------------------------------------------------------------------
_WATER_RHO_KG_M3 = 998.0          # kg/m³ (≈ 20 °C)
_WATER_CP_J_KG_K = 4180.0         # J/(kg·K)
_WATER_NU_M2_S = 1.0e-6           # m²/s
_PIPE_ROUGHNESS_M = 0.000015      # 0.015 mm (smooth copper)
_G = 9.80665                      # m/s²


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def calculate_single_run_v1(
    inp: HydronicsRunInputDTO,
) -> HydronicsRunResultDTO:
    """
    Calculate a single hydronic run (v1, canonical).
    """

    # ------------------------------------------------------------
    # 1) QT → mass flow → volume flow
    # ------------------------------------------------------------
    if inp.design_delta_t_k <= 0.0:
        return HydronicsRunResultDTO(
            volume_flow_m3_h=0.0,
            mass_flow_kg_s=0.0,
            selected_dn=None,
            velocity_m_s=None,
            dp_total_pa=None,
            head_m=None,
            pump_name=None,
            pump_speed_ratio=None,
            head_margin_m=None,
            notes="design_delta_t_k <= 0 (no flow)",
        )

    mass_flow_kg_s = (
        inp.heat_demand_w / (_WATER_CP_J_KG_K * inp.design_delta_t_k)
    )
    volume_flow_m3_s = mass_flow_kg_s / _WATER_RHO_KG_M3
    volume_flow_m3_h = volume_flow_m3_s * 3600.0

    # ------------------------------------------------------------
    # 2) Pipe sizing (velocity-based, v1)
    # ------------------------------------------------------------
    from HVAC.hydronics.pipe_sizing_solver_v1 import (
        size_pipe_for_flow,
    )

    pipe_sizing = size_pipe_for_flow(
        volume_flow_m3_h=volume_flow_m3_h,
        max_velocity_m_s=0.8,
    )

    selected_pipe = pipe_sizing.selected
    selected_dn = selected_pipe.name
    diameter_m = selected_pipe.internal_diameter_mm / 1000.0
    velocity_m_s = selected_pipe.velocity_m_s

    # ------------------------------------------------------------
    # 3) Pressure drop (Darcy–Weisbach via Colebrook)
    # ------------------------------------------------------------
    from HVAC.hydronics.physics.colebrook import CalcPipe

    pipe_calc = CalcPipe(
        flow_rate=volume_flow_m3_s,
        diameter=diameter_m,
        length=inp.pipe_length_m,
        roughness=_PIPE_ROUGHNESS_M,
        density=_WATER_RHO_KG_M3,
        kinematic_viscosity=_WATER_NU_M2_S,
    )

    dp_total_pa = pipe_calc["pressure_drop"]
    head_m = dp_total_pa / (_WATER_RHO_KG_M3 * _G)

    # ------------------------------------------------------------
    # 4) Assemble result DTO (no pump selection in v1)
    # ------------------------------------------------------------
    return HydronicsRunResultDTO(
        volume_flow_m3_h=volume_flow_m3_h,
        mass_flow_kg_s=mass_flow_kg_s,
        selected_dn=selected_dn,
        velocity_m_s=velocity_m_s,
        dp_total_pa=dp_total_pa,
        head_m=head_m,
        pump_name=None,
        pump_speed_ratio=None,
        head_margin_m=None,
        notes="OK",
    )
