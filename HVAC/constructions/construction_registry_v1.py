raise RuntimeError(
    "LEGACY MODULE USED: construction_registry_v1.py\n"
    "This module is obsolete and must not be imported.\n"
    "Use registry_v2.py and PRESETS_V2 instead.\n"
    "Superseded: Construction Registry v2 Bootstrap — Jan 2026"
)

def build_default_construction_registry() -> ConstructionRegistry:
    construction = registry.get(surface.construction_id)

    U = construction.u_value
    Qf = U * surface.area_m2 * delta_t

    reg = ConstructionRegistry()

    reg.register(
        ConstructionDefinition(
            id="WALL_EXT_SOLID_BRICK",
            name="External wall – solid brick",
            u_value=2.10,
            source="CIBSE Guide A",
        )
    )

    reg.register(
        ConstructionDefinition(
            id="WALL_EXT_CAVITY_PIR_100",
            name="External wall – cavity + 100mm PIR",
            u_value=0.18,
            source="CIBSE Guide A / SAP",
        )
    )

    reg.register(
        ConstructionDefinition(
            id="WINDOW_DG_STD",
            name="Window – double glazed (standard)",
            u_value=1.40,
            source="SAP default",
        )
    )

    return reg
