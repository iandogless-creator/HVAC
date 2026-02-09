"""
default_construction_tree.py
----------------------------

HVACgooee — Default Construction Tree v1 (LOCKED)

Conservative, UK-centric starter tree.
Small by design. Extend later via version bump.
"""

from HVAC_legacy.constructions.construction_tree import (
    ConstructionTree,
    ConstructionSurfaceGroup,
    ConstructionFamily,
    ConstructionVariant,
)
from HVAC_legacy.constructions.construction_preset import SurfaceClass


def build_default_construction_tree() -> ConstructionTree:
    return ConstructionTree(
        surfaces={
            # --------------------------------------------------
            # EXTERNAL WALLS
            # --------------------------------------------------
            SurfaceClass.EXTERNAL_WALL: ConstructionSurfaceGroup(
                surface_class=SurfaceClass.EXTERNAL_WALL,
                families=[
                    ConstructionFamily(
                        name="Masonry",
                        variants=[
                            ConstructionVariant(
                                name="Solid brick (pre-1920)",
                                preset_ref="EXT_WALL_SOLID_BRICK_PRE1920",
                            ),
                            ConstructionVariant(
                                name="Cavity wall (unfilled)",
                                preset_ref="EXT_WALL_CAVITY_UNFILLED",
                            ),
                            ConstructionVariant(
                                name="Cavity wall (filled)",
                                preset_ref="EXT_WALL_CAVITY_FILLED",
                            ),
                        ],
                    ),
                    ConstructionFamily(
                        name="Timber frame",
                        variants=[
                            ConstructionVariant(
                                name="Timber frame (insulated)",
                                preset_ref="EXT_WALL_TIMBER_FRAME",
                            ),
                        ],
                    ),
                ],
            ),

            # --------------------------------------------------
            # ROOFS
            # --------------------------------------------------
            SurfaceClass.ROOF: ConstructionSurfaceGroup(
                surface_class=SurfaceClass.ROOF,
                families=[
                    ConstructionFamily(
                        name="Pitched",
                        variants=[
                            ConstructionVariant(
                                name="Pitched roof (insulated loft)",
                                preset_ref="ROOF_PITCHED_INSULATED",
                            ),
                        ],
                    ),
                    ConstructionFamily(
                        name="Flat",
                        variants=[
                            ConstructionVariant(
                                name="Flat roof (warm deck)",
                                preset_ref="ROOF_FLAT_WARM",
                            ),
                        ],
                    ),
                ],
            ),

            # --------------------------------------------------
            # FLOORS
            # --------------------------------------------------
            SurfaceClass.FLOOR: ConstructionSurfaceGroup(
                surface_class=SurfaceClass.FLOOR,
                families=[
                    ConstructionFamily(
                        name="Ground floor",
                        variants=[
                            ConstructionVariant(
                                name="Solid floor (uninsulated)",
                                preset_ref="FLOOR_SOLID_UNINSULATED",
                            ),
                            ConstructionVariant(
                                name="Solid floor (insulated)",
                                preset_ref="FLOOR_SOLID_INSULATED",
                            ),
                        ],
                    ),
                ],
            ),

            # --------------------------------------------------
            # WINDOWS / GLAZING
            # --------------------------------------------------
            SurfaceClass.WINDOW: ConstructionSurfaceGroup(
                surface_class=SurfaceClass.WINDOW,
                families=[
                    ConstructionFamily(
                        name="Glazing",
                        variants=[
                            ConstructionVariant(
                                name="Double glazing (older)",
                                preset_ref="WINDOW_DOUBLE_OLD",
                            ),
                            ConstructionVariant(
                                name="Double glazing (modern)",
                                preset_ref="WINDOW_DOUBLE_MODERN",
                            ),
                        ],
                    ),
                ],
            ),
        }
    )
