#======================================================================
#HVAC/hydronics_v3/engines/hydronic_index_path_engine_v1.py
#======================================================================

from __future__ import annotations

from typing import Dict, List

from HVAC.hydronics_v3.dto.hydronic_topology_dto import HydronicTopologyDTO
from HVAC.hydronics_v3.dto.pressure_drop_path_dto import PressureDropPathDTO
from HVAC.hydronics_v3.dto.index_path_result_dto import IndexPathResultDTO


class HydronicIndexPathEngineV1:
    """
    HydronicIndexPathEngineV1 (CANONICAL)

    PURPOSE
    -------
    Identifies the index (critical) hydronic path based on
    total pressure drop.

    INPUT
    -----
    • HydronicTopologyDTO

    OUTPUT
    ------
    • IndexPathResultDTO

    RULES (LOCKED)
    --------------
    • No mutation of topology
    • No sizing
    • No balancing
    • No GUI
    • No inference beyond declared topology
    """

    @staticmethod
    def run(
        topology: HydronicTopologyDTO,
        pressure_drop_by_leg_pa: Dict[str, float],
    ) -> IndexPathResultDTO:
        """
        Parameters
        ----------
        topology:
            Declared hydronic topology.

        pressure_drop_by_leg_pa:
            Mapping of leg_id → pressure drop (Pa),
            produced by a prior pressure-drop engine.

        Returns
        -------
        IndexPathResultDTO
        """
        topology.validate()

        # ------------------------------------------------------------
        # Enumerate terminal paths
        # ------------------------------------------------------------
        paths: Dict[str, PressureDropPathDTO] = {}

        for leaf in topology.leaf_legs():
            leg_ids = HydronicIndexPathEngineV1._build_path_to_root(
                topology,
                leaf.leg_id,
            )

            total_dp = sum(
                pressure_drop_by_leg_pa.get(leg_id, 0.0)
                for leg_id in leg_ids
            )

            path_id = f"path::{leaf.leg_id}"

            paths[path_id] = PressureDropPathDTO(
                path_id=path_id,
                leg_ids=leg_ids,
                total_pressure_drop_pa=float(total_dp),
                terminal_leg_id=leaf.leg_id,
            )

        if not paths:
            raise ValueError("No terminal paths found in hydronic topology.")

        # ------------------------------------------------------------
        # Identify index path (max Δp)
        # ------------------------------------------------------------
        index_path = max(
            paths.values(),
            key=lambda p: p.total_pressure_drop_pa,
        )

        return IndexPathResultDTO(
            index_path_id=index_path.path_id,
            paths=paths,
            index_pressure_drop_pa=index_path.total_pressure_drop_pa,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_path_to_root(
        topology: HydronicTopologyDTO,
        start_leg_id: str,
    ) -> List[str]:
        """
        Walks from a terminal leg to the root (boiler),
        returning ordered leg_ids from root → terminal.
        """
        path: List[str] = []
        current_id = start_leg_id

        while current_id is not None:
            path.append(current_id)
            leg = topology.get_leg(current_id)
            current_id = leg.parent_leg_id

        path.reverse()
        return path
