# ======================================================================
# HVAC/core/value_resolution.py
# ======================================================================

def _resolve(room_value, env_value):
    """
    Generic resolver used by all HVACgooee parameters.

    Returns
    -------
    (value, source)

    source:
        "room"
        "environment"
        None
    """

    if room_value is not None:
        return room_value, "room"

    if env_value is not None:
        return env_value, "environment"

    return None, None


def resolve_effective_height_m(project, room):

    env = project.environment

    return _resolve(
        getattr(room, "height_m", None),
        getattr(env, "default_room_height_m", None) if env else None,
    )


def resolve_effective_ach(project, room):

    env = project.environment

    return _resolve(
        getattr(room, "ach_override", None),   # ✅ FIX
        getattr(env, "default_ach", None) if env else None,
    )


# ----------------------------------------------------------------------
# Internal design temperature resolution
# ----------------------------------------------------------------------

def resolve_effective_internal_temp_C(project, room):

    env = project.environment

    return _resolve(
        getattr(room, "internal_temp_override_C", None),
        getattr(env, "default_internal_temp_C", None) if env else None,
    )