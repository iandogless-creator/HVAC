# ======================================================================
# HVAC/heatloss_v3/run_heatloss_v3.py
# ======================================================================
"""
Terminal runner for HVACgooee Heat-Loss Engine v3

Purpose
-------
Headless execution of HeatLossEngineV3 from the command line.

This file:
✔ Runs the v3 engine directly
✔ Uses ConstructionPresetRegistry
✔ Prints domain results
✔ No GUI
✔ No Qt
✔ No legacy engines
"""

from __future__ import annotations

from HVAC.heatloss.engines.heatloss_engine_v3 import (
    HeatLossEngineV3,
    RoomHeatLossInput,
    BoundaryHeatLossInput,
)

from HVAC.constructions.construction_preset_registry import (
    ConstructionPresetRegistry,
)

from HVAC.constructions.default_construction_presets_v2 import (
    DEFAULT_CONSTRUCTION_PRESETS_V2,
)

from HVAC.project_v3.project_models_v3 import SurfaceV3


# ----------------------------------------------------------------------
# Build demo input
# ----------------------------------------------------------------------

def build_demo_input() -> RoomHeatLossInput:
    registry = ConstructionPresetRegistry(
        DEFAULT_CONSTRUCTION_PRESETS_V2
    )

    wall_preset = registry.get("EXT_WALL_MODERN_INSULATED")

    boundary = BoundaryHeatLossInput(
        element_type="external_wall",
        area_m2=12.0,
        construction=wall_preset,
    )

    return RoomHeatLossInput(
        room_name="Bedsit",
        internal_temp_c=21.0,
        external_temp_c=-3.0,
        boundaries=[boundary],
        room_volume_m3=50.0,
        ventilation_ach=0.5,
        ventilation_method="ACH (v3)",
    )


# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------

def main() -> None:
    print("\n=== HVACgooee Heat-Loss Engine v3 (Terminal) ===\n")

    engine = HeatLossEngineV3()

    # Build single-room demo input
    inp = build_demo_input()

    # Execute engine
    result = engine.compute_room(inp)

    print(f"Room: {result.room_name}")
    print(f"  Fabric loss: {result.total_fabric_heat_loss_w:.1f} W")
    print(f"  Vent loss:   {result.ventilation_heat_loss_w:.1f} W")
    print(f"  Total loss:  {result.total_heat_loss_w:.1f} W")

    for b in result.boundaries:
        print(
            f"   • {b.element_type}: "
            f"{b.heat_loss_w:.1f} W "
            f"(U={b.u_value}, A={b.area_m2}, ΔT={b.delta_t_k})"
        )

    print("\n=== END ===\n")
if __name__ == "__main__":
    main()
