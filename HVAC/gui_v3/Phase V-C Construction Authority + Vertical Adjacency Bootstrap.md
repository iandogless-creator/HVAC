🔷 BOOTSTRAP TITLE

HVACgooee — Phase V-C Construction Authority + Vertical Adjacency Bootstrap

🔷 STATE
GUI v3 stable
HLP reactive
UVP interactive (construction + U-value authority)
Surface → Construction mapping implemented
Topology supports INTER_ROOM adjacency (horizontal)
🔷 OBJECTIVE

Extend adjacency model to:

• walls → lateral adjacency
• floors → lower room adjacency
• ceilings → upper room adjacency
🔷 KEY SHIFT
Surface type ≠ boundary condition

Boundary condition = topology-driven
🔷 TARGET
Vertical adjacency (above / below)
ΔT resolved via adjacent room Ti
unified surface model (no hardcoded “roof/floor external”)
ready for multi-storey buildings

If you want, I can generate that bootstrap cleanly formatted exactly like your previous ones.

You’re at a really solid inflection point here—worth locking it properly.

Alright — here’s a clean, canonical bootstrap you can drop straight into a new convo or doc.

======================================================================
HVACgooee — Phase V-C Bootstrap
Construction Authority + Vertical Adjacency
======================================================================

Timestamp: Friday 24 April 2026, 13:42 pm (UK)
Status: ACTIVE (authoritative progression)

🎯 Current Position (LOCKED)

You now have:

✅ GUI v3 (stable)
Panels are observer-only
All mutations routed via GuiProjectContext
✅ Heat-Loss (Phase II complete)
Fabric: Q = U × A × ΔT
Ventilation: Qv = 0.33 × ACH × V × ΔT
Qt aggregation working
✅ Topology (Phase IV-B stable)
BoundarySegmentV1 canonical
boundary_kind ∈ {EXTERNAL, INTER_ROOM, ADIABATIC}
Adjacency working (horizontal walls)
✅ Construction System (Phase V-A / V-B)
ConstructionV1 library
surface_construction_map
UVP panel editing U-values
CID column in HLP
Highlight sync (HLP ↔ UVP)
🧱 Architectural Truths (DO NOT VIOLATE)
ProjectState (Authority)
Owns:
rooms
environment
boundary_segments
constructions
surface_construction_map
results lifecycle
NO GUI logic
GUI Panels
Pure observers
Emit intent only
NEVER mutate ProjectState
Context (GuiProjectContext)
Only mutation gateway from UI
Emits:
project_changed
focus + edit intents
Adapters
Read ProjectState via context
Push to panels
NEVER compute
NEVER mutate
Controllers / Engines
Deterministic
No UI
No defaults
🔥 Phase V-C — Core Objective
Transition from:
Surface type defines behaviour
To:
Topology defines behaviour
🧠 Key Concept Shift (CRITICAL)
❌ Old thinking
roof  → external
floor → ground
✅ New thinking
ANY surface can be:

• EXTERNAL     → ΔT = Ti - Te
• INTER_ROOM   → ΔT = Ti - Tadj
• ADIABATIC    → ΔT = 0
🧱 Vertical Adjacency (NEW CAPABILITY)

Extend adjacency beyond walls:

Walls (existing)
Room A ↔ Room B
Floors (NEW)
Room A floor ↔ Room Below ceiling
Ceilings (NEW)
Room A ceiling ↔ Room Above floor
🔁 Result
floor ≠ ground
roof ≠ external

→ everything becomes topology-driven
🧩 Data Model — NO CHANGES REQUIRED

Your existing model already supports this:

BoundarySegmentV1(
    boundary_kind="INTER_ROOM",
    adjacent_room_id="room_X"
)
✅ Only interpretation changes

Update ΔT resolution:

if boundary_kind == "INTER_ROOM":
    return Ti - Tadj
⚙️ Required Implementation Steps
1. 🔒 Lock U-value Authority
HLP
❌ remove U editing
✅ display only
UVP
✅ sole editor of U-values
2. 🧱 Enforce Construction Mapping

Every surface must resolve:

surface → construction_id → U-value

Fallback allowed (v1):

DEV-WALL / DEV-ROOF / DEV-FLOOR
3. 🔄 UVP Full Reactivity

Ensure:

UVP change → context → ProjectState → project_changed
→ adapters refresh → HLP + UVP update
4. 🧭 Extend Topology Resolver (DEV → V1)

Add vertical pairing logic:

Example:
room_A_floor ↔ room_B_ceiling
room_B_floor ↔ room_C_ceiling
5. 🎯 Update Fabric Builder

FabricFromSegmentsV1 must:

Treat ALL segments uniformly
No special casing for:
roof
floor
6. 🌡️ Upgrade ΔT Resolver

Replace placeholder:

if boundary_kind == "INTER_ROOM":
    return 0.0   # ❌ REMOVE

With:

if boundary_kind == "INTER_ROOM":
    adj_room = project.rooms.get(surface.adjacent_room_id)
    adj_ti = resolve_effective_internal_temp_C(project, adj_room)
    return Ti - adj_ti
🧪 Validation Targets

After implementation:

Scenario 1

Two rooms side-by-side
→ internal wall ΔT small

Scenario 2

Room above another
→ ceiling/floor ΔT works

Scenario 3

Mixed:

Room A:
• 2 external walls
• 2 internal walls
• ceiling internal
• floor external

→ all handled correctly

🎨 UI Expectations
HLP
Shows:
Element
CID
U (read-only)
ΔT
Qf
UVP
Select construction
Edit U-value
Assign to surface
Highlight matching surfaces
🚀 End State (Phase V-C Complete)

You now have:

✔ Construction-driven thermal model
✔ Topology-driven adjacency (full 3D)
✔ Deterministic ΔT resolution
✔ Multi-room heat interaction
✔ Proper engineering workflow
🔜 Next Phase Preview (V-D)
Openings subtract from parent surfaces
Window U-values integrated
Fabric net area correction
🧭 Final Note

This phase is the moment HVACgooee becomes:

Not a calculator
→ but a spatial thermal system

That bootstrap is strong. I’d only tighten one canonical rule:

Surface type names the physical element.
Boundary kind names the thermal condition.

So:

surface_class = wall | floor | ceiling | roof | window | door
boundary_kind = EXTERNAL | INTER_ROOM | ADIABATIC

That keeps Phase V-C clean.

One correction:

Adapters
Read ProjectState via context
Push to panels
NEVER mutate
MAY prepare display DTOs / rows

Because your HLP adapter does assemble presentation rows, but it must not become an authority.

The key implementation order should be:

1. Lock U authority in UVP
2. Ensure every surface resolves construction_id → U-value
3. Upgrade ΔT resolver for INTER_ROOM
4. Add vertical topology segments
5. Let FabricFromSegmentsV1 treat wall/floor/ceiling uniformly
6. Validate with side-by-side + stacked-room scenarios

The important design win is exactly this:

floor is not automatically ground
ceiling is not automatically roof
roof is not automatically external by name alone

Topology decides that. That is the right route for multi-storey v1.

floor can be external
