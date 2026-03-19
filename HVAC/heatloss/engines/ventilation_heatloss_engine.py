# ======================================================================
# HVAC/heatloss/engines/ventilation_heatloss_engine.py
# ======================================================================

from __future__ import annotations
from typing import Iterable, Dict
from dataclasses import dataclass

from HVAC.heatloss.dto.effective_room_snapshot import (
    EffectiveRoomSnapshotDTO,
)


class VentilationHeatLossEngine:
    """
    Pure ACH-based ventilation heat-loss engine.

    Rules
    -----
    • No defaults
    • No ProjectState access
    • No resolution logic
    • No GUI logic
    • Pure physics only
    """

    # ------------------------------------------------------------------
    # Result DTO (authoritative engine output)
    # ------------------------------------------------------------------
    @dataclass(frozen=True, slots=True)
    class VentilationHeatLossResultDTO:
        project_id: str
        external_design_temp_C: float
        qv_by_room_W: Dict[str, float]
        total_qv_W: float

    # ------------------------------------------------------------------
    # Engine entry point
    # ------------------------------------------------------------------
    @staticmethod
    def run(
        *,
        room_snapshots: Iterable[EffectiveRoomSnapshotDTO],
        external_design_temp_C: float,
    ) -> "VentilationHeatLossEngine.VentilationHeatLossResultDTO":

        qv_by_room_W: dict[str, float] = {}
        total_qv_W = 0.0

        project_id: str | None = None

        for snapshot in room_snapshots:

            # Capture project_id once (snapshots are authoritative)
            if project_id is None:
                project_id = snapshot.project_id

            delta_t = (
                snapshot.internal_design_temp_C
                - external_design_temp_C
            )

            if delta_t <= 0.0:
                raise RuntimeError(
                    f"Invalid ΔT for room '{snapshot.room_id}'"
                )

            qv = (
                0.33
                * snapshot.ach
                * snapshot.volume_m3
                * delta_t
            )

            qv_by_room_W[snapshot.room_id] = qv
            total_qv_W += qv

        if project_id is None:
            raise RuntimeError("No room snapshots supplied")

        return VentilationHeatLossEngine.VentilationHeatLossResultDTO(
            project_id=project_id,
            external_design_temp_C=float(external_design_temp_C),
            qv_by_room_W=qv_by_room_W,
            total_qv_W=total_qv_W,
        )