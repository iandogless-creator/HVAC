# HVACgooee — Architecture Status (v3)

Timestamp (UK):
Monday 26 January 2026, 04:02 am

Status:
🔒 STABLE — AUTHORITY ESTABLISHED

This document records the **current, authoritative architectural state**
of HVACgooee.

It exists to eliminate ambiguity about:
- where truth lives
- what is frozen
- what may evolve
- how domains interact

---

## 1. Architectural Phase

HVACgooee has transitioned from a **tool-era architecture** to a
**platform-era architecture**.

This transition is complete at the level of:
- project authority
- domain execution
- persistence
- runtime behaviour

Further work extends the platform; it does not redefine it.

---

## 2. Project Authority (RESOLVED)

### ProjectModelV3 is the single source of truth.

It owns:
- declared engineering intent
- derived engineering results
- explicit validity flags

It does **not**:
- calculate physics
- run engines
- infer validity
- manage workflow
- perform IO

Project state ambiguity present in v1/v2 no longer exists.

---

## 3. Runtime vs Disk (EXPLICIT)

Two kinds of state exist:

### Disk State (Authoritative)
- `project.json`
- project backups
- project archive / baseline

Disk state is complete, deterministic, and reloadable.

### Runtime State (Disposable)
- in-memory ProjectModel instance
- cached DTOs
- runner execution state
- GUI selections

Runtime state is a **buffer only**.

> Loading a project always clears runtime state.

This rule is mandatory.

---

## 4. Domain Engines (FROZEN VALUE)

The following domain implementations are considered **engine libraries**:

- Heat-loss engines
- Hydronics engines
- Physics / geometry / fabric logic

They are:
- deterministic
- stateless
- calculation-only

They do not:
- own project state
- access GUI
- persist data
- decide validity

Existing engines are **valuable and retained**.
They are consumed via adapters only.

---

## 5. Orchestration (v3)

Execution order is owned by **runners / controllers**.

Runners:
- build input DTOs from ProjectModelV3
- invoke frozen engines
- receive result DTOs
- write results back to ProjectModelV3
- explicitly flip validity flags

No domain auto-runs.
No engine runs implicitly.
No GUI action triggers physics unless explicitly requested.

---

## 6. GUI Role (OBSERVER + INTENT EDITOR)

The GUI:
- edits declared intent only
- observes project state
- requests explicit runs

The GUI does **not**:
- perform calculations
- infer validity
- manage persistence logic
- retain authority over state

---

## 7. Persistence Model (LOCKED)

- Projects are saved as **full snapshots**
- No partial updates
- No delta files
- No journaling

Safety is provided by:
- automatic backups
- explicit archive / baseline snapshots

Cleanup (pruning) is always user-initiated.

---

## 8. Heat-Loss Status (RESOLVED)

Heat-loss operates under a formal domain contract:

- deterministic
- stateless
- explicitly executed
- project-agnostic

Heat-loss ambiguity present in earlier implementations has been removed.

The heat-loss engine is now:
> a service under orchestration, not a self-running subsystem.

---

## 9. Legacy Code Status

Directories representing v1/v2 behaviour are:

- retained
- frozen
- treated as engine libraries or import sources

They must not regain authority.

All new architectural work targets:
- Project Core v3
- IO v3
- Orchestration v3
- GUI observer wiring

---

## 10. Architectural Invariants (LOCKED)

- Projects decide; engines calculate
- Validity is explicit, never inferred
- Runtime state is disposable
- Disk state is authoritative
- Physics never runs by accident
- Clearing the buffer restores truth

---

## Closing Statement

HVACgooee now has a stable architectural spine.

Future work adds capability, not authority.
Refactoring improves clarity, not ownership.

If something feels ambiguous, it is a violation of this document.

🔒 END OF ARCHITECTURE STATUS
