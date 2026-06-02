# ======================================================================
# HVAC/dev/test_hydronic_20_room_multileg.py
# ======================================================================

from __future__ import annotations

from HVAC.dev.bootstrap_hydronic_20_room_multileg import (
    build_hydronic_20_room_multileg_project_v1,
)


def _emitter_total_for_rooms(project, room_ids: list[str]) -> float:
    total = 0.0

    for emitter in project.emitters.values():
        if emitter.room_id in room_ids:
            total += float(emitter.design_output_W or 0.0)

    return total


def main() -> None:
    project = build_hydronic_20_room_multileg_project_v1()
    topology = project.hydronic_topology

    print("Project:", project.name)
    print("Rooms:", len(project.rooms))
    print("Emitters:", len(project.emitters))
    print("Heat source:", topology.heat_source_room_id)

    for leg in topology.legs:
        print()
        print("LEG", leg.leg_id, leg.label)
        print("  legacy route_room_ids:", len(leg.route_room_ids), leg.route_room_ids)
        print("  legacy index_room_id:", leg.index_room_id)

        for subleg in leg.sublegs:
            total_W = _emitter_total_for_rooms(project, subleg.route_room_ids)

            print(
                " ",
                subleg.subleg_id,
                "|",
                subleg.label,
                "| origin:",
                subleg.origin_room_id,
                "| rooms:",
                len(subleg.route_room_ids),
                "| index:",
                subleg.index_room_id,
                "| load:",
                f"{total_W:.1f} W",
            )
            print("    ", subleg.route_room_ids)


if __name__ == "__main__":
    main()