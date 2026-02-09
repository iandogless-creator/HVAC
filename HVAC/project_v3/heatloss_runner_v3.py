# ======================================================================
# HVAC/heatloss_v3/heatloss_runner_v3.py
# ======================================================================

"""
HVACgooee — Heat-Loss Runner v3 (CANONICAL)

Purpose
-------
Project-level orchestration for heat-loss calculations.

RULES (LOCKED)
--------------
• Runner owns fabric + ventilation physics
• Geometry comes from ProjectV3 spaces/surfaces
• surface.surface_class MUST be SurfaceClass (enum)
• U-values come ONLY from ConstructionUValueResultDTO in ProjectState
• Commits results to ProjectState
• Explicitly invalidates hydronics
• NO GUI imports
• NO legacy surface_type
"""

from __future__ import annotations

from HVAC_legacy.project.project_state import ProjectState
from HVAC_legacy.constructions.construction_preset import SurfaceClass
from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)


class HeatLossRunnerV3:
    """
    Canonical heat-loss runner (v3).
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    def run(project) -> None:
        project_state: ProjectState = project.project_state

        # project.project_info may be dict-like or object-like depending on loader
        info = getattr(project, "project_info", {}) or {}
        if isinstance(info, dict):
            external_temp = float(info.get("design_temp_outside_C", 0.0))
        else:
            external_temp = float(getattr(info, "design_temp_outside_C", 0.0))

        total_qt_w = 0.0

        for space in project.spaces:
            delta_t = float(space.design_temp_C) - external_temp

            # ------------------------------
            # Fabric heat-loss
            # ------------------------------
            qf = 0.0

            for surface in space.surfaces:
                u_value = HeatLossRunnerV3._resolve_u_value(
                    surface=surface,
                    project_state=project_state,
                )

                if u_value is None:
                    continue

                qf += u_value * float(surface.area_m2) * delta_t

            # ------------------------------
            # Ventilation heat-loss (optional)
            # ------------------------------
            qv = 0.0

            if hasattr(space, "ventilation_ach"):
                air_density = 1.2     # kg/m³
                air_cp = 1005.0       # J/kg·K

                volume = float(getattr(space, "volume_m3", 0.0) or 0.0)
                ach = float(getattr(space, "ventilation_ach", 0.0) or 0.0)

                qv = (
                    air_density
                    * air_cp
                    * volume
                    * ach
                    * delta_t
                    / 3600.0
                )

            total_qt_w += qf + qv

        # ------------------------------
        # Commit (single authority)
        # ------------------------------
        project_state.commit_heatloss_result(qt_w=total_qt_w)

    # ------------------------------------------------------------------
    # Construction resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_u_value(
        *,
        surface,
        project_state: ProjectState,
    ) -> float | None:
        """
        Resolve U-value for a surface.

        HARD CONTRACT:
        • surface.surface_class MUST be SurfaceClass
        • legacy surface_type MUST NOT exist
        """

        if hasattr(surface, "surface_type"):
            raise RuntimeError(
                f"Legacy surface_type leaked into v3: surface_id={getattr(surface, 'surface_id', '?')}"
            )

        surface_id = getattr(surface, "surface_id", "?")
        surface_class = getattr(surface, "surface_class", None)

        if surface_class is None:
            raise RuntimeError(f"Surface {surface_id} has no surface_class")

        if not isinstance(surface_class, SurfaceClass):
            raise TypeError(
                f"Surface {surface_id} surface_class must be SurfaceClass, "
                f"got {type(surface_class)} ({surface_class!r})"
            )

        dto: ConstructionUValueResultDTO | None = (
            project_state.constructions.get(surface_class)
        )

        if dto is None:
            print(
                f"[WARN] No U-value for surface_class={surface_class.name}; "
                f"surface_id={surface_id}"
            )
            return None

        return float(dto.u_value)
