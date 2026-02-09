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

from HVAC_legacy.project.project_state import ProjectState
from HVAC_legacy.constructions.construction_preset import SurfaceClass
from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)


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
        # Per-space aggregation (MINIMAL v1)
        # ------------------------------------------------------------
        for space in project.spaces:
            delta_t = space.design_temp_C - external_temp  # Ti - To

            for surface in space.surfaces:
                u = HeatLossRunnerV3._u_value_for_surface(
                    surface.surface_class,
                    project_state,
                )
                if u is None:
                    continue

                total_qt_w += u * surface.area_m2 * delta_t

        return total_qt_w

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
