# ======================================================================
# HVACgooee — Heat-Loss Controller (V4)
# Phase II-A / II-B
# PURE ORCHESTRATOR (CANONICAL)
# ======================================================================

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from HVAC.project.project_state import ProjectState

from HVAC.heatloss.engines.fabric_heatloss_engine import FabricHeatLossEngine
from HVAC.heatloss.dto.fabric_inputs import (
    FabricHeatLossInputDTO,
    FabricSurfaceInputDTO,
)


class HeatLossControllerV4:
    """
    V4 Heat-Loss Orchestrator (Phase II-B.1 Locked)

    Authority
    ---------
    • No state
    • No GUI logic
    • No readiness evaluation
    • No persistence logic beyond result hand-off

    Phase II-B Contract
    -------------------
    • Readiness MUST already be validated by caller
    • This controller MUST NOT call evaluate_heatloss_readiness()
    • If invoked, execution permission is assumed
    """

    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------
    def run(
            self,
            *,
            project: ProjectState,
            internal_design_temp_C: float,
            ach: float,
    ) -> None:
        """
        Execute heat-loss calculation (Fabric + Ventilation + Qt).

        Precondition (LOCKED):
            Readiness already validated by caller.
        """

        # --------------------------------------------------------------
        # Phase II-A — Fabric
        # --------------------------------------------------------------
        fabric_input = self._build_fabric_input(
            project=project,
            ti_C=internal_design_temp_C,
        )

        fabric_result = FabricHeatLossEngine.run(fabric_input)

        # Replace fabric result (authoritative)
        project.set_fabric_heatloss_result(fabric_result)

        # --------------------------------------------------------------
        # Phase II-B — Ventilation (Room-Level)
        # --------------------------------------------------------------
        ventilation_result = self._build_ventilation_result(
            project=project,
            ti_C=internal_design_temp_C,
            ach=ach,
        )

        # --------------------------------------------------------------
        # Phase II-C — Qt Aggregation
        # --------------------------------------------------------------
        qt_result = self._build_qt_result(
            fabric_result=fabric_result,
            ventilation_result=ventilation_result,
        )

        # --------------------------------------------------------------
        # Authoritative Container Commit (atomic shape)
        # --------------------------------------------------------------
        container = {
            "fabric": fabric_result,
            "ventilation": ventilation_result,
            "room_totals": qt_result,
        }

        project.heatloss_results = container
        project.mark_heatloss_valid()

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
        if env is None or env.external_design_temperature is None:
            raise RuntimeError("External design temperature not set")

        te_C = env.external_design_temperature
        delta_t = ti_C - te_C

        qv_by_room: dict[str, float] = {}

        for room_id, room in project.rooms.items():
            space = getattr(room, "space", None)
            if space is None:
                continue

            volume = (
                    float(getattr(space, "floor_area_m2", 0.0))
                    * float(getattr(space, "height_m", 0.0))
            )

            qv = 0.33 * ach * volume * delta_t
            qv_by_room[room_id] = qv

        return {
            "qv_by_room_W": qv_by_room,
            "total_qv_W": sum(qv_by_room.values()),
        }

    # ------------------------------------------------------------------
    # Phase II-C — Qt aggregation (Room-Level)
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
    # Phase II-A — Fabric input assembly (STRUCTURAL ONLY)
    # ------------------------------------------------------------------
    @staticmethod
    def _build_fabric_input(
        *,
        project: ProjectState,
        ti_C: float,
    ) -> FabricHeatLossInputDTO:
        env = project.environment
        if env is None or env.external_design_temperature is None:
            raise RuntimeError("External design temperature not set")

        if ti_C is None:
            raise RuntimeError("Internal design temperature not supplied")

        te_C = env.external_design_temperature
        delta_t = ti_C - te_C
        if delta_t <= 0:
            raise RuntimeError(
                f"Invalid ΔT (Ti={ti_C}, Te={te_C}) — must be > 0"
            )

        resolved_surfaces = list(project.iter_fabric_surfaces())
        if not resolved_surfaces:
            raise RuntimeError("No fabric surfaces declared")

        surface_inputs: list[FabricSurfaceInputDTO] = []

        for s in resolved_surfaces:
            surface = s.surface

            surface_inputs.append(
                FabricSurfaceInputDTO(
                    surface_id=surface.surface_id,
                    room_id=surface.room_id,
                    surface_class=(
                        surface.surface_class.value
                        if hasattr(surface.surface_class, "value")
                        else str(surface.surface_class)
                    ),
                    area_m2=surface.area_m2,
                    u_value_W_m2K=s.u_value_W_m2K,
                    delta_t_K=delta_t,
                )
            )

        return FabricHeatLossInputDTO(
            surfaces=surface_inputs,
            internal_design_temp_C=ti_C,
            external_design_temp_C=te_C,
            project_id=project.project_id,
        )