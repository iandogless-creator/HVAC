# HVACgooee

**HVACgooee** is an open-source, deterministic HVAC calculation project.

It is being built to expose the engineering route behind HVAC decisions: inputs, assumptions, physics, intermediate values, and results. The aim is not to hide calculations behind opaque software behaviour, but to make the calculation path inspectable, repeatable, and teachable.

> Current development state: see `CURRENT_STATE.md`.
>
> Current active code path: see `CODE_MAP.md`.
>
> Architectural contracts: see `ARCHITECTURE_FREEZES.md` and `FREEZE_INDEX.md`.
>
> Engineering caveats and design stance: see `CAVEATS.md`.
>
> Older documents are retained for project history and may not describe the active code path.

---

## Current Focus

The current active development area is:

```text
Hydronics Phase H — proportioning / return-arrangement evidence
```

Current hydronics work includes:

- Basic PS first-pass sizing / handoff evidence
- shared Haaland / Colebrook friction calculation core
- Colebrook-backed route pressure evidence
- Local K section pressure preview
- F&R / F+RR return arrangement comparison
- reverse-return added-length basis modes
- accepted return-arrangement design basis
- chosen-basis Proportioned tab evidence

This is still a preview and evidence phase.

It does **not** yet produce:

- pump selection
- valve selection
- final balancing
- final pipe resizing
- final installation-ready hydraulic output

---

## Core Model

Heat loss is expressed explicitly:

```text
Qf = A × U × ΔT
```

Where:

- `A` = area
- `U` = thermal transmittance
- `ΔT` = temperature difference

Hydronic pressure evidence is likewise intended to be explicit:

```text
flow → velocity → Reynolds number → friction factor → Δp/m → section Δp → route Δp
```

Where appropriate, HVACgooee uses recognised hydraulic methods such as Haaland approximation, Colebrook-White friction calculation, and Darcy-Weisbach pressure loss.

---

## System Structure

HVACgooee separates authority, intent, calculation, and display.

High-level authority boundaries:

- **ProjectState** owns project intent and committed state.
- **Topology** defines relationships such as rooms, surfaces, adjacency, legs, sublegs, and sections.
- **Constructions** define fabric performance such as U-values.
- **Engines / runners** perform deterministic calculation.
- **Controllers** own execution policy and result commits.
- **Adapters** project state into display rows and forward user intent.
- **GUI panels** observe and emit intent only.

The project avoids:

- hidden calculations
- implicit state repair
- GUI-owned engineering authority
- silent recalculation
- black-box result paths

---

## What This Is

HVACgooee is:

- a deterministic engineering calculation system
- a topology-driven HVAC modelling project
- an educational and audit-friendly calculation route
- an open-source foundation for future HVAC tools
- a project that keeps physics, assumptions, and design basis visible

## What This Is Not

HVACgooee is not:

- a quick calculator
- a GUI-first spreadsheet clone
- a black-box simulation package
- a substitute for competent engineering judgement
- a final design authority before the relevant phase is complete

---

## Project Status

Current broad status:

| Area | Status |
|---|---|
| Project model | Authoritative active model |
| Heat-loss engine | Operational / stable enough to pause |
| Heat-loss GUI v3 | Active-stable / observer-first |
| Construction assignment | Active-stable |
| Wall Wizard / opening schedule | Active-stable runtime path, not yet heat-loss physics authority |
| Hydronics | Active development — Phase H preview/evidence |
| Hydronic final design | Not yet active |
| Pump / valve / final balancing | Not yet implemented |

---

## Design Principles

Locked project principles include:

- engines are pure and deterministic
- ProjectState is the single engineering state authority
- GUI never decides engineering truth
- previews are evidence, not final output
- user design basis remains authoritative
- physics should be traceable
- assumptions should be visible
- published tables are respected as guidance, not treated as natural law

In short:

```text
Intent is explicit.
Physics is traceable.
Preview is not final.
The designer remains authoritative.
```

---

## Repository Structure

High-level structure:

```text
HVAC/
├── core/
├── topology/
├── heatloss/
├── heatloss_v3/
├── hydronics/
├── hydronics_v3/
├── gui_v3/
├── project/
├── dev/
└── examples/
```

Important root documents:

```text
README.md
CURRENT_STATE.md
CODE_MAP.md
ARCHITECTURE_FREEZES.md
FREEZE_INDEX.md
CAVEATS.md
```

---

## Development Notes

This repository contains active development work, historical notes, and parked subsystems.

When unsure, prefer the current authority chain:

```text
CURRENT_STATE.md → CODE_MAP.md → ARCHITECTURE_FREEZES.md → FREEZE_INDEX.md
```

Historical documents may still be useful, but they should not override the current state or architecture freezes.

---

## Licensing

HVACgooee core is released under **GPLv3**.

---

## Author

Ian Allison

---

*Correctness over convenience. Architecture over shortcuts.*
