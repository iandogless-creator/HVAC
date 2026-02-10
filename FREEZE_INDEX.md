# ======================================================================
# HVACgooee — Repository FREEZE INDEX
# ======================================================================
#
# This document defines all frozen subsystems, their authority,
# and their current lifecycle phase.
#
# It is NOT a README.
# It is NOT user documentation.
#
# It is the architectural spine of the repository.
#
# Location: repository root
# Status: CANONICAL
# ======================================================================


## Meaning of "Frozen"

A frozen subsystem:

• Has a locked public contract
• Has a fixed authority boundary
• Must not be refactored without an explicit new bootstrap
• May be *used*, but not *restructured*

Refactors that change **public shape, authority, or data ownership**
constitute restructuring.

Bug fixes are allowed.
Architectural changes are not.

---

## Authority Topology (Global)

HVACgooee follows a strict execution topology:

GUI → Adapter → Controller → Runner → Result
Result → ProjectState (commit only)

Reverse flows are forbidden.

---

## 🧠 Project Core — v3
**Status:** FROZEN
**Path:** `HVAC/project/`

### Authority
- Defines what a project *is*
- Owns ProjectState lifecycle
- Owns edit vs calculation mode
- Owns identity (rooms, elements, surfaces)

### Rules
- No GUI imports
- No physics
- No heuristics
- Factories assemble **intent only**
- State mutation only via controllers

---

## 🔥 Heat-Loss Engine — v1
**Status:** FROZEN
**Path:** `HVAC/heatloss/`, `HVAC/heatloss_v3/`

### Authority
- Fabric + ventilation + ΔT → heat loss
- Deterministic, testable physics
- Pure execution via runners

### Rules
- No GUI imports
- No persistence
- No ProjectState mutation
- No validation inference
- Explicit inputs, explicit outputs only

---

## 🚰 Hydronics Engine — v3
**Status:** FROZEN
**Path:** `HVAC/hydronics/`, `HVAC/hydronics_v3/`

### Authority
- Flow, pressure, balancing, pumps
- Network topology + physics only

### Rules
- No GUI imports
- No heat-loss imports
- DTOs only across boundaries
- No persistence
- No heuristics

---

## 🧱 Constructions & Fabric
**Status:** FROZEN
**Path:** `HVAC/constructions/`

### Authority
- Construction intent
- Fabric resolution
- U-value calculation

### Rules
- GUI edits **intent only**
- Engines resolve physics
- Results immutable once committed
- No area or ΔT responsibility (fabric ≠ heat-loss)

---

## 📊 Heat-Loss Overrides — v1
**Status:** FROZEN
**Owner:** `HeatLossStateV1`

### Definition
Overrides represent **user intent**, not results.

### Rules
- Overrides may shadow derived inputs
- Overrides are sparse and optional
- Clearing overrides removes intent
- Any override change invalidates results
- Overrides never store calculated values

### Forbidden
❌ results overwriting overrides
❌ implicit override creation
❌ override-driven mutation

---

## 🖥️ GUI v3 — Core Shell
**Status:** ACTIVE (Phase F)
**Path:** `HVAC/gui_v3/`

### Frozen Components
- Adapter → DTO → Panel architecture
- Observer-only ProjectState access
- saveState / restoreState persistence
- No GUI → ProjectState mutation

### Active Components
- Panel population
- Visual density refinement
- Controller wiring (Phase H+)

---

## 📋 GUI v3 — Panels

### Heat-Loss Panel
**Status:** ACTIVE (Phase E → H)
**Role:** Worksheet + observer substrate
**Authority:** NONE

- Displays derived, overridden, and committed values
- Emits override intent
- Emits run intent
- Never commits results
- Never performs calculations

### Environment Panel
**Status:** STABLE

### Project Panel
**Status:** STABLE

### Hydronics Schematic Panel
**Status:** FROZEN (Phase D)

- Read-only
- DTO-driven
- No authority
- No selection coupling

---

## 🎨 GUI Theme & Accent System
**Status:** ACTIVE
**Path:** `HVAC/gui_v3/common/`

### Rules
- Accent colours only
- No semantic meaning
- Installation-level preference
- Blue intentionally de-emphasised

---

## 🚫 Explicit Global Non-Goals

The following are forbidden everywhere:

• GUI performing calculations
• Panels mutating ProjectState
• Implicit recalculation
• Hidden authority
• Cross-engine imports
• GUI heuristics

Violations are architectural bugs.

---

## 🔐 Runner Purity Contract
**Status:** FROZEN
**Scope:** `*_runner_v*`

### Rules
- Pure functions
- No mutation of inputs
- No caching
- No persistence
- No GUI access
- Explicit return values only

This enables:
- reproducibility
- testing
- parallelism
- future acceleration

---

## 🆔 Identity & Addressing — v1
**Status:** FROZEN

### Identifiers
- `room_id` — stable project identifier
- `element_id` — stable within room
- `surface_class` — semantic classification

### Rules
- Overrides and results use identity
- Geometry may change shape, IDs persist
- Execution relies on identity, not GUI selection

---

## Phase H — Heat-Loss Execution & GUI Observer Substrate
**Status:** FROZEN

### Scope
- ProjectState D.2 authority
- HeatLossStateV1 + overrides
- HeatLossRunnerV3 (pure)
- HeatLossControllerV4
- GUI v3 Heat-Loss worksheet (observer-only)

---

## 📍 Next Planned Work (NOT FROZEN)

• Heat-Loss panel visual population
• Controller UX affordances
• Observer-only fabric inspection
• Accent scheme selector
• Dock coordination review *after* population

---

## Change Policy

Any change that violates a freeze must:

• be deliberate
• be documented
• update this file
• justify architectural impact

Silent violations are bugs.

---

**Authoritative owner:** Ian Allison
**Repository:** HVACgooee
**Licence:** GPL-v3 (core)

Status: **CANONICAL**

# ======================================================================
# END OF DOCUMENT
# ======================================================================
