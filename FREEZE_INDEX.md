# ======================================================================
# HVACgooee — Repository FREEZE INDEX
# ======================================================================
#
# This document defines all frozen subsystems, their authority,
# and their current lifecycle phase.
#
# It is NOT a README.
# It is NOT user documentation.
#
# It is the architectural spine of the repository.
#
# Location: repository root
# Status: CANONICAL
# ======================================================================


## Meaning of "Frozen"

A frozen subsystem:

• Has a locked public contract
• Has a fixed authority boundary
• Must not be refactored without an explicit new bootstrap
• May be *used*, but not *restructured*

Refactors that change **public shape, authority, or data ownership**
constitute restructuring.

Bug fixes are allowed.
Architectural changes are not.

---

## Authority Topology (Global)

HVACgooee follows a strict execution topology:

GUI → Adapter → Controller → Runner → Result
Result → ProjectState (commit only)

Observer / editor side paths are allowed only as intent:

Panel → Adapter → Context / Controller → ProjectState

Reverse authority flows are forbidden.

---

## 🧠 Project Core — v3
**Status:** FROZEN + EXTENDED COMPATIBILITY
**Path:** `HVAC/project/`

### Authority
- Defines what a project *is*
- Owns ProjectState lifecycle
- Owns edit vs calculation mode
- Owns identity
- Owns runtime project state containers

### Current ProjectState Authority Containers
- rooms
- environment
- boundary_segments
- constructions
- surface_construction_map
- heat-loss readiness / results containers
- emitters
- room_opening_schedules

### Compatibility Containers
- openings_by_surface remains as a legacy compatibility container because existing fabric code still calls `get_openings_for_surface(...)`.

### Rules
- No GUI imports
- No physics
- No hidden heuristics
- Factories assemble intent only
- State mutation only through explicit controller / adapter intent paths
- ProjectState may own runtime authority containers but must not calculate

---

## 🔥 Heat-Loss Engine — v1
**Status:** FROZEN
**Path:** `HVAC/heatloss/`, `HVAC/heatloss_v3/`

### Authority
- Fabric + ventilation + ΔT → heat loss
- Deterministic, testable physics
- Pure execution via runners

### Rules
- No GUI imports
- No persistence
- No ProjectState mutation
- No validation inference
- Explicit inputs, explicit outputs only

---

## 🧱 Heat-Loss Topology / Fabric Bridge
**Status:** ACTIVE-STABLE
**Path:** `HVAC/topology/`, `HVAC/heatloss/fabric/`

### Authority
- BoundarySegmentV1 defines room boundary intent
- Topology resolver creates rectangular v1 room segments
- FabricFromSegmentsV1 projects topology into fabric rows
- row_builder_v1 is the canonical row projection path for HLP

### Rules
- Boundary kind determines ΔT route:
  - EXTERNAL → Ti - Te
  - INTER_ROOM → Ti - adjacent Ti
  - ADIABATIC → 0
- U-value never lives on a surface
- U-value resolves through ConstructionV1
- Fabric rows are projection, not authority

### Current Status
- Rectangular v1 segment topology is active
- Horizontal / vertical adjacency are supported at v1 level
- Surface-level construction assignment is active through `surface_construction_map`
- Opening schedules exist but do not yet alter HLP fabric physics

---

## 🧱 Constructions & Fabric
**Status:** FROZEN + ACTIVE ASSIGNMENT PATH
**Path:** `HVAC/core/construction_v1.py`, construction/dev defaults, fabric projection paths

### Authority
- ConstructionV1 owns U-value
- Construction assignment may be per-surface through ProjectState.surface_construction_map
- Fabric / row projection resolves U-value from construction_id

### Rules
- GUI edits emit intent only
- ConstructionWizard writes assignment intent into ProjectState
- Surfaces never store U-values
- Results immutable once committed
- No area or ΔT responsibility in ConstructionV1

### Current DEV Defaults
- DEV-EXT-WALL — External Wall — U 0.26
- DEV-INT-WALL — Internal Wall — U 1.50
- DEV-FLOOR — Floor — U 0.18
- DEV-ROOF — Roof / Ceiling — U 0.16
- DEV-WINDOW — Window / Door — U 1.60
- DEV-EXT-DOOR — External Door — U 1.60
- DEV-INT-DOOR — Internal Door — U 1.80

---

## 🪟 Wall Wizard / Opening Schedule — v1
**Status:** ACTIVE-STABLE RUNTIME AUTHORITY
**Path:** `HVAC/gui_v3/wizards/wall_wizard.py`, `HVAC/gui_v3/adapters/wall_wizard_adapter.py`, `HVAC/core/opening_schedule_v1.py`

### Authority
- WallWizardDialog is UI only
- WallWizardAdapter routes intent
- ProjectState.room_opening_schedules owns runtime opening schedules
- RoomOpeningScheduleV1 owns room-level opening schedule items
- OpeningScheduleItemV1 owns profile, size, quantity, construction_id

### Current Scope
- Clicking any external wall opens a room-level external openings schedule
- Gross external wall area is total external wall area for the selected room
- Openings are room-level in v1, not placed on individual wall segments
- Schedule supports:
  - add opening
  - grouped display
  - remove selected grouped line
  - clear all
  - close/reopen reload during runtime

### Current Profiles
- Small Window — 0.60 × 0.90 m
- Standard Window — 1.20 × 1.20 m
- Large Window — 1.80 × 1.20 m
- External Door — 0.90 × 2.10 m
- Internal Door — 0.90 × 2.10 m

### Rules
- No HLP Qf mutation yet
- No project-file persistence yet
- No CAD placement
- No wall-position inference
- Opening U-values resolve by construction_id
- OpeningScheduleItemV1 never stores U-value

### Next Heat-Loss Opening Work
NOT CURRENTLY ACTIVE:
- Persist room_opening_schedules to project files
- Project openings into HLP rows
- Net external wall area affects fabric Qf
- Window / door rows become heat-loss rows

---

## 📊 Heat-Loss Overrides — v1
**Status:** FROZEN
**Owner:** `HeatLossStateV1`

### Definition
Overrides represent user intent, not results.

### Rules
- Overrides may shadow derived inputs
- Overrides are sparse and optional
- Clearing overrides removes intent
- Any override change invalidates results
- Overrides never store calculated values

### Forbidden
❌ results overwriting overrides
❌ implicit override creation
❌ override-driven mutation

---

## 🖥️ GUI v3 — Core Shell
**Status:** ACTIVE-STABLE
**Path:** `HVAC/gui_v3/`

### Frozen Components
- Adapter → DTO → Panel architecture
- Observer-only panel access
- Panel emits intent only
- saveState / restoreState persistence
- No GUI direct ProjectState mutation

### Active Components
- Hydronics restart
- Wall Wizard runtime opening editor
- Construction assignment path
- Overlay editing path
- Visual focus / selection refinement

---

## 📋 GUI v3 — Panels

### Heat-Loss Panel
**Status:** ACTIVE-STABLE / PARKED
**Role:** Worksheet + observer substrate
**Authority:** NONE

### Current Capabilities
- Displays topology/fabric-derived rows
- Displays construction U-values
- U column focuses construction / assignment path
- ΔT column routes adjacency edit intent
- Element column opens Wall Wizard for wall rows
- Surface focus routes to Construction Panel / UVP
- HLP physics is not yet affected by room opening schedules

### Rules
- Never commits results
- Never mutates ProjectState
- Never performs authoritative physics
- May show live fallback values only as projection

---

### Wall Wizard
**Status:** ACTIVE-STABLE / PARKED AFTER F1-C**
**Authority:** NONE

- Dialog is UI only
- Emits add/remove/clear intent
- Does not mutate ProjectState directly
- Does not calculate heat loss
- Does not persist project data

---

### Construction Panel / UVP
**Status:** ACTIVE-STABLE**

### Authority
- No authority in panels
- Construction assignment intent routed through adapter/wizard
- Construction focus is shared with HLP/UVP

### Current Capabilities
- Selected surface target is tracked
- Construction selector assigns ConstructionV1 to selected surface
- U-value display/focus path active
- UVP fallback resolver must pass surface_id, not BoundarySegmentV1 object

---

### Hydronics Schematic Panel
**Status:** FROZEN (Phase D) + NEXT ACTIVE TARGET
**Path:** `HVAC/gui_v3/panels/hydronics_schematic_panel.py`, `HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py`

### Authority
- Read-only
- DTO-driven
- No authority
- No selection coupling
- No physics

### Current Behaviour
- Adapter reads hydronics topology snapshot if present
- Panel renders schematic DTO nodes, edges, labels
- Missing hydronics topology is a valid empty state

### Next Hydronics GUI Work
- Hydronics Phase H-A: room emitter demand observer
- Read ProjectState rooms
- Read available heat-loss demand if available
- Show emitter requirement placeholder
- No pipe sizing yet

---

### Environment Panel
**Status:** STABLE

### Project Panel
**Status:** STABLE

---

## 🚰 Hydronics Engine — v3
**Status:** FROZEN ENGINE / ACTIVE GUI OBSERVER RESTART
**Path:** `HVAC/hydronics/`, `HVAC/hydronics_v3/`

### Engine Authority
- Flow
- Pressure
- Balancing
- Pumps
- Network topology + physics only

### Engine Rules
- No GUI imports
- No heat-loss imports
- DTOs only across boundaries
- No persistence
- No heuristics

### Current Restart Boundary
Heat-loss topology may inform a hydronics skeleton, but only as a room/emitter demand graph.

### Allowed Inference
- rooms
- emitter candidate per room
- room heat-load demand when available
- simple schematic nodes

### Forbidden Inference
- actual pipe routes
- pump head
- pipe lengths
- valve positions
- manifold position
- boiler position unless explicitly selected
- index circuit based on room adjacency alone

### Next Active Phase
Hydronics H-A — Generate/read room emitter demand observer.

---

## 🔥 Heat-Loss → Hydronics Boundary
**Status:** ACTIVE DESIGN BOUNDARY**

### Rule
Hydronics may consume heat-loss results but must not import heat-loss engine internals.

### Allowed
- committed room heat load result
- DTO / ProjectState result snapshot
- room_id-based demand lookup

### Forbidden
- hydronics running heat-loss calculations
- hydronics importing heat-loss engine physics
- hydronics mutating heat-loss inputs
- hydronics inferring hidden fabric physics

### v1 Interpretation
Heat-loss topology gives hydronics a room demand graph, not a hydraulic pipe network.

---

## ♨️ Emitters — v1
**Status:** ACTIVE MODEL**
**Path:** `HVAC/hydronics/emitter_v1.py`

### Authority
- Represents radiator / emitter intent
- Belongs to ProjectState
- Does not perform hydronic calculation
- Does not know about GUI

### Current Fields
- emitter_id
- room_id
- name
- emitter_type
- design_output_W
- flow_temp_C
- return_temp_C
- room_temp_C
- notes

### Next Work
- One emitter candidate per heated room
- design_output_W = committed room heat-loss Qt when available
- status if no heat-loss result exists

---

## 🎨 GUI Theme & Accent System
**Status:** ACTIVE
**Path:** `HVAC/gui_v3/common/`

### Rules
- Accent colours only
- No semantic meaning
- Installation-level preference
- Blue intentionally de-emphasised

---

## 🚫 Explicit Global Non-Goals

The following are forbidden everywhere:

• GUI performing calculations
• Panels mutating ProjectState
• Implicit recalculation
• Hidden authority
• Cross-engine imports
• GUI heuristics
• Hydronics calculating heat loss
• Heat-loss topology pretending to be pipe routing
• Openings changing HLP physics before explicit projection phase

Violations are architectural bugs.

---

## 🔐 Runner Purity Contract
**Status:** FROZEN
**Scope:** `*_runner_v*`

### Rules
- Pure functions
- No mutation of inputs
- No caching
- No persistence
- No GUI access
- Explicit return values only

This enables:
- reproducibility
- testing
- parallelism
- future acceleration

---

## 🆔 Identity & Addressing — v1
**Status:** FROZEN + EXTENDED**

### Identifiers
- `room_id` — stable project identifier
- `element_id` — stable within room
- `surface_id` — stable projected surface / segment identifier
- `segment_id` — boundary topology identity
- `construction_id` — construction authority identity
- `profile_id` — opening profile identity
- `emitter_id` — hydronic emitter identity

### Rules
- Overrides and results use identity
- Geometry may change shape, IDs persist
- Execution relies on identity, not GUI selection
- Room-level openings use room_id
- v1 openings do not require wall placement identity

---

## Phase H — Heat-Loss Execution & GUI Observer Substrate
**Status:** FROZEN / PARKED**

### Scope
- ProjectState D.2 authority
- HeatLossStateV1 + overrides
- HeatLossRunnerV3 pure execution
- HeatLossControllerV4
- GUI v3 Heat-Loss worksheet observer-only substrate

### Current Position
Heat-loss side is stable enough to pause.
Opening schedules exist as runtime authority but are not yet projected into HLP physics.

---

## Phase H-A — Hydronics Restart
**Status:** NEXT ACTIVE WORK**

### Scope
- Hydronics schematic panel remains read-only
- Start room emitter demand observer
- Use rooms and available heat-loss demand
- Show per-room emitter requirement status

### Non-Goals
- pipe sizing
- pump sizing
- pressure loss
- balancing
- plant selection
- pipe route inference

---

## 📍 Next Planned Work (NOT FROZEN)

Immediate:

• Hydronics H-A — room emitter demand observer
• Inspect ProjectState emitter container
• Create ProjectState → room emitter demand DTO
• Show emitter requirement status without pipe physics

Deferred:

• Persist room_opening_schedules
• Project openings into HLP rows
• Net wall Qf from room-level opening schedule
• HLP window/door read-only rows
• Hydronic pipe sizing
• Hydronic pump/head calculation

---

## Change Policy

Any change that violates a freeze must:

• be deliberate
• be documented
• update this file
• justify architectural impact

Silent violations are bugs.

---

**Authoritative owner:** Ian Allison
**Repository:** HVACgooee
**Licence:** GPL-v3 (core)

Status: **CANONICAL**

# ======================================================================
# END OF DOCUMENT
# ======================================================================
