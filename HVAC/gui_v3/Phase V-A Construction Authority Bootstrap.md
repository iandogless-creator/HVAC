======================================================================
HVACgooee — Phase V-A Construction Authority Bootstrap
Timestamp: (auto-generate on paste)
Status: ACTIVE (authoritative starting point for constructions)
======================================================================
🎯 Objective

Introduce Construction Authority (U-values) into HVACgooee without breaking:

ProjectState authority model
GUI v3 observer pattern
existing heat-loss pipeline
🧠 Core Principle (NON-NEGOTIABLE)
U-value NEVER lives on a surface
U-value ALWAYS comes from a construction
🧱 Architecture Overview
ProjectState
    ├── rooms
    ├── boundary_segments
    ├── constructions   ← NEW
    └── heatloss_results

Surface (segment-derived row)
    → construction_id
    → resolved U-value via lookup
======================================================================
🧩 Phase V-A Scope (STRICT)
======================================================================
✔ Include
ConstructionV1 dataclass
ProjectState.constructions (dict)
Lookup: construction_id → U-value
HLP uses construction-derived U
Minimal default construction set
❌ Exclude (later phases)
layered constructions
material stacks
standards libraries
thermal bridges (ψ)
UI editing panel (Phase V-B)
======================================================================
🧱 1. ConstructionV1 (NEW)
======================================================================
# HVAC/core/construction_v1.py

from dataclasses import dataclass

@dataclass(slots=True)
class ConstructionV1:
    construction_id: str
    name: str
    u_value_W_m2K: float
======================================================================
🧱 2. ProjectState Integration
======================================================================

Add to:

# HVAC/project/project_state.py
self.constructions: dict[str, ConstructionV1] = {}
======================================================================
🧱 3. Default DEV Constructions (bootstrap)
======================================================================

Add in your bootstrap:

project.constructions = {
    "DEV-EXT-WALL": ConstructionV1("DEV-EXT-WALL", "External Wall", 0.28),
    "DEV-INT-WALL": ConstructionV1("DEV-INT-WALL", "Internal Wall", 1.50),
    "DEV-ROOF":     ConstructionV1("DEV-ROOF", "Roof", 0.18),
    "DEV-FLOOR":    ConstructionV1("DEV-FLOOR", "Floor", 0.22),
    "DEV-WINDOW":   ConstructionV1("DEV-WINDOW", "Window", 1.40),
}
======================================================================
🧱 4. Surface → Construction Binding
======================================================================

Ensure your fabric rows include:

construction_id: str
======================================================================
🧱 5. U-Value Resolution (CRITICAL)
======================================================================

In:

FabricFromSegmentsV1

Replace any direct U usage with:

construction = project.constructions.get(construction_id)

u_value = None
if construction:
    u_value = construction.u_value_W_m2K
======================================================================
🧱 6. HLP Behaviour (READ-ONLY)
======================================================================

U column:

Displays: resolved U-value
Editable: NO
Click: emits open_construction_requested(surface_id)
======================================================================
🧠 Invariants (LOCK THESE)
1. Surface NEVER stores U directly
2. Construction is single source of truth
3. HLP is display-only
4. Adapter resolves U (not panel)
5. Missing construction → row state ≠ GREEN
======================================================================
🧪 Expected Behaviour After Phase V-A
======================================================================
All rows show U from construction
Changing a construction updates all linked surfaces
Heat-loss results change accordingly
No UI editing yet
======================================================================
🚀 Next Phase (V-B Preview)
======================================================================

Construction Panel:

list constructions
create new
duplicate existing
assign to surface
======================================================================
🎯 Mental Model
======================================================================
Geometry → defines size
Topology → defines relationship
Construction → defines behaviour
ΔT → defines driving force

Q = U × A × ΔT
======================================================================
✅ You are ready to begin Phase V-A
======================================================================

If you want, next step I’d suggest:

👉 I walk you through exact integration into FabricFromSegmentsV1 + adapter (10–15 lines total change) so you don’t get drift.
