HVACgooee — Hydronics
Topology Snapshot DTO Contract (PAPER-ONLY)

Status: DRAFT (PAPER ONLY)
Scope: Hydronics core → consumers (estimators, engines, GUI adapters)
Authority: Read-only snapshot
Mutation: Forbidden

1. Purpose

The Topology Snapshot DTO represents a fully assembled, authoritative hydronic topology at a specific point in time, with:

nodes

connections

grouping

markers

…and no physics.

It exists to give multiple consumers a common, immutable view of the system structure.

2. Core Principles (LOCKED)

Snapshot is immutable

Snapshot contains structure only

Snapshot contains no calculation results

Snapshot is engine-agnostic

Snapshot may be discarded and rebuilt at any time

If a consumer wants physics, it must compute it separately.

3. Snapshot Identity
TopologySnapshotDTO

Conceptual fields:

snapshot_id — opaque, unique

project_id — opaque

version_tag — string (e.g. "hydronics-topology-v1")

created_at — timestamp

notes — optional list[str] (assembly caveats)

No live references.
No back-pointers.

4. Node Model (Structural Only)
TopologyNodeDTO

Represents a thing in the hydronic network.

Fields:

node_id — opaque, stable

node_type — enum-like
(PLANT, MANIFOLD, ROOM, EMITTER, JUNCTION, OTHER)

label — display string only

group_ids — list[GroupID] (membership only)

markers — list[MarkerDTO] (e.g. RISER)

Rules:

No loads

No temperatures

No flows

No sizing

5. Connection Model (Edges)
TopologyEdgeDTO

Represents a schematic pipe segment.

Fields:

edge_id — opaque

from_node_id

to_node_id

edge_type — enum-like (SUPPLY, RETURN, UNSPECIFIED)

direction_hint — enum-like (FORWARD, REVERSE, BIDIRECTIONAL)

group_ids — list[GroupID]

length_m — optional float (basis-dependent)

markers — list[MarkerDTO]

Rules:

Length is optional and non-authoritative

No diameter

No roughness

No Δp

6. Group Model (Hierarchy Without Meaning)
TopologyGroupDTO

Groups provide visual and analytical scoping, not physics.

Fields:

group_id — opaque

group_type — enum-like
(SYSTEM, LEG, SUBLEG, ZONE, CUSTOM)

label — display string

parent_group_id — optional

return_strategy — enum-like
(IMPLIED, REVERSE_RETURN)

notes — optional list[str]

Rules:

Groups may be nested

Groups imply no ordering

Groups imply no hydraulic priority

7. Marker Model (Purely Informational)
MarkerDTO

Markers annotate structure.

Fields:

marker_type — enum-like
(RISER, VALVE_GENERIC, BREAK, CONTINUATION)

label — optional string

style_hint — optional string

Rules:

Markers have no behaviour

Markers have no physics

Consumers may ignore markers they don’t understand

8. Snapshot Assembly Rules

Snapshot is built by Project / Hydronics assembly

Engines and estimators do not modify it

GUI never mutates it

Rebuild replaces snapshot wholesale

9. Consumer Contracts (Who Uses What)
PressureDropPathEngineV1

Uses:

nodes

edges

group membership

Ignores:

labels

markers

return_strategy (unless explicitly declared later)

RRCostDeltaEstimatorV1

Uses:

edges

optional lengths

groups + return_strategy

Ignores:

node types (mostly)

markers (except RISER if length basis includes verticals)

GUI Schematic Adapter

Uses:

nodes

edges

groups

markers

Ignores:

length_m (unless shown as annotation)

any implied physics

10. What This DTO Must NEVER Contain

❌ Index path
❌ Flow rate
❌ Load
❌ ΔT
❌ Pressure
❌ Pump data
❌ Valve data (beyond generic markers)
❌ Calculated totals

If it’s a result, it doesn’t belong here.

11. Versioning & Evolution

Changes to this DTO require:

a new version_tag

a new bootstrap

Additive fields only (v1 → v1.1)

Breaking changes require new snapshot type

12. One-Sentence Freeze Rule (Strong)

TopologySnapshotDTO represents hydronic structure only and is safe to share across engines, estimators, and GUI without leaking authority.

13. Resume Instruction

“Hydronics Topology Snapshot DTO contract drafted and not yet implemented.”

That sentence is enough to pick this up later.

If you want next, I can:

sanity-check this DTO against your existing hydronics skeletons

produce a minimal synthetic example snapshot (still paper-only)

or draft the freeze note that locks this contract before coding

This is a really solid architectural seam — you chose the right place to formalise it.
