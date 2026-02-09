# ======================================================================
# HVAC/hydronics/committed/geometry_autogen_v1.py
# ======================================================================

"""
HVACgooee — Auto Geometry Generator v1
-------------------------------------

Generates default leg geometry including:
• Pipe runs
• Auto-inserted tee fittings at branches
• Auto-inserted lockshield valves at terminals

RULES
-----
• Deterministic
• One tee per branch point
• One lockshield per terminal leg
• No reducers (v1)
• No balancing logic (v1)
• Replaceable by explicit geometry
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from HVAC_legacy.hydronics.committed.committed_hydronic_leg import (
    CommittedHydronicLeg,
)
from HVAC_legacy.hydronics.committed.committed_leg_geometry_v1 import (
    CommittedLegGeometryV1,
)
from HVAC_legacy.hydronics.committed.committed_pipe_segment_v1 import (
    CommittedPipeSegmentV1,
)
from HVAC_legacy.hydronics.physics.fittings_k_library_v1 import (
    get_fitting_k_value,
)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def autogenerate_leg_geometry_v1(
    *,
    committed_legs: Iterable[CommittedHydronicLeg],
) -> List[CommittedLegGeometryV1]:
    """
    Generate default geometry including tees and lockshields.
    """

    legs = list(committed_legs)

    # --------------------------------------------------------------
    # Build parent → children map
    # --------------------------------------------------------------
    children_by_parent: Dict[str, List[str]] = {}

    for leg in legs:
        if leg.parent_leg_id is not None:
            children_by_parent.setdefault(
                leg.parent_leg_id, []
            ).append(leg.leg_id)

    geometries: List[CommittedLegGeometryV1] = []

    # --------------------------------------------------------------
    # Generate geometry per leg
    # --------------------------------------------------------------
    for leg in legs:
        if leg.nominal_length_m <= 0.0:
            raise RuntimeError(
                f"[GEOM] Invalid nominal length for leg '{leg.leg_id}'."
            )

        segments: List[CommittedPipeSegmentV1] = []

        # ----------------------------------------------------------
        # Main pipe run
        # ----------------------------------------------------------
        segments.append(
            CommittedPipeSegmentV1(
                segment_id=f"{leg.leg_id}-AUTO-P1",
                leg_id=leg.leg_id,
                kind="pipe",
                length_m=leg.nominal_length_m,
                label="Auto-generated pipe run",
            )
        )

        child_legs = children_by_parent.get(leg.leg_id, [])

        # ----------------------------------------------------------
        # Tee fitting (branch point)
        # ----------------------------------------------------------
        if len(child_legs) > 1:
            segments.append(
                CommittedPipeSegmentV1(
                    segment_id=f"{leg.leg_id}-AUTO-TEE",
                    leg_id=leg.leg_id,
                    kind="fitting",
                    k_value=get_fitting_k_value(
                        "TEE_BRANCH_EQUAL"
                    ),
                    label="Auto-generated branch tee",
                )
            )

        # ----------------------------------------------------------
        # Lockshield valve (terminal leg)
        # ----------------------------------------------------------
        if len(child_legs) == 0:
            segments.append(
                CommittedPipeSegmentV1(
                    segment_id=f"{leg.leg_id}-AUTO-LS",
                    leg_id=leg.leg_id,
                    kind="fitting",
                    k_value=get_fitting_k_value(
                        "LOCKSHIELD_VALVE_STD"
                    ),
                    label="Auto-generated lockshield valve",
                )
            )

        geometries.append(
            CommittedLegGeometryV1(
                leg_id=leg.leg_id,
                segments=segments,
            )
        )

    return geometries
