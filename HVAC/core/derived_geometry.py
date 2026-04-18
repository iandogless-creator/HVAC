from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------
# Floor area
# ---------------------------------------------------------------------

def resolve_floor_area_m2(room) -> Optional[float]:
    g = getattr(room, "geometry", None)
    if g is None:
        return None

    if g.length_m is None or g.width_m is None:
        return None

    return float(g.length_m) * float(g.width_m)


# ---------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------

def resolve_volume_m3(room, project_state) -> Optional[float]:
    area = resolve_floor_area_m2(room)
    if area is None:
        return None

    g = getattr(room, "geometry", None)
    h = getattr(g, "height_m", None)

    if h is None:
        env = getattr(project_state, "environment", None)
        h = getattr(env, "default_room_height_m", None) if env else None

    if h is None:
        return None

    return area * float(h)