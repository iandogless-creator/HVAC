# ======================================================================
# HVAC/heatloss/engines/fabric_heatloss_engine.py
# ======================================================================
"""
fabric_heatloss_engine.py
-------------------------

Fabric heat-loss engine for HVACgooee.

Phase II-A / II-C (LOCKED SCOPE)
--------------------------------
Implements steady-state fabric transmission heat loss only:

    Qf = U * A * ΔT      [W]

Dynamic fabric effects (Y-values) are NOT used in this engine.
They belong to a future dynamic phase and must not appear in the
steady-state execution path.

Ventilation / infiltration is handled separately in
ventilation_heatloss_engine.py.

Notes on compatibility
----------------------
This module still contains a small set of legacy/internal helper models
(FabricSurface, compute_* helpers). They are NOT part of the controller
contract. HeatLossControllerV4 must import only FabricHeatLossEngine.

The controller-facing return is currently a dict (Phase II-A/II-C safe).
Phase II-D may formalise a ResultDTO without changing the physics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from HVAC.heatloss.dto.fabric_inputs import FabricHeatLossInputDTO


# ---------------------------------------------------------------------------
# Legacy/internal helper model (NOT a controller contract)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class FabricSurface:
    """
    Single building element contributing to fabric heat loss.

    NOTE:
    - This helper may exist for legacy/demo use, but MUST NOT be imported
      by HeatLossControllerV4. Controller imports only FabricHeatLossEngine.
    - Y_W_m2K is NOT used in steady-state fabric path.
    """
    id: str
    name: str
    U_W_m2K: float
    area_m2: float

    # Future/dynamic only (kept for later, NOT used here)
    Y_W_m2K: Optional[float] = None

    meta: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class FabricLossBreakdown:
    """
    Result container for fabric heat-loss.

    Per-surface and total heat losses (in Watts).
    """
    surfaces: List[Dict[str, float]]  # [{id, U, A, dT, Q_W}, ...]
    total_W: float


# ---------------------------------------------------------------------------
# Steady-state helpers (engine-internal)
# ---------------------------------------------------------------------------

def compute_surface_loss(
    surface: FabricSurface,
    temp_inside_C: float,
    temp_outside_C: float,
) -> float:
    """
    Steady-state surface heat loss:

        Q = U * A * (Ti - Te)

    No Y-values. No modifiers. No heuristics.
    """
    dT = temp_inside_C - temp_outside_C
    if dT <= 0:
        return 0.0
    return surface.U_W_m2K * surface.area_m2 * dT


def compute_fabric_loss(
    surfaces: List[FabricSurface],
    temp_inside_C: float,
    temp_outside_C: float,
) -> FabricLossBreakdown:
    """
    Steady-state fabric heat loss for a list of surfaces.
    """
    breakdown_list: List[Dict[str, float]] = []
    total = 0.0

    dT = temp_inside_C - temp_outside_C
    if dT <= 0:
        return FabricLossBreakdown(surfaces=[], total_W=0.0)

    for s in surfaces:
        q = compute_surface_loss(s, temp_inside_C, temp_outside_C)
        total += q
        breakdown_list.append(
            {
                "id": s.id,
                "U_W_m2K": s.U_W_m2K,
                "area_m2": s.area_m2,
                "dT_K": dT,
                "Q_W": q,
            }
        )

    return FabricLossBreakdown(surfaces=breakdown_list, total_W=total)


def compute_room_fabric_loss(
    room_id: str,
    room_surfaces: List[FabricSurface],
    design_temp_inside_C: float,
    design_temp_outside_C: float,
) -> Dict[str, float]:
    """
    Legacy convenience wrapper (still steady-state clean).
    """
    breakdown = compute_fabric_loss(
        room_surfaces,
        temp_inside_C=design_temp_inside_C,
        temp_outside_C=design_temp_outside_C,
    )

    return {
        "room_id": room_id,
        "fabric_loss_W": breakdown.total_W,
    }


# ---------------------------------------------------------------------------
# Canonical engine entry point (controller-importable)
# ---------------------------------------------------------------------------

class FabricHeatLossEngine:
    """
    Fabric transmission heat-loss engine (PURE, LOCKED)

    Contract (locked by Phase II-A/II-C):
    • DTO in, dict out (temporary shape)
    • Pure, stateless
    • No ProjectState access
    • No GUI imports
    • No inference / no defaults
    • Physics: Qf = U × A × ΔT; totals are ΣQf only
    """

    @staticmethod
    def run(input_dto: FabricHeatLossInputDTO) -> Dict[str, Any]:
        if input_dto is None:
            raise RuntimeError("FabricHeatLossEngine.run: input_dto is None")

        if not input_dto.surfaces:
            raise RuntimeError("FabricHeatLossEngine.run: no surfaces supplied")

        rows: List[Dict[str, Any]] = []
        total_W: float = 0.0
        total_by_room_W: Dict[str, float] = {}

        for s in input_dto.surfaces:
            if s.area_m2 <= 0:
                raise RuntimeError(
                    f"Invalid area for surface '{s.surface_id}': {s.area_m2}"
                )
            if s.u_value_W_m2K <= 0:
                raise RuntimeError(
                    f"Invalid U-value for surface '{s.surface_id}': {s.u_value_W_m2K}"
                )
            if s.delta_t_K <= 0:
                raise RuntimeError(
                    f"Invalid ΔT for surface '{s.surface_id}': {s.delta_t_K}"
                )

            # Phase II-A/II-C locked physics
            q_W = float(s.area_m2) * float(s.u_value_W_m2K) * float(s.delta_t_K)

            # Rows: keep backward compatible keys, plus explicit Qf aliases.
            rows.append(
                {
                    "surface_id": s.surface_id,
                    "room_id": s.room_id,
                    "surface_class": s.surface_class,
                    "area_m2": float(s.area_m2),
                    "u_value_W_m2K": float(s.u_value_W_m2K),
                    "delta_t_K": float(s.delta_t_K),

                    # Back-compat (existing consumers)
                    "q_W": q_W,
                    "total_term": "U*A*dT",

                    # Canonical naming going forward (safe additive)
                    "qf_W": q_W,
                }
            )

            total_W += q_W
            total_by_room_W[s.room_id] = total_by_room_W.get(s.room_id, 0.0) + q_W

        # Return: keep existing keys, plus additive canonical aliases.
        return {
            "project_id": input_dto.project_id,
            "internal_design_temp_C": float(input_dto.internal_design_temp_C),
            "external_design_temp_C": float(input_dto.external_design_temp_C),

            # Back-compat
            "rows": rows,
            "total_fabric_W": total_W,
            "total_by_room_W": total_by_room_W,

            # Canonical aliases (additive)
            "total_qf_W": total_W,
            "qf_by_room_W": total_by_room_W,
        }