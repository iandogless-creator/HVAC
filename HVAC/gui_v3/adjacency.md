HVACgooee — Phase IV-B Adjacency Stabilisation Bootstrap
Timestamp: Friday 9 April 2026, 14:32 pm (UK)
Status: ACTIVE (debug + continuation)

Stabilise adjacency system (INTER_ROOM surfaces) across:

• Topology (BoundarySegmentV1)
• Row builder (row_builder_v1)
• Adapter (HeatLossPanelAdapter)
• UI (HeatLossPanelV3)

Focus:

✔ ΔT correctness (external vs internal vs adiabatic)
✔ Qf correctness (U × A × ΔT)
✔ Adjacency click → assignment → refresh
✔ No duplication between controller / adapter / builder

ProjectState
• authoritative data store
• owns rooms, environment, topology, results

BoundarySegmentV1
• segment_id
• owner_room_id
• length_m
• boundary_kind ∈ {EXTERNAL, INTER_ROOM, ADIABATIC}
• adjacent_room_id (REQUIRED for INTER_ROOM)

Row Builder (row_builder_v1)
• canonical source of rows + metas
• no UI logic
• no controller duplication

Adapter (HeatLossPanelAdapter)
• resolves Ti, Te
• resolves ΔT per row
• overlays results if available
• computes live fallback (Qf, Qv, Qt)

Panel (HeatLossPanelV3)
• pure display
• uses WorksheetRowMeta
• emits intent only

INTERNAL WALL DISAPPEARS
• occurs after geometry edit
• root cause:
→ topology not rebuilt OR mismatch lengths
ΔT CLICK DOES NOTHING
• clicking ΔT should trigger adjacency editor
• current state:
→ only Element column wired for adjacency
META BREAKAGE (FIXED PARTIALLY)
• error:
'dict' object has no attribute 'columns'
• cause:
→ metas not always WorksheetRowMeta
CONTROLLER ERROR
TypeError:
FabricHeatLossEngine.run() missing 'surfaces'
• mismatch between controller + engine contract
IMPLICIT ADJACENCY (TEMPORARY BEHAVIOUR)
• works with 2 rooms only
• must be replaced with explicit adjacent_room_id

2-room system:

Room A (21°C)
Room B (21°C)

Shared wall:

A_e2 ↔ B_e2

Expected:

ΔT_internal = 0
Qf_internal = 0

Test variation:

Room B → 18°C

Expected:

ΔT = 3K
Qf > 0

INTER_ROOM must always have adjacent_room_id
Adjacency must be symmetric:
A ↔ B
ΔT rules:
EXTERNAL → Ti - Te
INTER_ROOM → Ti - Tadj
ADIABATIC → 0
Row builder is single source of truth
Panel never calculates physics

• 4 segments per room (rectangle only)
• no segment splitting yet
• 1 adjacency per segment
• no corridor modelling yet

Stabilise ΔT resolution in adapter
Ensure row_builder returns proper WorksheetRowMeta
Fix adjacency click → editor trigger
Add topology rebuild on geometry change
Validate symmetry (A ↔ B)

User is debugging a live system where:

• architecture is largely correct
• issues are integration-level (not conceptual)
• prefers deterministic, engineering-grade behaviour
• wants minimal, surgical fixes — not rewrites

Focus responses on:

✔ root cause identification
✔ minimal patches
✔ architectural integrity
✔ no over-engineering
