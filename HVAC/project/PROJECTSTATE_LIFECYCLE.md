# ProjectState Lifecycle

**Status:** CANONICAL  
**Applies To:** Project Core v3+, GUI v3  
**Audience:** Engine authors, GUI authors, maintainers

---

## Purpose

`ProjectState` is the **single authoritative container** for a project’s
declared intent and committed engineering results.

It exists to:
- Provide a stable integration surface between subsystems
- Decouple engines from the GUI
- Prevent implicit or hidden state propagation

`ProjectState` is **not** an engine and **not** a GUI model.

---

## Core Principles (LOCKED)

1. **Single Source of Truth**  
   All authoritative project data flows through `ProjectState`.

2. **Explicit Mutation Only**  
   `ProjectState` is mutated only by:
   - Factories
   - Runners
   - Explicit commit steps

3. **Read-Only Observation**  
   GUI layers and adapters observe `ProjectState` but do not modify it.

4. **No Implicit Derivation**  
   Nothing inside `ProjectState` is inferred, guessed, or auto-created.

---

## Lifecycle Overview

The project lifecycle proceeds through **explicit phases**.

Heat-Loss as Authoritative ProjectState Sub-State

As of Phase D.2, heat-loss results are represented as a first-class sub-state of ProjectState.

ProjectState
 └─ heatloss : HeatLossStateV1


Heat-loss results are no longer stored as loose scalar fields.

HeatLossStateV1 — Responsibility

HeatLossStateV1 owns only committed results.

It:

Stores per-room heat-loss results

Optionally stores a project-level aggregate

Tracks explicit project validity / staleness

It does not:

Perform calculations

Infer completeness

Observe GUI actions

Perform validation

Trigger events

All mutation occurs via explicit commit methods only.

Commit Semantics (LOCKED)
Room-Level Commit

Overwrites the result for exactly one room

Marks any project aggregate as stale

Does not affect other room results

Project-Level Commit

Replaces all room results atomically

Commits project aggregate (if supplied)

Clears project stale state

No implicit aggregation or inference occurs.

Authority Rules (UNCHANGED)

Controllers are the only writers

Adapters and GUI layers are read-only

Runners remain pure and stateless

All authoritative values live in ProjectState

Architectural Statement

Heat-loss results are authoritative state,
not derived UI values.

This invariant is mandatory from Phase D.2 onward.

Deferred (Explicit)

Readiness / missing-data inspection

Event or listener infrastructure

Asynchronous execution

Progress reporting

Persistence format changes

None of the above are introduced by this phase.

Migration Note

Any legacy access to:

project_state.heatloss_qt_w
project_state.heatloss_valid


must be replaced with:

project_state.heatloss.project_qt_w
project_state.heatloss.project_valid


