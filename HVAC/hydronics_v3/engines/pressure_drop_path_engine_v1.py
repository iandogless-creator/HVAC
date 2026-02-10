# ======================================================================
# HVAC/hydronics_v3/engines/pressure_drop_path_engine_v1.py
# ======================================================================

from __future__ import annotations

from typing import List

from HVAC.hydronics_v3.dto.pressure_drop_path_dto import PressureDropPathDTO
from HVAC.hydronics_v3.dto.hydronic_topology_dto import HydronicTopologyDTO
from HVAC.hydronics_v3.models.hydronic_leg import HydronicLeg


class PressureDropPathEngineV1:
    """
    PressureDropPathEngineV1 (CANONICAL)

    PURPOSE
    -------
    Enumerates all boiler → terminal hydronic paths and
    aggregates their total pressure drop.

    RULES (LOCKED)
    --------------
    • Pure engine
    • DTO-in / DTO-out
    • No mutation
    • No sizing
    • No balancing
    • No inference
    • No GUI

    Physics assumptions:
    • Each PipeSegment already exposes its pressure drop (Pa)
    • This engine only sums
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def run(topology: HydronicTopologyDTO) -> List[PressureDropPathDTO]:
        """
        Build pressure-drop paths for all terminal legs.

        Args:
            topology: Declared hydronic topology

        Returns:
            List of PressureDropPathDTO (one per terminal leg)
        """
        topology.validate()

        paths: List[PressureDropPathDTO] = []

        for boiler_id in topology.boiler_leg_ids:
            boiler_leg = topology.get_leg(boiler_id)

            PressureDropPathEngineV1._walk(
                current_leg=boiler_leg,
                topology=topology,
                acc_legs=[],
                acc_length_m=0.0,
                acc_dp_pa=0.0,
                paths=paths,
            )

        return paths

    # ------------------------------------------------------------------
    # Recursive traversal
    # ------------------------------------------------------------------
    @staticmethod
    def _walk(
        *,
        current_leg: HydronicLeg,
        topology: HydronicTopologyDTO,
        acc_legs: List[str],
        acc_length_m: float,
        acc_dp_pa: float,
        paths: List[PressureDropPathDTO],
    ) -> None:
        """
        Depth-first traversal from boiler to terminal legs.
        """

        # Extend accumulators
        new_legs = acc_legs + [current_leg.leg_id]

        leg_length = current_leg.total_length_m()
        leg_dp = sum(
            seg.pressure_drop_pa for seg in current_leg.pipe_segments
        )

        new_length = acc_length_m + leg_length
        new_dp = acc_dp_pa + leg_dp

        # -------------------------------------------------
        # Leaf leg → emit path DTO
        # -------------------------------------------------
        if current_leg.is_leaf():
            path_id = " → ".join(new_legs)

            paths.append(
                PressureDropPathDTO(
                    path_id=path_id,
                    leg_ids=new_legs,
                    terminal_leg_id=current_leg.leg_id,
                    total_length_m=new_length,
                    total_pressure_drop_pa=new_dp,
                    design_qt_w=current_leg.design_qt_w,
                )
            )
            return

        # -------------------------------------------------
        # Branch leg → recurse
        # -------------------------------------------------
        for child in current_leg.child_legs:
            PressureDropPathEngineV1._walk(
                current_leg=child,
                topology=topology,
                acc_legs=new_legs,
                acc_length_m=new_length,
                acc_dp_pa=new_dp,
                paths=paths,
            )
