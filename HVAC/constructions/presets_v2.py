from __future__ import annotations

from HVAC.constructions.construction_preset import (
    ConstructionPreset,
    SurfaceClass,
)

PRESETS_V2: list[ConstructionPreset] = [

    ConstructionPreset(
        ref="WALL_STD",
        name="Standard External Wall",
        surface_class=SurfaceClass.EXTERNAL_WALL,
        u_value=0.30,
        preset_type="reference",
    ),

    ConstructionPreset(
        ref="ROOF_STD",
        name="Standard Roof",
        surface_class=SurfaceClass.ROOF,
        u_value=0.18,
        preset_type="reference",
    ),

    ConstructionPreset(
        ref="FLOOR_STD",
        name="Ground Floor Slab",
        surface_class=SurfaceClass.FLOOR,
        u_value=0.22,
        preset_type="reference",
    ),

    ConstructionPreset(
        ref="WINDOW_STD",
        name="Double Glazed Window",
        surface_class=SurfaceClass.WINDOW,
        u_value=1.40,
        preset_type="reference",
    ),

    ConstructionPreset(
        ref="WALL_INT",
        name="Standard Internal Wall",
        surface_class=SurfaceClass.INTERNAL_WALL,
        u_value=1.50,
        preset_type="reference",
    ),

ConstructionPreset(
    ref="DOOR_INT",
    name="Standard Internal Door",
    surface_class=SurfaceClass.INTERNAL_DOOR,
    u_value=2.50,
    preset_type="reference",
),
]