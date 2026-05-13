# ======================================================================
# HVAC/hydronics/pipes/pipe_run_intent_builder_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.models.hydronic_skeleton_v1 import HydronicSkeletonV1
from HVAC.hydronics.pipes.pipe_run_intent_v1 import PipeRunIntentV1


def build_pipe_run_intents_from_skeleton_v1(
    skeleton: HydronicSkeletonV1,
) -> list[PipeRunIntentV1]:
    """
    Build pipe-run intent placeholders from a hydronic skeleton.

    Authority
    ---------
    • Reads HydronicSkeletonV1 only
    • Does not mutate skeleton or ProjectState
    • Does not size pipes
    • Does not calculate pressure loss
    """

    rows: list[PipeRunIntentV1] = []

    for leg in skeleton.supply_legs.values():
        rows.append(
            PipeRunIntentV1(
                pipe_run_id=f"pipe_{leg.leg_id}",
                leg_id=leg.leg_id,
                from_node_id=leg.from_node_id,
                to_node_id=leg.to_node_id,
                circuit_type="supply",
                length_m=leg.length_m,
                notes="Auto pipe intent from hydronic skeleton supply leg",
            )
        )

    for leg in skeleton.return_legs.values():
        rows.append(
            PipeRunIntentV1(
                pipe_run_id=f"pipe_{leg.leg_id}",
                leg_id=leg.leg_id,
                from_node_id=leg.from_node_id,
                to_node_id=leg.to_node_id,
                circuit_type="return",
                length_m=leg.length_m,
                notes="Auto pipe intent from hydronic skeleton return leg",
            )
        )

    return rows
