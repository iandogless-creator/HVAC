# HVAC/project_v3/resolve_geometry.py

def resolve_height(
    *,
    surface_height: float | None,
    room_height: float | None,
    environment_height: float,
) -> float:
    """
    Resolve effective height with explicit precedence.

    surface override > room override > environment default
    """
    if surface_height is not None:
        return surface_height
    if room_height is not None:
        return room_height
    return environment_height
