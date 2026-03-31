# ======================================================================
# HVACgooee — Heat-Loss Controller (V4 Orchestrator)
# Phase: II-D Snapshot Isolation
# Status: CANONICAL — ORCHESTRATION ONLY
# ======================================================================

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from HVAC.project.project_state import ProjectState

# ----------------------------------------------------------------------
# Resolution (pure derivation)
# ----------------------------------------------------------------------
from HVAC.heatloss.resolution.effective_snapshot_builder import (
    build_effective_project_snapshot,
)

# ----------------------------------------------------------------------
# Engines (pure physics)
# ----------------------------------------------------------------------
from HVAC.heatloss.engines.fabric_heatloss_engine import FabricHeatLossEngine
from HVAC.heatloss.engines.ventilation_heatloss_engine import (
    VentilationHeatLossEngine,
)

# ----------------------------------------------------------------------
# Authoritative results (locked)
# ----------------------------------------------------------------------
from HVAC.heatloss.dto.heatloss_results_dto import (
    ProjectHeatLossResultDTO,
    RoomHeatLossResultDTO,
)
from HVAC.heatloss.validation.surface_edit_validator import SurfaceEditValidator

class HeatLossControllerV4:
    """
    Orchestrator-only controller.

    Forbidden responsibilities:
    • No effective height logic
    • No ACH logic
    • No ΔT logic
    • No manual FabricSurfaceInputDTO building
    • No ProjectState field peeking beyond lifecycle calls
    """

    def __init__(self, *, project_state: ProjectState) -> None:
        self._project = project_state
        self._validator = SurfaceEditValidator()
        self._overlay = None
    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def handle_overlay_commit(self, ctx, values) -> None:
        """
        Single entry point for ALL overlay commits.
        """

        # --------------------------------------------------
        # VALIDATION (pure)
        # --------------------------------------------------
        result = self._validator.validate(ctx, values, self._project)

        if not result.valid:
            self._overlay.show_validation(result)
            return

        # --------------------------------------------------
        # APPLY MUTATION
        # --------------------------------------------------
        self._apply_mutation(ctx, values)

        # --------------------------------------------------
        # LIFECYCLE
        # --------------------------------------------------
        self._project.mark_heatloss_dirty()

        # --------------------------------------------------
        # REFRESH
        # --------------------------------------------------
        self._main_window.refresh_all_adapters()


    def run(self, *, internal_design_temp_C: float) -> None:

        # --------------------------------------------------
        # Readiness
        # --------------------------------------------------
        readiness = self._project.evaluate_heatloss_readiness()
        if not readiness.is_ready:
            raise RuntimeError(
                "Heat-loss is not ready:\n"
                + "\n".join(f"- {r}" for r in readiness.blocking_reasons)
            )

        # --------------------------------------------------
        # Explicit invalidation
        # --------------------------------------------------
        self._project.mark_heatloss_dirty()

        # --------------------------------------------------
        # Build effective snapshot (single resolved truth)
        # --------------------------------------------------
        snapshot = build_effective_project_snapshot(
            project=self._project,
            internal_design_temp_C=float(internal_design_temp_C),
        )

        # --------------------------------------------------
        # Engines
        # --------------------------------------------------
        fabric_result = FabricHeatLossEngine.run(snapshot)

        ventilation_result = VentilationHeatLossEngine.run(
            room_snapshots=snapshot.rooms,
            external_design_temp_C=snapshot.external_design_temp_C,
        )

        # --------------------------------------------------
        # Aggregate authoritative totals
        # --------------------------------------------------
        qf_by_room_W = fabric_result.qf_by_room_W
        qv_by_room_W = ventilation_result.qv_by_room_W

        room_results: list[RoomHeatLossResultDTO] = []
        project_total_W = 0.0

        for room_snapshot in snapshot.rooms:
            rid = room_snapshot.room_id

            qf = float(qf_by_room_W.get(rid, 0.0))
            qv = float(qv_by_room_W.get(rid, 0.0))
            qt = qf + qv

            room_results.append(
                RoomHeatLossResultDTO(
                    room_id=rid,
                    q_fabric_W=qf,
                    q_ventilation_W=qv,
                    q_total_W=qt,
                )
            )

            project_total_W += qt

        result_dto = ProjectHeatLossResultDTO(
            project_id=snapshot.project_id,
            rooms=tuple(room_results),
            project_total_W=project_total_W,
        )

        # --------------------------------------------------
        # Atomic commit
        # --------------------------------------------------
        self._project.heatloss_results = {
            "result": result_dto,            # authoritative
            "fabric": fabric_result,         # engine detail
            "ventilation": ventilation_result,
        }

        self._project.mark_heatloss_valid()

    def _apply_mutation(self, ctx, values) -> None:
        ps = self._project

        room = ps.rooms.get(ctx.room_id)
        if room is None:
            return

        if ctx.kind == "surface":
            for s in room.fabric_elements:
                if s.surface_id == ctx.surface_id:
                    s.area_m2 = values["area_m2"]
                    s.u_value = values["u_value"]
                    return

        elif ctx.kind == "geometry":
            room.geometry.length_m = values["length_m"]
            room.geometry.width_m = values["width_m"]
            room.geometry.height_override_m = values["height_m"]

        elif ctx.kind == "ach":
            room.ach_override = values["ach"]