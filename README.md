# HVACgooee

**HVACgooee** is an open, engineering-grade HVAC calculation framework written in Python.
# HVACgooee (Workspace)

⚠ **Important**

Active development happens in the **HVAC** repository:

https://github.com/iandogless-creator/HVAC

This repository exists only as a local workspace shell.

It is designed to preserve and modernise traditional CIBSE-era methods
(U-values, steady-state heat-loss, hydronic sizing) while providing a
clean, modular foundation for future extensions
(dynamic fabric, comfort models, BIM, and advanced GUI workflows).

This repository contains the **authoritative core engine** and
reference orchestration for HVACgooee.

---
## Project Foundations

Before modifying core systems, please read:

- [EURIKA Bootstrap](BOOTSTRAP_EURIKA.md) — architectural authority
- [Design Philosophy](DESIGN_PHILOSOPHY.md) — how decisions are made
- [Caveats](CAVEATS.md) — clarifications and intent

## Project Status

**Active — Core Engines Stable**

- Heat-Loss v3: **Operational**
- Hydronics v3: **Frozen**
- Project Model v3: **Authoritative**
- GUI: Under active redevelopment (`gui_v3`)

This repository prioritises **correctness, clarity, and architectural
stability** over rapid UI development.

---
## Architectural Milestones

HVACgooee uses explicit architectural bootstraps to lock intent.

- **v1.0.0 — EURIKA**
  First fully working end-to-end authoritative pipeline
  See: `BOOTSTRAP_EURIKA.md`

## Architecture & Authority

HVACgooee uses explicit architectural freezes to prevent accidental
coupling between GUI, state, and physics.

The canonical authority rules, execution contracts, and frozen boundaries
are defined here:

➡️ **ARCHITECTURE_FREEZES.md**

All contributors are expected to respect these freezes.


## Design Philosophy

HVACgooee is intentionally **fine-grained and modular**.

Each engineering concept is isolated into a small, single-purpose module.
This increases the total file count, but dramatically improves:

- Traceability of calculations
- Long-term maintainability
- Testability of individual engineering steps
- Resistance to accidental architectural coupling

Large file counts are expected and intentional.

---

## Core Principles (Locked)

- **Engines are pure**
  - No GUI imports
  - No side effects
  - No implicit state
- **ProjectState is the single authority**
- **Factories assemble intent; runners compute**
- **GUI observes, never decides**
- **Physics is explicit, never inferred**

These rules are enforced across all v3 components.

---

## Repository Structure (High-Level)

HVAC/
├── constructions/ # Fabric intent, registries, U-value resolution
├── heatloss_v3/ # Pure heat-loss engine (Qt)
├── hydronics/ # Hydronic sizing & balancing (v3 frozen)
├── project_v3/ # Project schema & factory
├── orchestration/ # Headless runners (end-to-end execution)
├── project/ # ProjectState (authoritative runtime state)
├── gui_v3/ # Next-generation GUI (observer-only)
└── tests/ # Reference and regression tests


Deprecated or exploratory code is retained for reference but clearly marked.

---

## What HVACgooee Is (and Is Not)

**It is:**
- A professional calculation engine
- A learning and preservation tool for traditional HVAC methods
- A modular platform for future tooling

**It is not:**
- A quick calculator
- A monolithic application
- A GUI-first project

---

## Licensing

HVACgooee core is released under **GPLv3**.

This ensures:
- Long-term openness of the engineering core
- Freedom to build proprietary or commercial tools **around** the core
  via plugins or external interfaces

See `LICENSE` for details.

---

## Roadmap (Short)

- End-to-end v1 reference projects
- GUI v3 (read-only first, then intent editors)
- Formal validation examples (CIBSE-style)
- Documentation freeze for v1 core

---

## Author

HVACgooee is authored and maintained by **Ian**
(Open-source engineer, HVAC systems designer)

---

*This project favours correctness over speed, and architecture over convenience.*
