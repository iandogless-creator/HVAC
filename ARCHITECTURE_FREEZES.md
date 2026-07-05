# HVACgooee — Architecture Freezes

Status: CANONICAL  
Owner: Ian Allison  
Repository: HVACgooee  
Licence: GPL-v3 core  
Last updated: 2026-07-05  
Current active area: Hydronics Phase H — proportioning / return-arrangement evidence

This document is authoritative.

In the event of conflict between code and this file, the architecture described here takes precedence.

These freezes exist to prevent silent architectural drift. They are not intended to stop progress. They define what must remain stable while the project grows.

---

## FREEZE 1 — ProjectState Authority Contract (LOCKED)

### Scope

`HVAC/project/` and all runtime project-state containers.

### Status

LOCKED

### Definition

`ProjectState` is the sole authoritative data model.

It owns project intent, identity, persisted engineering state, and committed result containers.

### Rules

- ProjectState owns what the project is.
- ProjectState may hold runtime authority containers.
- ProjectState does not calculate.
- ProjectState does not import GUI.
- ProjectState does not silently repair engineering intent.
- ProjectState should expose explicit containers for user intent and committed results.

### Authority examples

ProjectState may own:

- rooms
- environment
- boundary segments
- constructions
- surface construction map
- heat-loss readiness / result containers
- emitters
- room opening schedules
- hydronic topology
- hydronic return-arrangement intent
- hydronic local K intent
- committed hydronic basis snapshots

### Forbidden

- Hidden calculation inside ProjectState
- GUI imports inside ProjectState
- Implicit state repair
- Silent creation of engineering results
- Treating display state as engineering authority

---

## FREEZE 2 — Layer Responsibilities / Execution Topology (LOCKED)

### Scope

Application architecture across GUI, adapters, controllers, runners, and ProjectState.

### Status

LOCKED

### Canonical topology

```text
GUI → Adapter → Controller → Runner → Result
Result → ProjectState only through explicit commit
```

Observer / editor side paths are allowed only as intent:

```text
Panel → Adapter → Context / Controller → ProjectState
```

Reverse authority flows are forbidden.

### GUI

- Displays intent and results.
- Emits user intent.
- Never executes physics.
- Never owns state.
- Never mutates authoritative engineering state directly.

### Adapter

- Observes ProjectState.
- Builds projection rows and display DTOs.
- Wires GUI intent to controller / context / transition path.
- Has no engineering authority.
- Must not invent physics, readiness, or final results.

### Controller

- Decides execution scope.
- Invokes runners.
- Owns readiness policy.
- Commits results.
- Marks validity explicitly.

### Runner

- Performs pure computation.
- Is stateless.
- Reads input DTOs or read-only state snapshots.
- Has no GUI imports.
- Has no persistence side effects.

### Forbidden

- GUI → Runner calls
- Runner → ProjectState mutation
- Adapter committing final results as a permanent architecture
- Validation policy inside runners
- GUI-derived authority
- Silent execution blocking

### Hydronics transition note

Hydronics Phase H currently contains some adapter/panel persistence and commit wiring while the Hydronics controller boundary is still maturing.

This is documented transition debt.

It is not a permanent relaxation of this freeze.

Before final hydronic output, pump selection, valve selection, final balancing, or pipe resizing become authoritative, those commit paths should be moved behind explicit controller boundaries.

---

## FREEZE 3 — Runner Purity Contract (LOCKED)

### Scope

`*_runner_v*` modules and equivalent pure calculation functions.

### Status

LOCKED

### Rules

- Runners are pure functions.
- No mutation of inputs.
- No persistence.
- No GUI access.
- No hidden caching.
- No validation inference.
- No side-channel authority.
- Diagnostics may exist, but must not become control flow authority.

### Output

- Explicit return values only.
- Results must be reproducible from the same inputs.

This contract enables:

- reproducibility
- testing
- parallelism
- future acceleration
- future CLI / batch / API execution

---

## FREEZE 4 — Overrides Semantics (LOCKED)

### Scope

Heat-loss worksheet overrides and future equivalent override systems.

### Status

LOCKED

### Definition

Overrides represent user intent, not calculated results.

### Rules

- Overrides never store calculated values.
- Overrides may shadow derived inputs.
- Overrides are optional and sparse.
- Clearing an override removes intent.
- Any override change invalidates dependent results.
- Overrides must be explicitly addressable by stable identity.

### Ownership

- Heat-loss overrides belong to `HeatLossStateV1.overrides`.
- Future domain overrides must have an equivalent explicit owner.
- Controllers write overrides.
- Runners and adapters read overrides.

### Forbidden

- Results overwriting overrides
- Overrides auto-clearing
- Implicit override creation
- Override-driven hidden mutation
- Treating a calculated result as a user override

---

## FREEZE 5 — GUI v3 Observer Rule (LOCKED)

### Scope

`HVAC/gui_v3`

### Status

LOCKED

### Definition

GUI panels are non-authoritative observers and intent emitters.

### Rules

- Panels may display incomplete or stale data.
- Panels may be destroyed or recreated freely.
- Panels never own engineering state.
- Panels emit intent only.
- Panels do not infer readiness.
- Panels do not commit results.
- Panels do not execute physics.

### Consequences

Globally not frozen unless separately stated:

- panel layout
- widget composition
- styling
- docking behaviour
- visual grouping
- table column ordering

Exception:

- the Heat-Loss worksheet column order is locked by Freeze 8.

Authority is never derived from GUI state.

---

## FREEZE 6 — Identity & Addressing (LOCKED)

### Scope

Rooms, elements, surfaces, boundary segments, openings, emitters, and hydronic route/section identities.

### Status

LOCKED — v1 identity contract

### Identifiers

- `room_id` — stable project room identifier
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
- Geometry may change shape, but IDs persist where the engineering object persists.
- Execution relies on identity, not GUI selection.
- Room-level openings use `room_id`.
- v1 openings do not require wall placement identity.
- Hydronic section focus must use `section_id`, not visible row number.

This freeze protects future geometry, schematic, and hydronic topology refactors.

---

## FREEZE 7 — Readiness & Blocking Semantics (LOCKED)

### Scope

Heat-loss execution readiness and user-facing blocking messages. The same pattern applies to later Hydronics readiness.

### Status

LOCKED

### Definition

Readiness determines whether an execution may run.

Blocking messages explain why execution cannot run.

Readiness is policy, not physics and not GUI authority.

### Ownership

| Concern | Owner |
|---|---|
| Readiness rules | Controller |
| Readiness state | ProjectState / domain state |
| Blocking reasons | Controller, explicit |
| Display of reasons | GUI, observer only |

### Rules

1. GUI never decides readiness.

   Panels must not infer “ready” or “not ready”.

2. Readiness is explicit and boolean.

   Controllers expose:

   ```text
   is_ready: bool
   blocking_reasons: list[str]
   ```

3. Blocking reasons are additive.

   Multiple reasons may exist simultaneously.

4. Readiness is phase-scoped.

   Heat-loss readiness does not require Hydronics data.

   Hydronics readiness must not be smuggled into Heat-Loss readiness.

5. Readiness invalidates results where appropriate.

   Any change to intent inputs must mark dependent results stale or dirty.

6. GUI wording is non-authoritative.

   Allowed:

   - “Cannot run yet because…”
   - “Heat-loss not ready”
   - “Results invalidated”
   - “Preview only”
   - “Evidence incomplete”

   Forbidden:

   - “Incorrect”
   - “Invalid input”
   - “Error in geometry”

The system explains. It does not judge.

### Explicitly forbidden

- GUI computing readiness
- Adapters inventing blocking reasons
- Runners checking readiness policy
- Silent execution blocking
- Implicit auto-runs

---

## FREEZE 8 — Heat-Loss Worksheet & HLPE Edit Spine (LOCKED)

### Scope

Heat-Loss worksheet column semantics, HLPE targeting model, and GUI v3 observer-only worksheet behaviour.

### Status

LOCKED

### Definition

HLPE is a GUI-only edit overlay that allows the user to express engineering intent against existing fabric elements.

HLPE:

- looks inline
- is not inline
- never mutates authoritative state
- never depends on layout position
- never executes heat-loss

### Locked column order

The Heat-Loss worksheet column order is:

```text
Element | Area | U | ΔT | Qf
```

Rationale:

- matches Qf = A × U × ΔT
- matches engineering scan order
- aligns with spreadsheet and hand-calculation convention

This specific worksheet order is locked for v1.

### Locked edit targeting

HLPE activation is non-positional.

Edits are routed exclusively by semantic identifiers:

```text
(room_id, element_id, attribute)
```

Where:

```text
attribute ∈ {"area", "u_value", "delta_t"}
```

### Explicitly prohibited

- column-index routing
- visual position inference
- table geometry-dependent edit routing
- inline worksheet mutation
- GUI-driven state changes
- HLPE calculating or validating engineering data

### Worksheet behaviour rules

- Worksheet adapters are observer-only.
- GUI never executes heat-loss.
- GUI never owns authoritative results.
- DEV rows may be injected only as temporary bootstrap when real engine rows are unavailable.
- DEV scaffolding must be removed once controller-backed previews/results exist.

### Result placement

- Element-level `Qf` values appear in the worksheet.
- Aggregate results appear below the worksheet.
- Summary results are not worksheet rows.

---

## FREEZE 9 — Wall Wizard / Room-Level Opening Schedule Contract (LOCKED)

### Scope

Wall Wizard v1, room-level opening schedules, opening profile preview rows, runtime ProjectState ownership of opening schedules, and Wall Wizard add / remove / clear behaviour.

### Status

LOCKED

### Applies to

- `HVAC/gui_v3/wizards/wall_wizard.py`
- `HVAC/gui_v3/adapters/wall_wizard_adapter.py`
- `HVAC/core/opening_schedule_v1.py`
- `ProjectState.room_opening_schedules`

### Definition

Wall Wizard v1 is a room-level opening schedule editor.

It is not:

- a CAD wall editor
- a heat-loss engine
- an authoritative wall geometry system

### Current scope

- Windows and doors are scheduled at room level.
- Openings are not placed on individual wall segments.
- Any external wall click in a room may open the same room-level external opening schedule.
- Gross external wall area is the total external wall area for that room.
- Net wall area is previewed as:

```text
net_external_wall_area = gross_external_wall_area - total_room_opening_area
```

### Authority

- WallWizardDialog is UI only.
- WallWizardAdapter routes intent.
- `ProjectState.room_opening_schedules` owns runtime opening schedules.
- `RoomOpeningScheduleV1` owns room-level opening schedule items.
- `OpeningScheduleItemV1` owns profile, size, quantity, and construction_id.

### Rules

- No HLP Qf mutation yet.
- No project-file persistence yet unless explicitly added in a later phase.
- No CAD placement.
- No wall-position inference.
- Opening U-values resolve by `construction_id`.
- `OpeningScheduleItemV1` never stores U-value.

---

## FREEZE 10 — Hydronics Proportioning Preview & Return Arrangement Basis Contract (LOCKED)

### Scope

Hydronics Phase H proportioning preview, Basic PS handoff, route pressure evidence, Local K preview, return arrangement comparison, reverse-return length basis, and chosen-basis Proportioned preview.

### Status

LOCKED — Hydronics Phase H preview contract

### Applies to

- `HVAC/gui_v3/panels/hydronics_schematic_panel.py`
- `HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py`
- `HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py`
- `HVAC/core/fluid_friction/`
- `HVAC/core/materials/pipe_materials_library.py`
- `HVAC/hydronics/sizing/`
- `HVAC/hydronics/local_losses/`
- `HVAC/hydronics/pipes/dp/`
- `HVAC/hydronics/proportioning/`
- `HVAC/hydronics/proportioning/return_arrangement_acceptance_intent_v1.py`

### Definition

Hydronics Phase H is a preview and design-basis evidence phase.

It may show detailed pressure evidence.

It does not yet produce a final hydraulic design.

### Basic PS contract

Basic PS is a first-pass sizing / handoff basis.

It may provide:

- topology section rows
- carried flow
- candidate pipe size
- first-pass velocity
- first-pass pressure gradient
- first-pass status evidence

Basic PS must remain clearly labelled as preliminary where appropriate.

Basic PS does not:

- select the pump
- select valves
- perform final balancing
- resize final pipework
- create final hydraulic authority

### Shared friction / pressure contract

The shared friction core is the canonical route for friction-factor calculations.

The hydronics pressure path may use:

- Haaland for first-pass / candidate sizing where appropriate
- Colebrook-White for detailed route pressure evidence
- Darcy-Weisbach pressure calculation
- material roughness from the pipe material library
- candidate internal diameter from the pipe material / pipe size basis

Hydronics code must not silently re-implement independent friction solvers where the shared core should be used.

### Route pressure evidence contract

Route pressure preview is evidence only.

It may show:

- section Δp
- straight Δp
- Local K Δp
- route ΣΔp
- controlling route candidate
- route shortfall
- preliminary balancing burden
- Reynolds number
- friction factor
- friction method
- Colebrook iteration count

Route pressure preview does not commit:

- balancing valve selection
- pump head
- final pipe size
- final hydraulic result
- final installation instruction

### Local K contract

Local K intent is section-level design intent.

Local K preview may calculate local pressure loss for evidence.

Local K preview does not become final balancing.

### Return arrangement contract

Return arrangement comparison may show F&R versus F+RR evidence.

It may show:

- F&R route Δp
- F+RR route Δp
- route Δp change
- balancing burden
- resistance reduction or increase
- RR length basis
- RR extra length
- RR extra Δp

This evidence informs design judgement.

It must not automatically select the design basis.

### Accepted return arrangement basis

Return arrangement acceptance is user design intent.

It may be accepted at:

- system level
- leg level
- common subleg level
- branch subleg level

Inheritance is allowed.

Room-level return-arrangement selection is not part of v1.

Room-level or subleg-level exclusion / opt-out is not part of v1.

Hydronic topology membership governs participation.

### Reverse-return length basis

Reverse-return added length is separate from reverse-return arrangement.

The recognised RR length basis modes are:

```text
physical_loop_zero_extra
downstream_proxy
manual_allowance
```

Display labels:

```text
Physical loop — no extra allowance
Downstream proxy allowance
Manual allowance
```

Meaning:

- `physical_loop_zero_extra` means a represented or perfect physical loop is not penalised with invented extra pipe.
- `downstream_proxy` means the model derives a provisional extra-length allowance from downstream path evidence.
- `manual_allowance` means the user provides an explicit extra length in metres.

The RR length basis belongs with return-arrangement design intent, not as unrelated GUI state.

The preferred authority home is:

```text
ProjectState.hydronic_return_arrangement_intent.rr_added_length_basis_mode
ProjectState.hydronic_return_arrangement_intent.rr_added_length_m
```

### Proportioned tab contract

The Proportioned tab may show chosen-basis evidence.

It is read-only at this stage.

It may show:

- resolved effective return arrangement
- chosen-basis route Δp
- chosen-basis controlling route
- chosen-basis shortfall / preliminary burden
- chosen-basis readiness summary

It does not yet show a final hydraulic result.

### Commit contract

Commit Proportioning currently commits a frozen basis snapshot only.

The snapshot records accepted design basis evidence.

It does not mean:

- pump selected
- valves selected
- balancing complete
- pipework resized
- installation-ready hydraulic design complete

### Evidence wording contract

Hydronics evidence should use wording such as:

- “preview only”
- “candidate”
- “evidence”
- “chosen basis”
- “user design basis”
- “controlling route candidate”
- “preliminary balancing burden”

Hydronics evidence should avoid wording that implies final authority before the final hydraulic phase exists.

### Explicitly forbidden in Phase H preview

- pump selection
- valve selection
- final balancing
- final pipe resizing
- final hydraulic result
- automatic design choice from F&R / F+RR evidence
- hidden RR extra length
- treating a table or proxy as natural law
- treating GUI selection as engineering authority

### Transition debt

Current Hydronics adapter/panel wiring includes some direct intent persistence while the Hydronics controller boundary is still under development.

This is accepted only as short-term transition debt.

It must be reviewed before any final hydronic result, pump, valve, or balancing commit path is introduced.

---

## NOT FROZEN (INTENTIONALLY)

Unless a specific freeze above says otherwise, the following remain unfrozen:

- panel layout
- visual style
- table column ordering outside locked Heat-Loss worksheet columns
- docking behaviour
- education content
- explanatory wording
- schematic drawing layout
- hover content
- focus colour and visual affordances
- UI grouping and collapse behaviour
- future report/export layout

These may evolve without architecture-freeze updates, provided authority boundaries are preserved.

---

## CHANGE POLICY

Any change that violates a freeze must:

- be deliberate
- be documented
- update this file
- justify architectural impact

Silent violations are bugs.

If implementation temporarily breaches a freeze during a transition phase, the breach must be labelled as transition debt and scheduled for cleanup before the affected feature becomes final authority.

---

## FINAL NOTE

These freezes exist to reduce complexity, not creativity.

Future work is expected, but must respect the authority boundaries.

This is how HVACgooee scales without collapsing under its own weight.

In short:

```text
Intent is explicit.
Physics is traceable.
Preview is not final.
The designer remains authoritative.
```

# ======================================================================
# END OF DOCUMENT
# ======================================================================
