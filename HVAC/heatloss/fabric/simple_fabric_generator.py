# ======================================================================
# HVAC/heatloss/fabric/simple_fabric_generator.py
# ======================================================================

from __future__ import annotations

from HVAC.core.room_state import RoomStateV1


# ======================================================================
# generate_simple_fabric_elements (LEGACY — DISABLED)
# ======================================================================

def generate_simple_fabric_elements(room: "RoomStateV1") -> None:
    """
    ⚠️ LEGACY FABRIC GENERATOR — DISABLED

    This function previously populated FabricElementV1 objects directly
    onto `room.fabric_elements`.

    It is now superseded by:

        TopologyResolverV1
            → FabricFromSegmentsV1.build_rows_for_room()

    Architecture (LOCKED)
    ---------------------
    • Fabric is derived from topology, not generated locally
    • room.fabric_elements MUST contain FabricSurfaceRowV1 only
    • This function MUST NOT mutate ProjectState

    Status
    ------
    Retained for reference during transition only.
    """

    # ------------------------------------------------------------------
    # HARD DISABLE (do nothing)
    # ------------------------------------------------------------------
    return