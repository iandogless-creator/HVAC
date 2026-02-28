# ======================================================================
# HVACgooee — Heat-Loss Controller (V4 Orchestrator)
# Phase: II-A / II-B
# Status: CANONICAL — ORCHESTRATION ONLY
# ======================================================================

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from HVAC.project.project_state import ProjectState

# ----------------------------------------------------------------------
# Engines (pure, stateless)
# ----------------------------------------------------------------------
from HVAC.heatloss.engines.fabric_heatloss_engine import FabricHeatLossEngine
from HVAC.heatloss.engines.ventilation_heatloss_engine import VentilationHeatLossEngine

# ----------------------------------------------------------------------
# DTOs (physics inputs)
# ----------------------------------------------------------------------
from HVAC.heatloss.dto.fabric_inputs import FabricHeatLossInputDTO
from HVAC.heatloss.dto.vent_inputs import VentilationACHInputDTO
from HVAC.heatloss.dto.fabric_inputs import (
    FabricHeatLossInputDTO,
    FabricSurfaceInputDTO,
)

class HeatLossControllerV4:
    """
    Heat-Loss Orchestrator (V4)

    Responsibilities
    ----------------
    • Orchestrate Phase II-A (Fabric)
    • Orchestrate Phase II-B (Ventilation, ACH-only)
    • Enforce readiness
    • Commit results to ProjectState

    Explicitly forbidden
    --------------------
    • Physics
    • Defaults
    • GUI logic
    • State ownership
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, *, project_state: ProjectState) -> None:
        self._project = project_state

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Phase II-A — Fabric
    # ------------------------------------------------------------------
    def _run_fabric(self, *, ti_C: float) -> None:
        fabric_input = self._build_fabric_input(
            project=self._project,
            ti_C=ti_C,
        )
        result = FabricHeatLossEngine.run(fabric_input)
        self._project.set_fabric_heatloss_result(result)

    # ------------------------------------------------------------------
    # Phase II-B — Ventilation (ACH-only)
    # ------------------------------------------------------------------
    def _run_ventilation(self) -> None:
        vent_input = self._build_ventilation_input(
            project=self._project,
        )
        result = VentilationHeatLossEngine.run_ach_only(vent_input)
        self._project.set_ventilation_heatloss_result(result)

    # ------------------------------------------------------------------
    # Readiness enforcement
    # ------------------------------------------------------------------
    def _assert_ready(self) -> None:
        readiness = self._project.evaluate_heatloss_readiness()
        if not readiness.is_ready:
            raise RuntimeError(
                "Heat-loss is not ready:\n"
                + "\n".join(f"- {r}" for r in readiness.blocking_reasons)
            )
    # ------------------------------------------------------------------
    # Public entry point (CANONICAL)
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Phase II-C — Qt aggregation helper (controller-only)
    # ------------------------------------------------------------------
    @staticmethod
    def _aggregate_qt(
            *,
            room_ids: list[str],
            qf_by_room_W: dict[str, float],
            qv_by_room_W: dict[str, float],
    ) -> dict:
        qt_by_room_W: dict[str, float] = {}
        total_qt_W = 0.0

        for rid in room_ids:
            qf = float(qf_by_room_W.get(rid, 0.0))
            qv = float(qv_by_room_W.get(rid, 0.0))
            qt = qf + qv
            qt_by_room_W[rid] = qt
            total_qt_W += qt

        return {
            "qt_by_room_W": qt_by_room_W,
            "total_qt_W": total_qt_W,
        }

    # ------------------------------------------------------------------
    # Public entry point (CANONICAL)
    # ------------------------------------------------------------------
    def run(
            self,
            *,
            internal_design_temp_C: float,
            ach: float,
    ) -> None:
        """
        Authoritative execution entry point.

        Contract
        --------
        • Requires readiness
        • Invalidates previous results
        • Executes Fabric
        • Executes Ventilation (room-level)
        • Aggregates Qt (controller-only)
        • Commits container atomically
        • Marks heat-loss valid exactly once
        """

        # --------------------------------------------------
        # Phase I-C — Readiness
        # --------------------------------------------------
        self._assert_ready()

        # --------------------------------------------------
        # Phase I-B — Explicit invalidation
        # --------------------------------------------------
        self._project.mark_heatloss_dirty()

        # --------------------------------------------------
        # Phase II-A — Fabric
        # --------------------------------------------------
        fabric_input = self._build_fabric_input(
            project=self._project,
            ti_C=internal_design_temp_C,
        )
        fabric_result = FabricHeatLossEngine.run(fabric_input)

        # Expect fabric_result to contain qf_by_room_W + total_qf_W
        qf_by_room_W = dict(fabric_result.get("qf_by_room_W", {}))

        # --------------------------------------------------
        # Phase II-B — Ventilation (ACH-only) — controller implementation (for now)
        # --------------------------------------------------
        env = self._project.environment
        if env is None or env.external_design_temperature is None:
            raise RuntimeError("External design temperature not defined")

        delta_t = internal_design_temp_C - env.external_design_temperature

        room_ids = list(self._project.rooms.keys())
        qv_by_room_W: dict[str, float] = {}

        for room_id, room in self._project.rooms.items():
            volume = (
                    float(getattr(room.space, "floor_area_m2", 0.0))
                    * float(getattr(room.space, "height_m", 0.0))
            )
            qv_by_room_W[room_id] = 0.33 * float(ach) * float(volume) * float(delta_t)

        ventilation_result = {
            "qv_by_room_W": qv_by_room_W,
            "total_qv_W": sum(qv_by_room_W.values()),
        }

        # --------------------------------------------------
        # Phase II-C — Qt aggregation (controller-only)
        # --------------------------------------------------
        room_totals = self._aggregate_qt(
            room_ids=room_ids,
            qf_by_room_W=qf_by_room_W,
            qv_by_room_W=qv_by_room_W,
        )

        # --------------------------------------------------
        # Phase II-D — Atomic container commit (single write)
        # --------------------------------------------------
        container = {
            "fabric": fabric_result,
            "ventilation": ventilation_result,
            "room_totals": room_totals,
        }
        self._project.heatloss_results = container

        # --------------------------------------------------
        # Phase II-D — Explicit validity marking (once)
        # --------------------------------------------------
        self._project.mark_heatloss_valid()

    # ==================================================================
    # DTO builders (STRUCTURAL ONLY)
    # ==================================================================

    @staticmethod
    def _build_fabric_input(
            *,
            project: ProjectState,
            ti_C: float,
    ) -> FabricHeatLossInputDTO:
        # --------------------------------------------------
        # Environment
        # --------------------------------------------------
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

        # --------------------------------------------------
        # Fabric participants (declared intent only)
        # --------------------------------------------------
        resolved_surfaces = list(project.iter_fabric_surfaces())
        if not resolved_surfaces:
            raise RuntimeError("No fabric surfaces declared")

        surface_inputs: list[FabricSurfaceInputDTO] = []

        for s in resolved_surfaces:
            surface = s.surface

            # -----------------------------
            # Identity (fail loud)
            # -----------------------------
            sid = (
                    getattr(surface, "surface_id", None)
                    or getattr(surface, "id", None)
                    or getattr(surface, "name", None)
            )
            if not sid:
                raise RuntimeError(
                    "Fabric surface missing identifier: expected Surface.name "
                    "(or .id / .surface_id)"
                )

            rid = getattr(surface, "room_id", None) or getattr(s, "room_id", None)
            if not rid:
                raise RuntimeError(
                    f"Resolved fabric surface '{sid}' has no room_id. "
                    "Controller must populate FabricSurfaceInputDTO.room_id "
                    "without inference."
                )

            # -----------------------------
            # Classification
            # -----------------------------
            sclass = getattr(surface, "surface_class", None)
            if sclass is None:
                sclass = getattr(surface, "surface_type", None)

            surface_class_str = (
                sclass.value if hasattr(sclass, "value") else str(sclass)
            )

            # -----------------------------
            # Geometry
            # -----------------------------
            area_m2 = getattr(surface, "area_m2", None)
            if area_m2 is None:
                raise RuntimeError(f"Surface '{sid}' missing area_m2")

            surface_inputs.append(
                FabricSurfaceInputDTO(
                    surface_id=str(sid),
                    room_id=str(rid),
                    surface_class=surface_class_str,
                    area_m2=float(area_m2),
                    u_value_W_m2K=float(s.u_value_W_m2K),
                    delta_t_K=float(delta_t),
                )
            )

        # --------------------------------------------------
        # Final DTO (single return point)
        # --------------------------------------------------
        return FabricHeatLossInputDTO(
            surfaces=surface_inputs,
            internal_design_temp_C=float(ti_C),
            external_design_temp_C=float(te_C),
            project_id=project.project_id,
        )

    @staticmethod
    def _build_ventilation_input(
        *,
        project: ProjectState,
    ) -> VentilationACHInputDTO:
        """
        Phase II-B — ACH-only ventilation input.

        IMPLEMENT LATER.
        """
        raise NotImplementedError("Ventilation input builder not yet implemented")