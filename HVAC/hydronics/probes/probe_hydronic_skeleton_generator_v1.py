# ======================================================================
# HVAC/hydronics/probes/probe_hydronic_skeleton_generator_v1.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.models.hydronic_skeleton_generator_v1 import (
    RoomLoadV1,
    generate_initial_hydronic_skeleton_v1,
)


def main() -> None:
    print()
    print("Hydronics H-M1 — skeleton generator probe")
    print()

    rooms = [
        RoomLoadV1(
            room_id="room-001",
            room_name="Kitchen",
            design_heat_loss_w=421.6,
        ),
        RoomLoadV1(
            room_id="room-002",
            room_name="Living Room",
            design_heat_loss_w=650.0,
        ),
    ]

    skeleton = generate_initial_hydronic_skeleton_v1(rooms)

    print(f"Skeleton ID:   {skeleton.skeleton_id}")
    print(f"Boiler ID:     {skeleton.boiler.boiler_id}")
    print(f"Boiler name:   {skeleton.boiler.name}")
    print(f"Terminals:     {len(skeleton.terminals)}")
    print(f"Supply legs:   {len(skeleton.supply_legs)}")
    print(f"Return legs:   {len(skeleton.return_legs)}")
    print(f"All legs:      {len(skeleton.all_legs())}")
    print()

    for terminal in skeleton.terminals.values():
        print(
            f"{terminal.terminal_id} | "
            f"{terminal.room_id} | "
            f"{terminal.room_name} | "
            f"{terminal.design_heat_loss_w:.1f} W"
        )

    print()

    for leg in skeleton.all_legs():
        print(
            f"{leg.leg_id} | "
            f"{leg.from_node_id} -> {leg.to_node_id} | "
            f"length={leg.length_m}"
        )

    assert len(skeleton.terminals) == 2
    assert len(skeleton.supply_legs) == 2
    assert len(skeleton.return_legs) == 2
    assert len(skeleton.all_legs()) == 4

    print()
    print("OK — hydronic skeleton generator probe passed.")
    print()


if __name__ == "__main__":
    main()
