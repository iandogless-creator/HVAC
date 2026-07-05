# HVACgooee — Repository FREEZE INDEX

Status: CANONICAL  
Owner: Ian Allison  
Repository: HVACgooee  
Licence: GPL-v3 core  
Last updated: 2026-07-05  
Current active area: Hydronics Phase H — proportioning / return-arrangement evidence

This document defines the frozen subsystems, their authority, and their current lifecycle phase.

It is not a README.

It is the architectural spine of the repository.

---

## Meaning of “Frozen”

A frozen subsystem:

- Has a locked public contract.
- Has a fixed authority boundary.
- Must not be restructured without an explicit new bootstrap or freeze update.
- May be used, extended, and bug-fixed inside its authority boundary.

Refactors that change public shape, authority, or data ownership constitute restructuring.

Bug fixes are allowed.

Silent architectural changes are not.

---

## Authority Topology — Global

HVACgooee follows a strict execution topology:

```text
GUI → Adapter → Controller → Runner → Result
Result → ProjectState only through explicit commit
```

Observer / editor side paths are allowed only as intent:

```text
Panel → Adapter → Context / Controller → ProjectState
```

Reverse authority flows are forbidden.

### Global non-negotiables

- GUI does not execute physics.
- Panels do not own engineering state.
- Adapters build projections and forward intent.
- Controllers own readiness and commit policy.
- Runners are pure computation.
- ProjectState is the sole authoritative data model.

Hydronics Phase H currently contains some adapter / panel persistence and commit wiring while the Hydronics controller boundary is still maturing. This is documented transition debt, not a permanent authority change.

---

## Project Core — v3

**Status:** FROZEN + EXTENDED COMPATIBILITY  
**Path:** `HVAC/project/`

### Authority

Project Core defines what a project is.

It owns:

- ProjectState lifecycle
- edit vs calculation mode
- identity
- runtime project state containers
- committed result containers
- persisted engineering intent

### Current ProjectState authority containers

- rooms
- environment
- boundary_segments
- constructions
- surface_construction_map
- heat-loss readiness / result containers
- emitters
- room_opening_schedules
- hydronic topology
- hydronic local K intent
- hydronic return-arrangement intent
- hydronic proportioned basis snapshot

### Rules

- No GUI imports.
- No physics.
- No hidden heuristics.
- No silent engineering repair.
- Factories assemble intent only.
- ProjectState may own runtime authority containers but must not calculate.

---

## Heat-Loss Engine — v1 / v3

**Status:** FROZEN / ACTIVE-STABLE  
**Path:** `HVAC/heatloss/`, `HVAC/heatloss_v3/`

### Authority

- Fabric + ventilation + ΔT → heat loss.
- Deterministic physics.
- Pure execution through runners.

### Rules

- No GUI imports.
- No persistence.
- No ProjectState mutation.
- No validation inference.
- Explicit inputs and explicit outputs only.

---

## Heat-Loss Topology / Fabric Bridge

**Status:** ACTIVE-STABLE  
**Path:** `HVAC/topology/`, `HVAC/heatloss/fabric/`

### Authority

- `BoundarySegmentV1` defines room boundary intent.
- Topology resolver creates rectangular v1 room segments.
- Fabric projection converts topology into heat-loss worksheet rows.
- `row_builder_v1` is the canonical row projection path for HLP.

### Rules

Boundary kind determines ΔT route:

- `EXTERNAL` → `Ti - Te`
- `INTER_ROOM` → `Ti - adjacent Ti`
- `ADIABATIC` → `0`

U-value never lives on a surface.

U-value resolves through `ConstructionV1`.

Fabric rows are projection, not authority.

### Current status

- Rectangular v1 segment topology is active.
- Horizontal and vertical adjacency are supported at v1 level.
- Surface-level construction assignment is active through `surface_construction_map`.
- Opening schedules exist but do not yet alter HLP fabric physics.

---

## Constructions & Fabric

**Status:** FROZEN + ACTIVE ASSIGNMENT PATH  
**Path:** `HVAC/core/construction_v1.py`, construction defaults, fabric projection paths

### Authority

- `ConstructionV1` owns U-value.
- Construction assignment may be per-surface through `ProjectState.surface_construction_map`.
- Fabric / row projection resolves U-value from `construction_id`.

### Rules

- GUI edits emit intent only.
- Construction wizard writes assignment intent through approved intent paths.
- Surfaces never store U-values.
- Results are immutable once committed.
- No area or ΔT responsibility in `ConstructionV1`.

---

## Wall Wizard / Opening Schedule — v1

**Status:** ACTIVE-STABLE / PARKED  
**Path:** `HVAC/gui_v3/wizards/wall_wizard.py`, `HVAC/gui_v3/adapters/wall_wizard_adapter.py`, `HVAC/core/opening_schedule_v1.py`

### Authority

- WallWizardDialog is UI only.
- WallWizardAdapter routes intent.
- `ProjectState.room_opening_schedules` owns runtime opening schedules.
- `RoomOpeningScheduleV1` owns room-level opening schedule items.
- `OpeningScheduleItemV1` owns profile, size, quantity, and construction_id.

### Current scope

- Clicking any external wall opens a room-level external openings schedule.
- Gross external wall area is total external wall area for the selected room.
- Openings are room-level in v1, not placed on individual wall segments.
- Schedule supports add, grouped display, remove selected grouped line, clear all, and close / reopen reload during runtime.

### Rules

- No HLP Qf mutation yet.
- No project-file persistence yet unless explicitly added in a later phase.
- No CAD placement.
- No wall-position inference.
- Opening U-values resolve by `construction_id`.
- `OpeningScheduleItemV1` never stores U-value.

### Next Heat-Loss opening work

Not currently active:

- persist `room_opening_schedules` to project files
- project openings into HLP rows
- net external wall area affects fabric Qf
- window / door rows become heat-loss rows

---

## Heat-Loss Overrides — v1

**Status:** FROZEN  
**Owner:** `HeatLossStateV1`

### Definition

Overrides represent user intent, not results.

### Rules

- Overrides may shadow derived inputs.
- Overrides are sparse and optional.
- Clearing overrides removes intent.
- Any override change invalidates results.
- Overrides never store calculated values.

### Forbidden

- results overwriting overrides
- implicit override creation
- override-driven mutation
- calculated results becoming user overrides

---

## GUI v3 — Core Shell

**Status:** ACTIVE-STABLE  
**Path:** `HVAC/gui_v3/`

### Frozen components

- Adapter → DTO → Panel architecture.
- Observer-only panel access.
- Panel emits intent only.
- `saveState` / `restoreState` persistence.
- No GUI direct ProjectState mutation.
- No GUI direct physics execution.

### Active components

- Hydronics Phase H proportioning evidence.
- Wall Wizard runtime opening editor.
- Construction assignment path.
- Overlay editing path.
- Visual focus / selection refinement.

---

## GUI v3 — Panels

### Heat-Loss Panel

**Status:** ACTIVE-STABLE / PARKED  
**Role:** worksheet + observer substrate  
**Authority:** none

Current capabilities:

- displays topology / fabric-derived rows
- displays construction U-values
- U column focuses construction / assignment path
- ΔT column routes adjacency edit intent
- Element column opens Wall Wizard for wall rows
- surface focus routes to Construction Panel / UVP
- HLP physics is not yet affected by room opening schedules

Rules:

- never commits results
- never mutates ProjectState
- never performs authoritative physics
- may show live fallback values only as projection

### Wall Wizard

**Status:** ACTIVE-STABLE / PARKED  
**Authority:** none

- Dialog is UI only.
- Emits add / remove / clear intent.
- Does not mutate ProjectState directly.
- Does not calculate heat loss.
- Does not persist project data.

### Construction Panel / UVP

**Status:** ACTIVE-STABLE  
**Authority:** none in panels

Current capabilities:

- selected surface target is tracked
- construction selector assigns `ConstructionV1` to selected surface through intent path
- U-value display / focus path active
- UVP fallback resolver must pass `surface_id`, not `BoundarySegmentV1` object

### Hydronics Schematic Panel

**Status:** ACTIVE — Hydronics Phase H preview and design-basis evidence  
**Path:** `HVAC/gui_v3/panels/hydronics_schematic_panel.py`, `HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py`, `HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py`  
**Authority:** preview / observer / intent only

Current behaviour:

- reads hydronic topology and Basic PS projection
- displays branch-aware topology authority audit
- displays selected-route schematic preview
- displays received Basic PS section rows
- displays carried flow, pipe size, velocity, Δp/m, Re, friction factor, method, and iteration count
- displays Local K preview
- displays route pressure preview
- displays route shortfall / preliminary balancing burden
- displays F&R versus F+RR return comparison
- displays RR length basis and RR extra-length evidence
- lets user accept return-arrangement design basis at system / leg / common subleg / branch subleg level
- displays chosen-basis evidence in Proportioned tab
- supports frozen basis snapshot commit

Non-goals in current preview phase:

- pump selection
- valve selection
- final balancing
- pipe resizing
- final hydraulic result generation
- automatic design choice from F&R / F+RR evidence

Transition note:

Hydronics adapter / panel currently contains some persistence and commit wiring while controller boundary is maturing. This must be reviewed before final hydronic output authority is introduced.

### Environment Panel

**Status:** STABLE

Environment is design-condition authority. Future hydronic flow and return temperature inputs should live here or be sourced from project design conditions, then consumed by hydronic calculations.

### Project Panel

**Status:** STABLE

---

## Hydronics Engine / Hydronics Phase H

**Status:** ACTIVE PREVIEW / ENGINE CONTRACT MATURING  
**Path:** `HVAC/hydronics/`, `HVAC/hydronics_v3/`, `HVAC/core/fluid_friction/`, `HVAC/core/materials/`

### Engine authority

Hydronics engine is responsible for:

- flow
- pressure
- pipe / material pressure basis
- Local K pressure effects
- route pressure evidence
- balancing evidence
- pumps later
- valves later
- network topology + physics only

### Engine rules

- No GUI imports.
- No heat-loss engine imports.
- DTOs / state snapshots only across boundaries.
- No hidden persistence.
- No hidden heuristics.
- No final result unless explicitly committed through the future controller path.

### Current Hydronics capability

- Basic PS first-pass pipe sizing preview.
- Shared Haaland / Colebrook friction core.
- Hydronics Colebrook compatibility wrapper.
- Hydronics mass-flow pressure-drop wrapper.
- Basic PS friction helpers use shared core.
- Route / section pressure projection uses hydronic mass-flow wrapper.
- Route pressure exposes Re, friction factor, method, and Colebrook iteration metadata.
- Route accumulator Colebrook metadata is merged into received section rows.
- Local K pressure preview is section-level.
- Route shortfall and preliminary balancing burden are previewed.
- F&R / F+RR return path comparison is previewed.
- RR added length can affect reverse-return route comparison.
- RR length basis modes are recognised:
  - `physical_loop_zero_extra`
  - `downstream_proxy`
  - `manual_allowance`
- RR length basis belongs with return-arrangement intent.
- Chosen-basis Proportioned preview is read-only.

### Explicit current non-goals

- final pump sizing
- final valve selection
- final balancing
- pipe resizing
- final hydraulic result generation
- final installation instruction
- hidden automatic design choice

---

## Heat-Loss → Hydronics Boundary

**Status:** ACTIVE DESIGN BOUNDARY

### Rule

Hydronics may consume heat-loss results but must not import heat-loss engine internals.

### Allowed

- committed room heat-load result
- DTO / ProjectState result snapshot
- room_id-based demand lookup
- emitter demand evidence

### Forbidden

- hydronics running heat-loss calculations
- hydronics importing heat-loss engine physics
- hydronics mutating heat-loss inputs
- hydronics inferring hidden fabric physics

### v1 interpretation

Heat-loss topology gives hydronics a room demand graph, not a hydraulic pipe network.

---

## Emitters — v1

**Status:** ACTIVE MODEL  
**Path:** `HVAC/hydronics/emitter_v1.py`

### Authority

- Represents radiator / emitter intent.
- Belongs to ProjectState.
- Does not perform hydronic calculation.
- Does not know about GUI.

### Current fields

- emitter_id
- room_id
- name
- emitter_type
- design_output_W
- flow_temp_C
- return_temp_C
- room_temp_C
- notes

### Current / next work

- One emitter candidate per heated room.
- `design_output_W` follows committed room heat-loss `Qt` when available.
- Status shown if no heat-loss result exists.

---

## GUI Theme & Accent System

**Status:** ACTIVE  
**Path:** `HVAC/gui_v3/common/`

### Rules

- Accent colours only.
- No semantic meaning unless explicitly assigned by a panel contract.
- Installation-level preference.
- Focus styling is presentation, not engineering authority.

---

## Explicit Global Non-Goals

The following are forbidden everywhere:

- GUI performing calculations
- panels mutating ProjectState directly
- implicit recalculation
- hidden authority
- cross-engine imports
- GUI heuristics becoming engineering facts
- Hydronics calculating heat loss
- Heat-loss topology pretending to be pipe routing
- Openings changing HLP physics before explicit projection phase
- Preview evidence being treated as final hydraulic output

Violations are architectural bugs.

---

## Runner Purity Contract

**Status:** FROZEN  
**Scope:** `*_runner_v*` and equivalent pure calculation functions

### Rules

- pure functions
- no mutation of inputs
- no hidden caching
- no persistence
- no GUI access
- explicit return values only

This enables reproducibility, testing, parallelism, and future acceleration.

---

## Identity & Addressing — v1

**Status:** FROZEN + EXTENDED

### Identifiers

- `room_id` — stable project identifier
- `element_id` — stable within room / worksheet element context
- `surface_id` — stable projected surface / segment identifier
- `segment_id` — boundary topology identity
- `construction_id` — construction authority identity
- `profile_id` — opening profile identity
- `emitter_id` — hydronic emitter identity
- `leg_id` — hydronic leg identity
- `subleg_id` — hydronic subleg identity
- `section_id` — hydronic route / pipe section identity
- `route_id` — hydronic route identity where available

### Rules

- Overrides and results use identity.
- Geometry may change shape, IDs persist where the engineering object persists.
- Execution relies on identity, not GUI selection.
- Room-level openings use `room_id`.
- v1 openings do not require wall placement identity.
- Hydronic section focus uses `section_id`, not visible row number.

---

## Phase H — Hydronics Proportioning Preview

**Status:** ACTIVE

### Scope

- branch-aware topology audit
- Basic PS handoff
- shared Haaland / Colebrook core
- Colebrook-backed route pressure evidence
- Local K section pressure preview
- route shortfall / preliminary balancing burden
- F&R / F+RR comparison
- RR length basis modes
- return arrangement acceptance
- chosen-basis Proportioned preview

### Current milestone

- H-S29-M / H-S29-M1 / H-S29-M2: RR length basis mode control, intent storage, and acceptance evidence refresh
- Next: H-S29-N — manual RR extra length entry

### Non-goals

- pump sizing
- valve sizing / selection
- final balancing
- final pipe resizing
- final hydraulic authority

---

## Next Planned Work

### Immediate

- finish / commit H-S29-M1 and H-S29-M2 if pending
- H-S29-N — manual RR extra length entry
- confirm manual metre input updates RR extra length and RR extra Δp evidence
- keep return comparison evidence as guidance only

### Deferred

- review Hydronics controller boundary debt
- persist / reload RR length basis intent cleanly if project save/load does not already do so
- add clearer return-arrangement wording: “Evidence is guidance only — user design basis remains authoritative”
- project openings into HLP rows
- net wall Qf from room-level opening schedule
- final hydronic pump / valve / balancing / pipe resizing phases

---

## Change Policy

Any change that violates a freeze must:

- be deliberate
- be documented
- update the relevant freeze document
- justify architectural impact

Silent violations are bugs.

---

**Authoritative owner:** Ian Allison  
**Repository:** HVACgooee  
**Licence:** GPL-v3 core  
**Status:** CANONICAL

# ======================================================================
# END OF DOCUMENT
# ======================================================================
