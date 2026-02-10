
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

# ======================================================================
# END OF DOCUMENT
# ======================================================================
