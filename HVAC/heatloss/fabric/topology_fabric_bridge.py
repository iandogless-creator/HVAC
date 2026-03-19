# ======================================================================
# HVAC/heatloss/fabric/topology_fabric_bridge.py
# ======================================================================

from __future__ import annotations

from HVAC.core.fabric_element import FabricElementV1


def generate_fabric_from_boundaries(project_state, room):
    """
    Temporary Phase-IV bridge.

    Converts boundary segments into FabricElementV1 rows
    so the Heat-Loss worksheet can populate.

    Rules (DEV)
    -----------
    • EXTERNAL boundaries → external_wall
    • INTER_ROOM boundaries ignored (ΔT = 0)
    • Floor + roof derived from polygon area
    """

    g = room.geometry

    if not hasattr(project_state, "boundary_segments"):
        return

    height = getattr(g, "height_override_m", None)

    if height is None:
        height = getattr(g, "height_m", None)

    if height is None:
        return

    room.fabric_elements.clear()

    # --------------------------------------------------
    # External walls
    # --------------------------------------------------

    for seg in project_state.boundary_segments.values():

        if seg.owner_room_id != room.room_id:
            continue

        if seg.boundary_kind != "EXTERNAL":
            continue

        area = seg.length_m * height

        room.fabric_elements.append(
            FabricElementV1(
                element_class="external_wall",
                area_m2=area,
                construction_id="DEV-WALL",   # ← DEV placeholder
            )
        )

    # --------------------------------------------------
    # Floor + roof from polygon
    # --------------------------------------------------

    poly = getattr(g, "polygon", None)

    if poly and len(poly) >= 3:
        area = _polygon_area(poly)

        room.fabric_elements.append(
            FabricElementV1(
                element_class="floor",
                area_m2=area,
                construction_id="DEV-ROOF",
            )
        )

        room.fabric_elements.append(
            FabricElementV1(
                element_class="roof",
                area_m2=area,
                construction_id="DEV-ROOF",
            )
        )


# ----------------------------------------------------------------------
# Simple polygon area
# ----------------------------------------------------------------------

def _polygon_area(poly):

    area = 0.0
    n = len(poly)

    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += x1 * y2 - x2 * y1

    return abs(area) * 0.5