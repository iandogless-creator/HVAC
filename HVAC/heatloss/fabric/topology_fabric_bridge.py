# ======================================================================
# HVAC/heatloss/fabric/topology_fabric_bridge.py
# ======================================================================

from __future__ import annotations


# ======================================================================
# generate_fabric_from_boundaries (LEGACY — DISABLED)
# ======================================================================

def generate_fabric_from_boundaries(project_state, room):
    """
    ⚠️ LEGACY TOPOLOGY → FABRIC BRIDGE — DISABLED

    This function previously converted boundary segments into
    FabricElementV1 objects and wrote them directly into
    `room.fabric_elements`.

    It is now fully replaced by:

        TopologyResolverV1
            → FabricFromSegmentsV1.build_rows_for_room()

    Architecture (LOCKED)
    ---------------------
    • Topology is authoritative for boundaries
    • Fabric rows are derived via FabricFromSegmentsV1
    • room.fabric_elements MUST contain FabricSurfaceRowV1 only
    • This function MUST NOT mutate ProjectState

    Status
    ------
    Retained for reference during transition only.
    """

    # ------------------------------------------------------------------
    # HARD DISABLE (no mutation, no generation)
    # ------------------------------------------------------------------
    return


# ----------------------------------------------------------------------
# _polygon_area (LEGACY — retained for reference only)
# ----------------------------------------------------------------------

def _polygon_area(poly):
    """
    ⚠️ LEGACY helper — no longer used in active pipeline.
    """

    area = 0.0
    n = len(poly)

    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += x1 * y2 - x2 * y1

    return abs(area) * 0.5