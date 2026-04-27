# HVACgooee — EURIKA Bootstrap

**Status:** FROZEN
**Scope:** First end-to-end authoritative HVAC pipeline

---

## Overview

This bootstrap defines the first **fully coherent system state**.

It proves that HVACgooee:

* Separates intent from physics correctly
* Executes deterministically
* Commits results explicitly
* Maintains strict authority boundaries

From this point onward:

> **New features are added above this layer, not inside it.**

---

## Canonical Pipeline (LOCKED)

```id="pipeline1"
project.json
↓
ProjectFactoryV3
↓
ProjectState (authoritative)
↓
Construction Resolution
↓
HeatLossRunnerV3
↓
Qt (W)
```

Everything beyond this point must **build on top**, not reach inside.

---

## What Is Proven

### 1. Project Assembly — v3

* `ProjectFactoryV3` is the sole authority for:

  * project metadata
  * environment inputs
  * room geometry
  * templates
  * deterministic surface generation

Factories:

* assemble **intent only**
* perform **no physics**
* perform **no validation inference**

All project objects are deterministic after load.

---

### 2. Construction Resolution — v2

* Construction presets resolve to:

  * `ConstructionUValueResultDTO`

Resolution is:

* explicit
* registry-controlled
* surface-class keyed

Results:

* committed once
* stored in `ProjectState`
* never recomputed implicitly

---

### 3. ProjectState Authority

* `ProjectState` is the single source of truth

Engines:

* read only
* never mutate

GUI:

* observes only
* never decides

Validity is:

* explicit
* never inferred

---

### 4. Heat-Loss Engine — v3

`HeatLossRunnerV3` is:

* pure
* deterministic
* side-effect free

It consumes:

* constructions
* surfaces
* environment temperatures

It produces:

* a single authoritative result (Qt, W)

It does **not**:

* mutate state
* set validity
* import GUI
* import hydronics

---

### 5. Orchestration Contract

Execution is coordinated by headless orchestration:

* sequences engines
* commits results explicitly
* contains no physics

Engines remain unaware of orchestration.

---

## What Is Explicitly Not Included

The following are **intentionally excluded**:

* Ventilation / infiltration losses
* Dynamic fabric (Y-values)
* Comfort models (Tai, operative temperature)
* Solar / orientation / shading
* GUI authority
* Hydronic coupling

These are future layers built above this bootstrap.

---

## Engineering Semantics

* **Ti** — internal design temperature (steady-state, authoritative)
* **Te** — external design temperature
* **Tai / comfort models** — deferred to later phases

No ambiguity exists at this level.

---

## Why This Matters

This bootstrap demonstrates that the system:

* is deterministic
* is auditable
* separates concerns correctly
* scales without architectural refactor
* preserves traditional methods without locking them in

It establishes a stable base for:

* GUI development
* additional physics layers
* validation against real-world examples

---

## Extension Rule

From this point onward:

* No modification of locked behaviour
* No widening of contracts
* No implicit coupling

If a change requires breaking these rules:

→ a new bootstrap must be created

---

## Status

**EURIKA is frozen.**

This document is an architectural milestone and must be read before modifying core systems.

---

## Commit Reference (Recommended)

```bash id="commit1"
git add BOOTSTRAP_EURIKA.md
git commit -m "EURIKA bootstrap: first end-to-end authoritative HVAC pipeline"
git tag -a eurika-v1 -m "EURIKA freeze"
```

---

*This is the point where the system becomes real.*
# HVACgooee — EURIKA Bootstrap

**Status:** FROZEN
**Scope:** First end-to-end authoritative HVAC pipeline

---

## Overview

This bootstrap defines the first **fully coherent system state**.

It proves that HVACgooee:

* Separates intent from physics correctly
* Executes deterministically
* Commits results explicitly
* Maintains strict authority boundaries

From this point onward:

> **New features are added above this layer, not inside it.**

---

## Canonical Pipeline (LOCKED)

```id="pipeline1"
project.json
↓
ProjectFactoryV3
↓
ProjectState (authoritative)
↓
Construction Resolution
↓
HeatLossRunnerV3
↓
Qt (W)
```

Everything beyond this point must **build on top**, not reach inside.

---

## What Is Proven

### 1. Project Assembly — v3

* `ProjectFactoryV3` is the sole authority for:

  * project metadata
  * environment inputs
  * room geometry
  * templates
  * deterministic surface generation

Factories:

* assemble **intent only**
* perform **no physics**
* perform **no validation inference**

All project objects are deterministic after load.

---

### 2. Construction Resolution — v2

* Construction presets resolve to:

  * `ConstructionUValueResultDTO`

Resolution is:

* explicit
* registry-controlled
* surface-class keyed

Results:

* committed once
* stored in `ProjectState`
* never recomputed implicitly

---

### 3. ProjectState Authority

* `ProjectState` is the single source of truth

Engines:

* read only
* never mutate

GUI:

* observes only
* never decides

Validity is:

* explicit
* never inferred

---

### 4. Heat-Loss Engine — v3

`HeatLossRunnerV3` is:

* pure
* deterministic
* side-effect free

It consumes:

* constructions
* surfaces
* environment temperatures

It produces:

* a single authoritative result (Qt, W)

It does **not**:

* mutate state
* set validity
* import GUI
* import hydronics

---

### 5. Orchestration Contract

Execution is coordinated by headless orchestration:

* sequences engines
* commits results explicitly
* contains no physics

Engines remain unaware of orchestration.

---

## What Is Explicitly Not Included

The following are **intentionally excluded**:

* Ventilation / infiltration losses
* Dynamic fabric (Y-values)
* Comfort models (Tai, operative temperature)
* Solar / orientation / shading
* GUI authority
* Hydronic coupling

These are future layers built above this bootstrap.

---

## Engineering Semantics

* **Ti** — internal design temperature (steady-state, authoritative)
* **Te** — external design temperature
* **Tai / comfort models** — deferred to later phases

No ambiguity exists at this level.

---

## Why This Matters

This bootstrap demonstrates that the system:

* is deterministic
* is auditable
* separates concerns correctly
* scales without architectural refactor
* preserves traditional methods without locking them in

It establishes a stable base for:

* GUI development
* additional physics layers
* validation against real-world examples

---

## Extension Rule

From this point onward:

* No modification of locked behaviour
* No widening of contracts
* No implicit coupling

If a change requires breaking these rules:

→ a new bootstrap must be created

---

## Status

**EURIKA is frozen.**

This document is an architectural milestone and must be read before modifying core systems.

---

## Commit Reference (Recommended)

```bash id="commit1"
git add BOOTSTRAP_EURIKA.md
git commit -m "EURIKA bootstrap: first end-to-end authoritative HVAC pipeline"
git tag -a eurika-v1 -m "EURIKA freeze"
```

---

*This is the point where the system becomes real.*
