# HVACgooee — H-S7 Leg / Primary Subleg Refactor

Status: PLANNED
Branch: phase-hydronics-h-a

## Purpose

Restore the original hydronic topology meaning:

- A leg comes from the common main.
- A leg does not directly contain rooms.
- A leg feeds one or more sublegs.
- A subleg, whatever its origin, contains rooms.

## Current transitional implementation

Current DEV code allows:

```python
HydronicLegV1.route_room_ids

This is transitional only.

It currently represents what should become the leg’s primary room-carrying subleg.

Target model
HydronicTopologyV1
    heat_source_room_id
    legs: list[HydronicLegV1]

HydronicLegV1
    leg_id
    label
    sublegs: list[HydronicSublegV1]

HydronicSublegV1
    subleg_id
    label
    origin_id / origin_room_id
    route_room_ids
    index_room_id
    sublegs
Terminology

Leg:
Primary outlet from the common main. Has no rooms directly.

Primary subleg:
Default/main room-carrying route fed by a leg.

Branch subleg:
Additional room-carrying route created by a split/tee.

Terminal:
Last downstream room/node on a subleg.

Index:
Mutable selected/calculated index room/emitter. May be terminal, but is not the same concept as terminal.

Migration idea

For existing transitional topology:

leg.route_room_ids

create:

HydronicSublegV1(
    subleg_id=f"{leg.leg_id}-primary-subleg",
    label="Primary subleg",
    origin_room_id="",
    route_room_ids=leg.route_room_ids,
    index_room_id=leg.index_room_id,
)

Then clear/remove direct leg route use later.

Consumer changes needed
DevHydronicTopologyBuilderV1 should create leg + primary subleg.
HydronicTopologyEditorV1 should edit subleg route_room_ids.
TopologyArrangerProjectionV1 should project primary subleg rows.
Proportioning schematic projection should consume subleg route rows.
Basic PS should eventually consume topology sublegs, not room list order.
Rule

Do not use room list order as hydronic route authority.
Do not treat leg.route_room_ids as final architecture.


