
### Responsibilities
This document is authoritative. In the event of conflict between code and
this file, the architecture described here takes precedence.


#### GUI
• Displays intent and results
• Emits user intent
• Never executes physics
• Never mutates state

#### Adapter
• Observes ProjectState
• Forwards intent
• Wires GUI → controller
• Has NO authority

#### Controller
• Decides execution scope
• Invokes runners
• Commits results
• Marks validity explicitly

#### Runner
• Pure computation
• Stateless
• Read-only ProjectState access
• No side effects
• No GUI imports

### Forbidden

❌ GUI → Runner calls
❌ Runner → ProjectState mutation
❌ Adapter committing results
❌ Validation inside runners

---

## FREEZE 3 — Runner Purity Contract (LOCKED)

### Scope
`*_runner_v*` modules

### Status
**LOCKED**

### Rules

• Runners are PURE functions
• No mutation of inputs
• No caching
• No logging beyond diagnostics
• No persistence
• No GUI access
• No validation inference

### Output
• Explicit return values only
• No side-channel effects

This contract enables:
• reproducibility
• testing
• parallelism
• future acceleration (threads / GPU / distributed)

---

## FREEZE 4 — Overrides Semantics (LOCKED)

### Scope
Heat-Loss worksheet overrides (v1)

### Status
**LOCKED**

### Definition
Overrides represent **user intent**, not results.

### Rules

• Overrides never store calculated values
• Overrides may shadow derived inputs
• Overrides are optional and sparse
• Clearing overrides removes intent
• Any override change invalidates results

### Ownership
• Stored in `HeatLossStateV1.overrides`
• Written only by controllers
• Read by runners and adapters

### Forbidden

❌ results overwriting overrides
❌ overrides auto-clearing
❌ implicit override creation
❌ override-driven mutation

---

## FREEZE 5 — GUI v3 Observer Rule (LOCKED)

### Scope
`HVAC.gui_v3`

### Status
**LOCKED**

### Definition
GUI panels are **non-authoritative observers**.

### Rules

• Panels may display incorrect or incomplete data
• Panels may be destroyed or recreated freely
• Panels never own state
• Panels emit intent only
• Panels do not infer readiness
• Panels do not commit results

### Consequences

• Panel layout is NOT frozen
• Widget composition is NOT frozen
• Styling is NOT frozen
• Docking behavior is NOT frozen

Authority is never derived from GUI state.

---

## FREEZE 6 — Identity & Addressing (LOCKED)

### Scope
Rooms, elements, surfaces

### Status
**LOCKED — v1 Identity Contract**

### Identifiers

• room_id — stable project identifier
• element_id — stable within room
• surface_class — semantic classification

### Rules

• IDs are used for overrides and results
• Geometry may change shape but IDs persist
• Execution relies on identity, not GUI selection

This freeze protects future geometry refactors.

---

## NOT FROZEN (INTENTIONALLY)

The following are **explicitly unfrozen**:

• Panel layout and UI composition
• Styling and theming
• Education content
• Table column ordering
• Docking behavior
• GUI persistence strategy

These are expected to evolve.

---

## CHANGE POLICY

Any change that violates a freeze must:

• be deliberate
• be documented
• update this file
• justify architectural impact

Silent violations are bugs.

---

## FINAL NOTE

These freezes exist to reduce complexity, not creativity.

Future work is expected — but must respect these boundaries.

This is how HVACgooee scales without collapsing under its own weight.

FREEZE 7 — Readiness & Blocking Semantics (Phase F-B) (LOCKED)
Scope

Heat-Loss execution readiness and user-facing blocking messages
(GUI v3, adapters, controllers)

Status

LOCKED

Definition

Readiness determines whether an execution may run.
Blocking messages explain why execution cannot run.

These are presentation and control concerns, not physics and not GUI authority.

Ownership
Concern	Owner
Readiness rules	Controller
Readiness state	ProjectState / HeatLossState
Blocking reasons	Controller (explicit)
Display of reasons	GUI (observer only)
Rules
1. GUI never decides readiness

• Panels must not infer “ready” or “not ready”
• Panels may show partial, incorrect, or missing data
• Panels only display readiness and reasons supplied to them

❌ if not length: disable run
❌ if no room selected: infer not ready

2. Readiness is explicit and boolean

Controllers expose:

is_ready: bool
blocking_reasons: list[str]


There is no implicit readiness.

3. Blocking reasons are additive

Multiple reasons may exist simultaneously.

Example:

Cannot run heat-loss because:
• No room selected
• Room has no geometry
• No constructions defined


No prioritisation or masking in GUI.

4. Readiness is phase-scoped

Phase F-B readiness rules are minimal:

Heat-Loss may NOT run if:
• No project loaded
• No room selected
• Room has no geometry intent
• Required constructions are missing

Heat-Loss does NOT require (yet):
• Complete U-values
• Overrides resolved
• Ventilation present
• Hydronics data

These expand only in later freezes.

5. Readiness invalidates results

Any change to intent inputs (geometry, ACH, constructions, overrides):

• Marks heat-loss results dirty
• Clears “ready” state
• Requires explicit re-run

No auto-recalculation.

6. GUI wording is non-authoritative

Allowed phrases:
• “Cannot run yet because…”
• “Heat-loss not ready”
• “Results invalidated”

Forbidden phrases:
❌ “Incorrect”
❌ “Invalid input”
❌ “Error in geometry”

The system explains — it does not judge.

Consequences

• Run buttons may be enabled/disabled only from controller signals
• Status panels mirror controller state verbatim
• Tests assert readiness logic without GUI involvement
• Future solvers (batch, CLI, API) reuse identical rules

Explicitly Forbidden

❌ GUI computing readiness
❌ Adapters inventing blocking reasons
❌ Runners checking readiness
❌ Silent execution blocking
❌ Implicit auto-runs

Rationale

This freeze:
• Preserves GUI v3 observer purity
• Makes readiness testable
• Prevents “spreadsheet logic” creeping into widgets
• Enables future non-GUI execution paths

Readiness is policy, not physics.


FREEZE 8 — HLPE Interaction & Signal Contract (GUI v3) (LOCKED)
Scope

Heat-Loss Edit Overlay (HLPE), Heat-Loss worksheet interaction, GUI v3 adapters

Status

LOCKED

Purpose

This freeze formalises the HLPE interaction model and guarantees that all
heat-loss editing behaviour remains semantic, non-positional, and
non-authoritative.

This prevents regression into column-index logic, inline mutation, or GUI-driven
state changes.

Definition

HLPE is a GUI-only edit overlay that allows the user to express engineering
intent against existing fabric elements.

HLPE:
• Looks inline
• Is not inline
• Never mutates authoritative state
• Never depends on layout position

Locked Interaction Model
Selection

• Mouse left-click only
• Clicking an editable worksheet cell opens HLPE
• Keyboard navigation is not used for candidate selection

Cancellation

• Esc always cancels
• Cancel closes HLPE and discards staged edits
• No state mutation occurs

Apply

• Apply emits semantic edit intent only
• No calculation is triggered
• Results are marked dirty explicitly elsewhere

Locked Signal Contract

Worksheet → HLPE communication is semantic only.

Signals MUST include:
• room_id
• element_id (or surface identifier)
• attribute ∈ { "area", "u_value", "delta_t" }

Signals MUST NOT include:
❌ row index
❌ column index
❌ widget position
❌ layout assumptions

Column order and column width are presentation concerns only.

Attribute Ownership

• "area" — geometric magnitude override
• "u_value" — construction / fabric performance override
• "delta_t" — assumption override

Editor selection is driven only by attribute, never by column position.

Non-Editable Cells

• Clicking non-editable cells MUST NOT open HLPE
• Element name cells display a tooltip:

“Element naming is read-only in v1”

This behaviour is intentional and not an error.

Authority Rules

HLPE:
• Does NOT mutate ProjectState
• Does NOT perform validation
• Does NOT execute calculations
• Does NOT infer readiness

All HLPE output is intent, not results.

Rationale

This freeze ensures that:

• Worksheet column reordering cannot break behaviour
• HLPE remains robust as UI layout evolves
• Editing semantics are testable and explicit
• GUI v3 remains a pure observer/emitter layer

HLPE is now safe to extend without architectural drift.

Consequences

Allowed:
• Reordering worksheet columns
• Changing column widths
• Changing visual layout
• Adding new HLPE-editable attributes later

Forbidden:
❌ Positional signal logic
❌ Inline worksheet mutation
❌ GUI-driven state changes
❌ HLPE calculating or validating data

Level of Achievement (as of this freeze)

At this point, GUI v3 has achieved:

• A stable, non-positional HLPE interaction model
• Spreadsheet-faithful worksheet behaviour
• Explicit edit vs result separation
• Clear user feedback for non-editable cells
• A future-proof foundation for batch edits, undo/redo, and richer intent DTOs

Further work is additive only.

Freeze: Heat-Loss Worksheet Semantics & HLPE Edit Spine (GUI v3)

Status: LOCKED (GUI v3 / Heat-Loss v3 / HLPE v1)
Date: 2026-02-18

1. Scope

This freeze governs:

Heat-Loss worksheet column semantics

HLPE (Heat-Loss Edit Overlay) targeting model

GUI v3 observer-only worksheet behaviour

It applies to all GUI v3 worksheet views regardless of data source
(DEV preview rows, engine previews, or authoritative results).

2. Column Order (LOCKED)

The Heat-Loss worksheet column order is fixed as:

Element | Area | U | ΔT | Qf


Rationale:

Matches engineering mental model: Qf = A × U × ΔT

Optimises left-to-right scan for experienced engineers

Aligns with spreadsheet and hand-calc conventions

This order must not change in v1.

3. HLPE Edit Targeting (LOCKED)

HLPE activation is non-positional.

Edits are routed exclusively by semantic identifiers:

(room_id, element_id, attribute)


Where attribute ∈ {"area", "u_value", "delta_t"}.

Explicitly prohibited:

Column index–based routing

Visual position–based inference

Table geometry–dependent logic

This guarantees:

Safe column reordering

Stable edit behaviour across themes, layouts, and DPI

Future keyboard/navigation support without refactor

4. Worksheet Behaviour Rules

Worksheet adapters are observer-only

No calculations are permitted in GUI adapters

No mutation of ProjectState

DEV preview rows are allowed temporarily

DEV rows must be visually plausible but non-authoritative

DEV preview population must be removed once
HeatLossControllerV4 provides real previews/results.

5. Results Placement (LOCKED)

Element-level Qf values appear only in the worksheet

Aggregate results (ΣQf, Qt, Cv) are displayed below the worksheet

Summary results are not rows

This separation preserves worksheet clarity and auditability.

6. Visual Conventions (v1)

Units appear under column headers, not in cells

Numeric values are right-aligned

Decimal points are aligned

Default precision: 2 decimal places (configurable post-v1)

Neutral background; no dominant colour fills

Edit indication may use subtle border/accent (not fill)

7. Non-Goals (Explicit)

This freeze does not include:

Keyboard navigation

Editable element names

User-configurable precision

Theming (dark mode planned post-v1)

8. Regression Rule

Any change affecting:

column order

edit routing

worksheet semantics

requires an explicit architecture freeze update.

Silent drift is not permitted.

Explicit non-goals (this phase):

External wall length is not represented

Geometry is treated as scalar intent only (L, W, H, ACH, Ti)

No surface decomposition or orientation

These are deferred until after the HLPE interaction model and worksheet spine are proven stable

Heat-Loss Worksheet Contract (LOCKED)

Heat-Loss Worksheet & HLPE Contract — LOCKED

Status: CANONICAL
Scope: GUI v3

Locked Decisions

Worksheet Row Model

Heat-loss worksheet rows are represented by
HeatLossWorksheetRowDTO

DTO is GUI-only and non-authoritative

One DTO instance maps to one fabric/opening element

Column Semantics (Non-Positional)

Column order is fixed and canonical:

Element | Area | U | ΔT | Qf


HLPE edit targeting is based on semantic role,
not column index or widget position

Edit Pathway

Worksheet cell click → HLPE overlay → cancel/apply

Signal routing does not depend on keyboard navigation

Mouse left-click only in v1

ESC cancels active HLPE session

DEV Worksheet Rows

DEV rows may be injected when:

no engine previews exist

no declared fabric exists

DEV rows:

do not mutate ProjectState

do not calculate

are deterministic

DEV scaffolding must be removed once
HeatLossController produces real previews

Authority Boundary

GUI never executes heat-loss

GUI never owns authoritative results

Engines remain the sole source of truth

These rules are frozen to prevent regression of
interaction semantics and architectural boundaries.

That paragraph alone is worth the commit.

4. Why this is safe to land on main

You explicitly said you prefer to stay on main.
That’s justified here because:

✅ No engine behaviour is changed

✅ No data model authority is altered

✅ GUI-only scaffolding is clearly marked

✅ Contracts are documented, not implied

✅ Reversion would be trivial if needed

This is foundational, not experimental.

5. What this unlocks next (so you feel momentum)

After this commit, future work becomes linear and calm:

Next clean steps (in order):

Make DEV row visible (1 row is enough)

Highlight editable cell (subtle border, not colour wash)

Implement HLPE apply path for Area only

Replace DEV rows with engine preview output

Remove gui_v3/dev/heat_loss_dev_rows.py

No rewrites. No refactors. No fear.

### Phase F — Heat-Loss Worksheet Spine (FROZEN)

The Heat-Loss worksheet interaction model is frozen with the following rules:

• Worksheet rows are populated exclusively via HeatLossWorksheetRowDTO
• GUI adapters are observer-only (read ProjectState, never mutate)
• Cell edit intent is non-positional and attribute-addressed
• HLPE entry is triggered only via explicit cell intent
• DEV worksheet rows are permitted ONLY as a temporary bootstrap
• DEV rows MUST be removed once the engine provides real worksheet rows

This freeze guarantees:
• No regression to positional UI wiring
• No GUI-owned calculations
• Stable HLPE interaction semantics

# ======================================================================
# HVACgooee — ARCHITECTURE FREEZE
# Phase: H — Post–G-C System Behaviour & Readiness
# Status: FROZEN
# Date: Tuesday 18 February 2026, 09:17 am
# ======================================================================

## 1. Scope

Phase H formalises **post–G-C system behaviour** across the application.

This phase defines:
- Project readiness semantics
- Validity vs readiness rules
- Global invalidation behaviour
- GUI behavioural contracts
- Save / load invariants

Phase H introduces **no new calculation physics** and **no new UI panels**.

---

## 2. Authority (LOCKED)

| Layer | Authority |
|------|----------|
| ProjectState | **Sole authoritative data model** |
| Engines | Pure, deterministic, stateless |
| GUI | Observer + intent emitter only |
| Adapters | Read-only projection |
| DTOs | Immutable snapshots |

The GUI:
- MUST NOT derive or repair engineering intent
- MUST NOT auto-calculate
- MUST NOT persist transient state

---

## 3. Readiness Model (LOCKED)

A project SHALL expose a **derived readiness state**.

Readiness:
- Is computed from ProjectState
- Is never user-set
- Is not persisted
- Does not trigger calculation

### Canonical Readiness States

EMPTY
STRUCTURAL
ENVIRONMENT_READY
HEATLOSS_READY
HEATLOSS_VALID
HYDRONICS_READY (reserved)
COMPLETE (reserved)


Later phases MAY extend the enum but MUST NOT alter existing meanings.

---

## 4. Validity vs Readiness (LOCKED)

| Concept | Definition |
|-------|------------|
| Validity | Internal consistency of data |
| Readiness | Sufficiency of data to proceed |

Rules:
- Data may be valid but not ready
- Data may be ready but results invalidated
- Validity never implies readiness
- Readiness never implies calculation

---

## 5. Heat-Loss Invalidation Rules (LOCKED)

Any of the following SHALL invalidate heat-loss results:

- Geometry affecting area or volume
- Environment parameter changes (Te, authoritative Ti)
- Construction U-value change
- Element thermal participation toggle
- Room inclusion/exclusion from HL scope

Invalidation:
- MUST NOT auto-recalculate
- MUST be visible to the user
- MUST persist across save/load

---

## 6. GUI Behaviour Contracts (LOCKED)

### 6.1 Panel Roles

Every GUI panel MUST belong to exactly one role:

- **Observer Panel** — read-only projection
- **Edit Overlay Panel** — local, non-authoritative intent
- **Commit Panel** — writes to ProjectState

Panels MUST NOT mix roles.

---

### 6.2 Readiness-Driven UX

- Control enable/disable SHALL be driven by readiness only
- User messaging SHALL explain *why* an action is unavailable
- No hidden defaults or silent fixes are permitted

Example:
> “Heat-loss unavailable: external design temperature not defined.”

---

## 7. Save / Load Invariants (LOCKED)

### On Save
- Persist ProjectState only
- Exclude GUI state
- Exclude transient edit overlays
- Preserve invalidation flags

### On Load
- Recompute readiness
- Preserve invalid states
- Perform no automatic recalculation

Reopening a project MUST NOT change results without explicit user intent.

---

## 8. Post-G-C Behaviour Guarantee (LOCKED)

After Phase G-C and Phase H:

- Edits never silently propagate
- Commits are explicit
- Calculations are deliberate
- System state is explainable at all times

The application SHALL always be able to answer:
> “Why is this result missing, invalid, or stale?”

---

## 9. Non-Goals (Explicit)

Phase H does NOT define:
- Hydronics behaviour
- Templates or wizards
- Advanced geometry semantics
- Calculation sequencing beyond HL

Those belong to later phases.

---

## 10. Enforcement

Any future phase that:
- Auto-repairs data
- Auto-calculates on edit
- Persists GUI state
- Blurs authority boundaries

**violates Phase H** and MUST be rejected or refactored.

---

## 11. Lock Statement

Phase H defines **system behaviour**, not features.

Once frozen:
- Behavioural rules are immutable
- Later phases must comply, not reinterpret
- Deviations require a new freeze note

**Phase H is hereby FROZEN.**

# ======================================================================
# END OF DOCUMENT
# ======================================================================
