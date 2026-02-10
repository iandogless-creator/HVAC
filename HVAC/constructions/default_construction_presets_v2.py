"""
default_construction_presets_v2.py
----------------------------------

HVACgooee — Default Construction Presets (v2, v3-compatible)

Conservative, orthodox, steady-state effective U-values.
"""

from HVAC.constructions.construction_preset import (
    ConstructionPreset,
    SurfaceClass,
)


DEFAULT_CONSTRUCTION_PRESETS_V2 = [

    # ------------------------
    # External Walls
    # ------------------------
    ConstructionPreset(
        ref="EXT_WALL_SOLID_LEGACY",
        name="Solid masonry wall (uninsulated)",
        surface_class=SurfaceClass.EXTERNAL_WALL,
        u_value=2.1,
        preset_type="reference",
    ),
    ConstructionPreset(
        ref="EXT_WALL_CAVITY_PART_FILL",
        name="Cavity wall (partial fill)",
        surface_class=SurfaceClass.EXTERNAL_WALL,
        u_value=0.6,
        preset_type="reference",
    ),
    ConstructionPreset(
        ref="EXT_WALL_MODERN_INSULATED",
        name="Modern insulated external wall",
        surface_class=SurfaceClass.EXTERNAL_WALL,
        u_value=0.18,
        preset_type="reference",
    ),

    # ------------------------
    # Internal Walls
    # ------------------------
    ConstructionPreset(
        ref="INT_WALL_STANDARD",
        name="Standard internal partition",
        surface_class=SurfaceClass.INTERNAL_WALL,
        u_value=1.5,
        preset_type="reference",
    ),
    ConstructionPreset(
        ref="INT_WALL_ADIABATIC",
        name="Internal wall (adiabatic)",
        surface_class=SurfaceClass.INTERNAL_WALL,
        u_value=0.0,
        preset_type="reference",
    ),

    # ------------------------
    # Roofs
    # ------------------------
    ConstructionPreset(
        ref="ROOF_UNINSULATED",
        name="Uninsulated roof",
        surface_class=SurfaceClass.ROOF,
        u_value=2.3,
        preset_type="reference",
    ),
    ConstructionPreset(
        ref="ROOF_MODERN_INSULATION",
        name="Modern insulated roof",
        surface_class=SurfaceClass.ROOF,
        u_value=0.18,
        preset_type="reference",
    ),

    # ------------------------
    # Floors
    # ------------------------
    ConstructionPreset(
        ref="FLOOR_SOLID_UNINSULATED",
        name="Uninsulated solid floor",
        surface_class=SurfaceClass.FLOOR,
        u_value=0.7,
        preset_type="reference",
    ),
    ConstructionPreset(
        ref="FLOOR_SOLID_INSULATED",
        name="Insulated solid floor",
        surface_class=SurfaceClass.FLOOR,
        u_value=0.25,
        preset_type="reference",
    ),

    # ------------------------
    # Windows
    # ------------------------
    ConstructionPreset(
        ref="WINDOW_SINGLE_LEGACY",
        name="Single glazing (legacy)",
        surface_class=SurfaceClass.WINDOW,
        u_value=5.6,
        preset_type="reference",
    ),
    ConstructionPreset(
        ref="WINDOW_DOUBLE_LEGACY",
        name="Double glazing (legacy)",
        surface_class=SurfaceClass.WINDOW,
        u_value=2.8,
        preset_type="reference",
    ),
]
