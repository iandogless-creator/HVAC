# ======================================================================
# HVACgooee — Heat-Loss Controller (V4)
# Phase II-A / II-B / II-C
# PURE ORCHESTRATOR (CANONICAL)
# ======================================================================

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from HVAC.project.project_state import ProjectState

from HVAC.heatloss.engines.fabric_heatloss_engine import FabricHeatLossEngine
from HVAC.heatloss.dto.fabric_inputs import FabricSurfaceInputDTO
from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1


class HeatLossControllerV4:

    def __init__(self, *, project_state: ProjectState) -> None:
        self._ps = project_state

    @staticmethod
    def run(
            self,
            *,
            internal_design_temp_C: float,
            ach: float,
    ) -> None:
        project = self._ps

        # existing logic unchanged
        """
        Execute heat-loss calculation (Fabric + Ventilation + Qt).

        Precondition:
            Readiness already validated by caller.
        """
        print(">>> RUN METHOD HIT")
        # --------------------------------------------------------------
        # Phase II-A — Fabric
        # --------------------------------------------------------------
        fabric_input = self._build_fabric_input(
            project=project,
            ti_C=internal_design_temp_C,
        )

        fabric_result = FabricHeatLossEngine.run(fabric_input)
        project.set_fabric_heatloss_result(fabric_result)

        # --------------------------------------------------------------
        # Phase II-B — Ventilation
        # --------------------------------------------------------------
        ventilation_result = self._build_ventilation_result(
            project=project,
            ti_C=internal_design_temp_C,
            ach=ach,
        )
        project.set_ventilation_heatloss_result(ventilation_result)
        # --------------------------------------------------------------
        # Phase II-C — Qt aggregation
        # --------------------------------------------------------------
        qt_result = self._build_qt_result(
            fabric_result=fabric_result,
            ventilation_result=ventilation_result,
        )

        # --------------------------------------------------------------
        # Authoritative container commit
        # --------------------------------------------------------------
        container = {
            "fabric": fabric_result,
            "ventilation": ventilation_result,
            "room_totals": qt_result,
        }

        project.heatloss_results = container
        project.mark_heatloss_valid()

    # ------------------------------------------------------------------
    # Phase II-A — Fabric input assembly
    # ------------------------------------------------------------------
    @staticmethod
    def _build_fabric_input(
        *,
        project: ProjectState,
        ti_C: float,
    ) -> list[FabricSurfaceInputDTO]:
        env = project.environment
        if env is None or env.external_design_temp_C is None:
            raise RuntimeError("External design temperature not set")

        if ti_C is None:
            raise RuntimeError("Internal design temperature not supplied")

        te_C = float(env.external_design_temp_C)

        # Canonical source: topology-derived fabric rows
        resolved_surfaces = list(FabricFromSegmentsV1.apply_to_project(project))

        if not resolved_surfaces:
            raise RuntimeError("No fabric surfaces declared")

        surface_inputs: list[FabricSurfaceInputDTO] = []

        for s in resolved_surfaces:
            delta_t = HeatLossControllerV4._resolve_surface_delta_t(
                surface=s,
                ti_C=ti_C,
                te_C=te_C,
            )

            if delta_t <= 0:
                raise RuntimeError(
                    f"Invalid ΔT (Ti={ti_C}, Te={te_C}) — must be > 0"
                )

            surface_inputs.append(
                FabricSurfaceInputDTO(
                    surface_id=str(s.surface_id),
                    room_id=str(s.room_id),
                    surface_class=str(getattr(s, "surface_class", "unknown")),
                    area_m2=float(s.area_m2),
                    u_value_W_m2K=float(s.u_value_W_m2K),
                    delta_t_K=float(delta_t),
                )
            )

        return surface_inputs

    # ------------------------------------------------------------------
    # Phase II-B — Ventilation result assembly
    # ------------------------------------------------------------------
    @staticmethod
    def _build_ventilation_result(
        *,
        project: ProjectState,
        ti_C: float,
        ach: float,
    ) -> dict:
        env = project.environment
        if env is None or env.external_design_temp_C is None:
            raise RuntimeError("External design temperature not set")

        te_C = float(env.external_design_temp_C)
        delta_t = float(ti_C) - te_C

        qv_by_room: dict[str, float] = {}

        for room_id, room in project.rooms.items():
            g = getattr(room, "geometry", None)
            if g is None:
                continue

            area = getattr(g, "floor_area_m2", None)
            if callable(area):
                area = area()

            height = getattr(g, "height_m", None)
            if height is None:
                height = getattr(g, "height_override_m", None)

            if area is None or height is None:
                continue

            volume = float(area) * float(height)
            qv = 0.33 * float(ach) * volume * delta_t
            qv_by_room[str(room_id)] = qv

        return {
            "qv_by_room_W": qv_by_room,
            "total_qv_W": sum(qv_by_room.values()),
        }

    # ------------------------------------------------------------------
    # Phase II-C — Qt aggregation
    # ------------------------------------------------------------------
    @staticmethod
    def _build_qt_result(
        *,
        fabric_result: dict,
        ventilation_result: dict,
    ) -> dict:
        qf_by_room = fabric_result.get("qf_by_room_W", {})
        qv_by_room = ventilation_result.get("qv_by_room_W", {})

        qt_by_room: dict[str, float] = {}
        all_rooms = set(qf_by_room.keys()) | set(qv_by_room.keys())

        for room_id in all_rooms:
            qt_by_room[room_id] = (
                float(qf_by_room.get(room_id, 0.0))
                + float(qv_by_room.get(room_id, 0.0))
            )

        return {
            "qt_by_room_W": qt_by_room,
            "total_qt_W": sum(qt_by_room.values()),
        }

    # ------------------------------------------------------------------
    # Surface ΔT resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_surface_delta_t(
        *,
        surface,
        ti_C: float,
        te_C: float,
    ) -> float:
        boundary_kind = str(getattr(surface, "boundary_kind", "EXTERNAL")).upper()

        if boundary_kind == "EXTERNAL":
            return float(ti_C) - float(te_C)

        if boundary_kind == "ADIABATIC":
            return 0.0

        if boundary_kind == "INTER_ROOM":
            # Phase IV dev rule: unresolved inter-room treated as zero ΔT
            return 0.0

        return float(ti_C) - float(te_C)