HVACgooee Bootstrap — Phase IV Adjacency System

Phase: IV
Objective: Stable multi-room topology model for heat-loss
Scope: Boundary segments + adjacency resolution
Status: Design freeze candidate

1. Core Concept

Rooms do not directly know their neighbors.

Instead the building is represented by boundary segments.

Each segment belongs to one room and may reference another.

This forms a graph of connected spaces.

Room A
 ├ segment 1 → external
 ├ segment 2 → external
 └ segment 3 → Room B

Room B
 └ segment 7 → Room A

This model avoids duplication and topology bugs.

2. Authoritative Model

Location:

HVAC/geometry/boundary_segment_v1.py
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class BoundarySegmentV1:

    segment_id: str
    owner_room_id: str

    geometry_ref: str
    length_m: float

    boundary_kind: str
    # "EXTERNAL"
    # "INTER_ROOM"
    # "ADIABATIC"

    adjacent_room_id: Optional[str] = None
3. Rules (Topology Invariants)

These must always hold.

Ownership
segment.owner_room_id must exist in ProjectState.rooms
Inter-room segments
boundary_kind == "INTER_ROOM"

must satisfy:

adjacent_room_id != None
adjacent_room_id != owner_room_id
External segments
boundary_kind == "EXTERNAL"

must satisfy:

adjacent_room_id == None
Adiabatic segments
boundary_kind == "ADIABATIC"

must satisfy:

adjacent_room_id == None
4. Storage in ProjectState

Add to:

HVAC/project/project_state.py
boundary_segments: dict[str, BoundarySegmentV1] = field(default_factory=dict)

Helper iterator:

def iter_boundary_segments_for_room(self, room_id: str):

    for seg in self.boundary_segments.values():
        if seg.owner_room_id == room_id:
            yield seg
5. Topology → Fabric Projection

Location:

HVAC/heatloss/fabric/topology_fabric_bridge.py

Purpose:

Convert boundary topology into temporary fabric surfaces.

Example:

for seg in project.iter_boundary_segments_for_room(room.room_id):

    if seg.boundary_kind != "EXTERNAL":
        continue

    area = seg.length_m * height

    rows.append(
        DevFabricRow(
            element_id=f"{room.room_id}-{seg.geometry_ref}",
            room_id=room.room_id,
            surface_class="external_wall",
            area_m2=area,
        )
    )

Floor and roof still come from polygon.

6. ΔT Resolution

ΔT must not be guessed inside the GUI.

Location:

HVAC/heatloss/resolution/adjacency_delta_t_resolver.py

Concept:

if boundary_kind == "EXTERNAL":
    dT = Ti - Te

elif boundary_kind == "INTER_ROOM":
    dT = Ti - Tadj

elif boundary_kind == "ADIABATIC":
    dT = 0

Where:

Ti   = owner room internal temp
Tadj = adjacent room internal temp
Te   = environment external temp
7. Future Internal Partition Surfaces

When boundary_kind == "INTER_ROOM" we may optionally generate surfaces:

surface_class = "internal_partition"

These usually have:

Q ≈ 0

but still useful for:

comfort calculations

dynamic models

acoustic modelling

8. Why This Model Is Stable

This avoids the common mistakes:

No duplicated walls

Bad model:

Room A wall
Room B wall

Good model:

BoundarySegment owned by A referencing B
No missing adjacency

Segment explicitly states adjacency.

Perimeter validation becomes simple

Room perimeter must equal:

Σ segment.length_m
9. Relationship to Graph Theory

This topology is equivalent to a graph.

Room → node
BoundarySegment → edge

Which means later you can easily run algorithms like:

shortest path
loop detection
network balancing
thermal propagation

The same abstraction is used in:

CAD kernels
fluid networks
hydronic systems
electrical circuits
10. Development Stages
Phase IV-A

Boundary segments introduced.

External walls only.

Phase IV-B

Inter-room adjacency enabled.

Phase IV-C

Topology validator.

Checks:

closed perimeter
duplicate edges
invalid adjacency
Phase IV-D

Full ΔT resolver integration.

11. Interaction with GUI

Geometry panel will eventually create segments like:

wall edge
→ external
→ internal
→ adiabatic

User chooses boundary type.

12. Example Result

Room A polygon:

4m x 3m

Segments:

A-1 external 4m
A-2 external 3m
A-3 internal → Room B
A-4 external 3m

Fabric projection:

external_wall surfaces
internal_partition surface
floor
roof
13. Why This Makes Multi-Room HL Easy

Once adjacency exists:

Room A Q
Room B Q

interactions become automatic.

For example:

Q_internal = U * A * (Ti_A - Ti_B)

No special logic required.

14. Current Immediate Next Step

Do not implement adjacency yet.

First stabilize:

worksheet
fabric projection
engine execution
GUI refresh

Then introduce topology validation.

If you'd like, I can also show you the five invariants that prevent 90% of adjacency bugs before they ever reach the solver.
