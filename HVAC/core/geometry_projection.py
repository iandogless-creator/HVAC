def compute_room_geometry_projection(room, env):

    geom = room.geometry

    if geom.length_m is None or geom.width_m is None:
        return None

    height = geom.height_override_m or env.default_room_height_m

    floor_area = geom.length_m * geom.width_m
    volume = floor_area * height

    if geom.external_wall_length_m is not None:
        gross_ext_wall_area = geom.external_wall_length_m * height
    else:
        gross_ext_wall_area = None

    return {
        "floor_area_m2": floor_area,
        "volume_m3": volume,
        "gross_ext_wall_area_m2": gross_ext_wall_area,
        "height_m": height,
    }