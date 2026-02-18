# ======================================================================
# HVAC/heatloss_v3/heatloss_runner_v3.py
# ======================================================================

"""
HVACgooee — Heat-Loss Runner v3 (CANONICAL)

Purpose
-------
Pure, project-level steady-state heat-loss computation.

RULES (LOCKED)
--------------
• Runner is PURE (no mutation)
• Reads ProjectState (read-only)
• Returns authoritative Qt
• NEVER sets validity flags
• NEVER commits to ProjectState
• NEVER imports GUI
"""

from __future__ import annotations
from typing import Dict

OverridesT = Dict[str, Dict[str, Dict[str, float]]]

from HVAC.project.project_state import ProjectState
from HVAC.constructions.construction_preset import SurfaceClass
from HVAC.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)

# ------------------------------------------------------------------
# Worksheet override resolution (Phase G-A)
# ------------------------------------------------------------------

def _override(
    overrides: OverridesT,
    *,
    room_id: str,
    element_id: str,
    field: str,
    derived: float,
) -> float:
    """
    Resolve effective value using worksheet overrides.

    Precedence:
        override → derived

    Notes:
    • Read-only
    • Safe if overrides are missing
    """
    try:
        return overrides[room_id][element_id][field]
    except KeyError:
        return derived

class HeatLossRunnerV3:
    """
    Pure heat-loss runner (v3).

    Consumes (read-only):
        • ProjectState.constructions
        • project.spaces
        • project.project_info["outside_temperature_c"]  (steady-state To / teo)

    Produces:
        • float Qt (authoritative)

    Raises:
        RuntimeError on missing required constructions or environment data
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    def run_authoritative_qt(project) -> float:
        project_state: ProjectState = project.project_state

        print("[HeatLossRunnerV3] ProjectState id:", id(project_state))
        print("[HeatLossRunnerV3] constructions:", project_state.constructions)

        # ------------------------------------------------------------
        # Guard: required constructions
        # ------------------------------------------------------------
        required = (
            SurfaceClass.EXTERNAL_WALL,
            SurfaceClass.WINDOW,
            SurfaceClass.FLOOR,
        )

        missing = [
            sc for sc in required
            if sc not in project_state.constructions.results
        ]

        if missing:
            raise RuntimeError(
                "Missing constructions for: "
                + ", ".join(sc.value for sc in missing)
            )

        # ------------------------------------------------------------
        # Guard: external temperature (steady-state To / teo)
        # ------------------------------------------------------------
        try:
            external_temp = float(
                project.project_info["outside_temperature_c"]
            )
        except KeyError as exc:
            raise RuntimeError(
                "Project missing outside_temperature_c"
            ) from exc

        total_qt_w = 0.0

        # ------------------------------------------------------------
        # Per-space aggregation (Phase G-A)
        # ------------------------------------------------------------
        overrides = project_state.heatloss.overrides

        for space in project.spaces:
            room_id = space.id
            derived_delta_t = space.design_temp_C - external_temp

            for surface in space.surfaces:
                element_id = surface.id

                u_derived = HeatLossRunnerV3._u_value_for_surface(
                    surface.surface_class,
                    project_state,
                )
                if u_derived is None:
                    continue

                area = _override(
                    overrides,
                    room_id=room_id,
                    element_id=element_id,
                    field="area_m2",
                    derived=surface.area_m2,
                )

                delta_t = _override(
                    overrides,
                    room_id=room_id,
                    element_id=element_id,
                    field="delta_t_k",
                    derived=derived_delta_t,
                )

                u_value = _override(
                    overrides,
                    room_id=room_id,
                    element_id=element_id,
                    field="u_value",
                    derived=u_derived,
                )

                total_qt_w += area * u_value * delta_t

    # ------------------------------------------------------------------
    # Construction DTO resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _u_value_for_surface(
        surface_class: SurfaceClass,
        project_state: ProjectState,
    ) -> float | None:
        dto: ConstructionUValueResultDTO | None = (
            project_state.constructions.results.get(surface_class)
        )

        if dto is None:
            print(
                f"[WARN] No construction DTO for surface "
                f"{surface_class.value}; skipping"
            )
            return None

        return dto.u_value

    def _override(
            overrides: dict,
            *,
            room_id: str,
            element_id: str,
            field: str,
            derived: float,
    ) -> float:
        """
        Resolve effective value using worksheet overrides.

        Precedence:
        override → derived
        """
        try:
            return overrides[room_id][element_id][field]
        except KeyError:
            return derived
