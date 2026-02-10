# ======================================================================
# HVAC/hydronics/pipes/dp/pressure_drop_aggregator_v1.py
# ======================================================================

"""
HVACgooee — Pressure Drop Aggregator v1.1
----------------------------------------

Aggregates pressure drop along explicit hydronic paths.

Consumes:
    • SizedPipeSegmentV1            (pipe sizing results, Pa/m + velocity)
    • CommittedHydronicLeg          (authoritative topology)
    • CommittedLegGeometryV1        (ordered pipe + fitting segments)
    • Explicit path definitions     (path_id → ordered leg_ids)

Produces:
    • PressureDropPathV1            (Pa totals)

RULES
-----
• No sizing
• No balancing
• No topology inference
• Deterministic summation only
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from HVAC.hydronics.pipes.dto.sized_pipe_segment_v1 import SizedPipeSegmentV1
from HVAC.hydronics.committed.committed_hydronic_leg import CommittedHydronicLeg
from HVAC.hydronics.committed.committed_leg_geometry_v1 import CommittedLegGeometryV1
from HVAC.hydronics.pipes.dp.pressure_drop_path_v1 import PressureDropPathV1


RHO_WATER_KG_M3 = 1000.0


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def aggregate_pressure_drop_v1(
    *,
    sized_segments: Iterable[SizedPipeSegmentV1],
    committed_legs: Iterable[CommittedHydronicLeg],
    geometries: Iterable[CommittedLegGeometryV1],
    paths: Dict[str, List[str]],
) -> List[PressureDropPathV1]:
    """
    Aggregate pressure drop along explicit hydronic paths.
    """

    # --------------------------------------------------------------
    # Index inputs
    # --------------------------------------------------------------
    seg_by_segment_id: Dict[str, SizedPipeSegmentV1] = {
        s.segment_id: s for s in sized_segments
    }

    geom_by_leg: Dict[str, CommittedLegGeometryV1] = {
        g.leg_id: g for g in geometries
    }

    results: List[PressureDropPathV1] = []

    # --------------------------------------------------------------
    # Aggregate per path
    # --------------------------------------------------------------
    for path_id, leg_ids in paths.items():
        per_leg_dp: Dict[str, float] = {}
        total_dp = 0.0

        for leg_id in leg_ids:
            geometry = geom_by_leg.get(leg_id)
            if geometry is None:
                raise RuntimeError(
                    f"[ΔP] No geometry provided for leg_id '{leg_id}'."
                )

            dp_leg = 0.0

            for segment in geometry.segments:
                seg_result = seg_by_segment_id.get(segment.segment_id)
                if seg_result is None:
                    raise RuntimeError(
                        f"[ΔP] No sizing result for segment '{segment.segment_id}'."
                    )

                # ------------------------------
                # Pipe segment
                # ------------------------------
                if segment.kind == "pipe":
                    if segment.length_m <= 0.0:
                        raise RuntimeError(
                            f"[ΔP] Invalid length for pipe segment "
                            f"'{segment.segment_id}'."
                        )

                    dp_leg += (
                        seg_result.pressure_drop_Pa_per_m
                        * segment.length_m
                    )

                # ------------------------------
                # Fitting segment (K-based)
                # ------------------------------
                elif segment.kind == "fitting":
                    dp_leg += (
                        segment.k_value
                        * 0.5
                        * RHO_WATER_KG_M3
                        * seg_result.velocity_m_s ** 2
                    )

                else:
                    raise RuntimeError(
                        f"[ΔP] Unknown segment kind '{segment.kind}' "
                        f"for segment '{segment.segment_id}'."
                    )

            per_leg_dp[leg_id] = dp_leg
            total_dp += dp_leg

        results.append(
            PressureDropPathV1(
                path_id=path_id,
                leg_ids=list(leg_ids),
                total_dp_Pa=total_dp,
                per_leg_dp_Pa=per_leg_dp,
            )
        )

    return results
