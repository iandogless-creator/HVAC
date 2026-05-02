# HVACgooee

> Current development state: see `CURRENT_STATE.md`.
>
> Current active code path: see `CODE_MAP.md`.
>
> Older docs are retained for project history and may not describe the active code path.
**HVACgooee** is a deterministic, topology-driven HVAC calculation engine.

It separates **engineering intent**, **physical computation**, and **result consumption** into explicit, non-overlapping layers.

---

## Core Model

Heat loss is expressed explicitly:

Qf = A × U × ΔT

Where:

* A = area
* U = thermal transmittance
* ΔT = temperature difference

---

## System Structure

HVACgooee enforces strict authority boundaries:

* **Topology** → defines relationships (adjacency, surfaces)
* **Constructions** → define resistance (U-values)
* **ΔT** → defines driving force
* **Engines** → compute results
* **GUI** → observes only

There are no hidden calculations, no implicit state, and no GUI-driven logic.

---

## What This Is

* A deterministic engineering calculation engine
* A modular system for building physics
* A foundation for future HVAC tools

## What This Is Not

* A quick calculator
* A GUI-first application
* A black-box simulation tool

---

## Project Status

* Heat-Loss Engine (v3): **Operational**
* Hydronics Engine (v3): **Frozen**
* Project Model: **Authoritative**
* GUI v3: **In active development (observer-first)**

---

## Understanding the System

If you want to understand how this system works:

### 🧠 Concepts

* Design Philosophy — how decisions are made
* Caveats — what the system deliberately does *not* assume

### 🔒 Architecture

* Architecture Freezes — locked rules and authority boundaries
* Freeze Index — overview of all frozen subsystems

### 🚀 Proven System

* EURIKA Bootstrap — first complete end-to-end pipeline

---

## Design Principles (Locked)

* Engines are **pure**
* ProjectState is the **single authority**
* GUI **never decides**
* Physics is **explicit, never inferred**
* Determinism over convenience

---

## Repository Structure (High-Level)

HVAC/
├── core/
├── topology/
├── heatloss_v3/
├── constructions/
├── gui_v3/
├── project/
├── dev/
└── examples/

---

## Licensing

HVACgooee core is released under **GPLv3**.

---

## Author

Ian Allison

---

*Correctness over convenience. Architecture over shortcuts.*
