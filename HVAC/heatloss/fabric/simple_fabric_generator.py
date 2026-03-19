from __future__ import annotations

from HVAC.core.room_state import RoomStateV1


def generate_simple_fabric_elements(room: "RoomStateV1") -> None:
    """
    Populate default fabric elements from room geometry.

    Elements generated:
        • external_wall (one per boundary edge)
        • roof
        • floor
    """

    geom = room.geometry

    if geom.length_m is None or geom.width_m is None:
        return

    try:
        L = float(geom.length_m)
        W = float(geom.width_m)
    except Exception:
        return

    if L <= 0 or W <= 0:
        return

    # --------------------------------------------------
    # Geometry derivations
    # --------------------------------------------------

    floor_area = L * W

    height = geom.height_override_m
    if height is None:
        height = 2.4

    # Rectangle polygon
    polygon = [
        (0.0, 0.0),
        (L, 0.0),
        (L, W),
        (0.0, W),
    ]

    # --------------------------------------------------
    # Reset existing elements
    # --------------------------------------------------

    room.fabric_elements.clear()

    # --------------------------------------------------
    # External walls (one per edge)
    # --------------------------------------------------

    for i in range(len(polygon)):

        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]

        edge_length = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        wall_area = edge_length * height

        room.fabric_elements.append(
            FabricElementV1(
                element_class="external_wall",
                area_m2=wall_area,
                construction_id="DEFAULT_WALL",
                boundary_index=i,  # ← important future hook
            )
        )

    # --------------------------------------------------
    # Roof
    # --------------------------------------------------

    room.fabric_elements.append(
        FabricElementV1(
            element_class="roof",
            area_m2=floor_area,
            construction_id="DEFAULT_ROOF",
        )
    )

    # --------------------------------------------------
    # Floor
    # --------------------------------------------------

    room.fabric_elements.append(
        FabricElementV1(
            element_class="floor",
            area_m2=floor_area,
            construction_id="DEFAULT_FLOOR",
        )
    )