# HVACgooee

HVACgooee is an open-source HVAC engineering platform focused on
**deterministic heat-loss and hydronic sizing**, with strict architectural
separation between:

- design intent
- physics engines
- orchestration
- project authority

This repository contains a **frozen hydronics + heat-loss baseline**
preserved as an architectural and engineering reference.

---

## 🚨 Project Status — FROZEN BASELINE

**Hydronics and Heat-Loss are frozen.**

The `hydro-frozen-v1` branch (tag: `v1-hydronics-frozen`) represents a
completed and defensible implementation of:

- steady-state fabric heat-loss
- explicit heat-loss payloads
- deterministic hydronic physics
- pipe sizing and pressure loss
- radiator / emitter sizing
- explicit user oversizing intent (applied once)

No new features or refactors will be added to this baseline.

All further development continues in **Project Core v3** and later branches,
with an explicit ProjectModel, validators, and orchestration layer.

This freeze is intentional.

---

## What This Repository Is

✔ A **reference implementation**
✔ A **physics-correct baseline**
✔ A **known-good hydronics engine**
✔ A **foundation for future platform work**

## What This Repository Is Not

✘ A finished product
✘ A workflow engine
✘ A GUI-driven application
✘ A dynamic simulation tool

---

## Architectural Principles (NON-NEGOTIABLE)

HVACgooee enforces:

- **Explicit design intent**
- **Pure physics engines**
- **No hidden coupling**
- **No implicit recalculation**
- **No GUI-owned state**

Oversizing is applied **exactly once** at the
heat-loss → hydronics boundary.

Physics engines:

- consume DTOs
- emit result DTOs
- never store state
- never mutate project models

---

## Repository Structure

Authoritative, frozen code lives under:

- `HVAC/` — heat-loss and hydronic physics engines (frozen)

Other directories at the repository root represent historical,
experimental, or local working context and are intentionally
non-authoritative.
