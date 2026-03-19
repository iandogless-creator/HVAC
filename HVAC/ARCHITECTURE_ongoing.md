
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

A room must define internal length and width to exist as a calculable
entity. All other geometric and fabric inputs build upon this base.
Scalar external wall length is a permanent modelling mode and remains
available alongside future orientation and vector-based geometry.

Rooms must be explicitly created and selected via the Room Panel
before they can participate in geometry, fabric editing, or heat-loss
modelling. A new project with zero rooms is the only exception.
Mouse selects the candidate; keyboard edits the value.
Selection semantics are not tied to focus traversal.

✅ Canonical naming (LOCK THIS)
Concept	Canonical field
Area	area_m2
ΔT	delta_t_k
U-value	u_value_w_m2k
Fabric heat loss	qf_w
# ======================================================================
# END OF DOCUMENT
# ======================================================================
