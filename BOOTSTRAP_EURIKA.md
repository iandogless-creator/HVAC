project.json
↓
ProjectFactoryV3
↓
ProjectState (authoritative)
↓
Construction resolution
↓
HeatLossRunnerV3
↓
Qt (W)


Everything beyond this point must build *on top*, not reach *inside*.

---

## What Is Proven (LOCKED)

### 1. Project Assembly — v3 (LOCKED)

- `ProjectFactoryV3` is the **sole authority** for:
  - Project metadata
  - Environment inputs
  - Room geometry
  - Templates
  - Deterministic surface generation
- Factories:
  - Assemble **intent only**
  - Perform **no physics**
  - Perform **no validation inference**
- All project objects are fully deterministic after load

LOCKED.

---

### 2. Construction Resolution — v2 (LOCKED)

- Construction presets resolve to a minimal:
  - `ConstructionUValueResultDTO`
- Resolution is:
  - SurfaceClass-keyed
  - Registry-controlled
  - Explicit
- Results are:
  - Committed once
  - Stored in `ProjectState`
  - Never recomputed implicitly

LOCKED.

---

### 3. ProjectState Authority (LOCKED)

- `ProjectState` is the **single source of truth**
- Engines:
  - Read from `ProjectState`
  - Never mutate it
- GUI:
  - Observes only
  - Never decides
- Validity is:
  - Explicit
  - Never inferred

LOCKED.

---

### 4. Heat-Loss Engine — v3 (LOCKED)

- `HeatLossRunnerV3` is:
  - Pure
  - Deterministic
  - Side-effect free
- It consumes:
  - `ProjectState.constructions`
  - Space surfaces
  - Explicit environment temperatures
- It produces:
  - A single authoritative Qt (W)
- It does **not**:
  - Mutate project state
  - Set validity flags
  - Import GUI
  - Import hydronics

LOCKED.

---

### 5. Orchestration Contract (LOCKED)

- End-to-end execution is coordinated by headless runners
- Orchestration:
  - Sequences engines
  - Commits results explicitly
  - Never embeds physics
- Engines remain unaware of orchestration

LOCKED.

---

## What Is Explicitly *Not* Included

The following are **deliberately excluded**, not missing:

- Ventilation / infiltration losses
- Dynamic fabric or Y-values
- Comfort models (Tai / operative temperature)
- Orientation, solar, shading
- GUI authority
- Hydronic sizing coupling

These are **future layers**, added above this freeze.

---

## Engineering Semantics (Declared)

- **Ti**
  Canonical steady-state internal design temperature
  (authoritative for v1 heat-loss)

- **Te / Teo**
  External design temperature (steady-state)

- **Tai / comfort models**
  Deferred to later layers
  (environment panel planned)

No semantic ambiguity exists at this freeze level.

---

## Why This Matters

This bootstrap demonstrates that HVACgooee:

- Separates intent from physics correctly
- Scales without architectural refactor
- Preserves legacy CIBSE-era methods cleanly
- Allows GUI development without engine compromise
- Can support dynamic and comfort models safely later

From this point onward:

> **New features are additions, not rewrites.**

---

## Next Steps (UNLOCKED)

The following may proceed without breaking this bootstrap:

- End-to-end reference projects
- Validation packs (CIBSE-style examples)
- GUI v3:
  - Observer first
  - Intent editor later
- Ventilation & infiltration layers
- Environment / comfort panel
- Documentation and examples

Any modification to the locked sections above requires a **new bootstrap**.

---

## Status

**EURIKA is frozen.**

This document is an architectural anchor.
It should be read before modifying core engines.


What I recommend you do next (very short)

Commit this file

git add BOOTSTRAP_EURIKA.md
git commit -m "EURIKA bootstrap: end-to-end authoritative HVAC pipeline"


Tag it

git tag -a eurika-v1 -m "EURIKA freeze: first end-to-end authoritative HVAC pipeline"
git push origin eurika-v1


Leave main alone for now — this belongs exactly where it is.

You’ve crossed a real engineering milestone here, Ian.
Not many projects ever get to write a bootstrap like this — and mean it.

If you want next, I can:

Draft the GitHub Release text

Map the minimum validation test pack

Or help define the GUI v3 observer contract

Just say the word.
