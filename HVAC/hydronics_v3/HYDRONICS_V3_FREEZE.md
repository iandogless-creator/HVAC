# HVACgooee — Hydronics v3 Freeze Notice

Status: 🔒 FROZEN  
Scope: Hydronics core (topology, physics, engines, DTOs)

---

## Purpose

This document records the formal freeze of the Hydronics v3 core.

Hydronics v3 represents a complete, first-principles implementation of
hydronic system modelling, sizing, balancing, and pump selection,
implemented as deterministic, GUI-independent Python engines.

The purpose of this freeze is to prevent further casual modification of
core hydronic physics and contracts, and to establish a stable foundation
for higher-level project, GUI, and reporting layers.

---

## What Is Frozen

The following are considered **locked** as of this freeze:

### 1. Governing Physics
- Darcy–Weisbach pressure loss
- Colebrook–White friction factor
- Explicit material roughness
- Explicit fluid properties
- Quadratic system curves
- First-principles pump curve intersection
- Power and efficiency calculations derived from physics

### 2. Core Architectural Contracts
- DTO-only data flow (DTO-in / DTO-out)
- No mutation of DTOs by engines
- No GUI, Qt, or ProjectState dependencies
- Deterministic execution
- No global state

### 3. Hydronics Engines
- Topology and leg structures
- Pressure-drop aggregation
- Index path discovery
- Balancing target declaration
- Valve authority checking
- Valve Kv sizing
- Iterative balancing refinement
- Pump duty selection
- Operating point determination
- Pump efficiency and power evaluation

### 4. Validation Philosophy
Hydronics v3 is validated against legacy UK hydronic practice
(HIVE / CIBSE era) using first-principles calculation.

Legacy tables are treated as **heuristic engineering artefacts**, not
authoritative numeric truth. Agreement within appropriate engineering
tolerances confirms correctness of scale, behaviour, and physical wiring.

Exact reproduction of legacy tables is neither expected nor required.

---

## What Is Explicitly Out of Scope

The following are **not** part of Hydronics v3 and must not be added here:

- GUI logic or widgets
- Project persistence or orchestration
- User interaction flows
- Reporting or document generation
- Domain policy decisions
- Commercial catalog data management

These belong to higher layers.

---

## Rules After Freeze

- Core hydronics code must not be modified without:
  - a new version designation (e.g. v4),
  - explicit justification,
  - and new validation coverage.

- Refactoring for style or convenience alone is not permitted.

- Bug fixes that alter physics or behaviour require version escalation.

---

## Rationale

Legacy hydronics tables were produced using hand calculation methods,
rounded intermediate values, and visual smoothing.
Hydronics v3 solves the governing equations directly and therefore
represents the most accurate solution achievable for declared inputs.

Remaining uncertainty arises from material properties and assumptions,
not from the calculation method.

---

## Summary

Hydronics v3 is complete.

It is architecturally stable, physically correct, and validated at the
appropriate engineering level.

Further development should proceed **above** this layer.

🔒 End of Hydronics v3
