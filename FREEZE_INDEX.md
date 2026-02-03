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

Bug fixes are allowed.
Architectural changes are not.

---

## 🧠 Project Core

### Project Assembly — v3
**Status:** FROZEN  
**Path:** `HVAC/project/`

**Authority**
- Defines what a project *is*
- Owns ProjectState lifecycle
- Owns edit vs calculation mode

**Rules**
- No GUI imports
- No physics
- No heuristics
- Factories assemble intent only

---

## 🔥 Heat-Loss Engine — v1
**Status:** FROZEN  
**Path:** `HVAC/heatloss/`

**Authority**
- Fabric + ventilation + ΔT → heat loss
- Deterministic, testable physics

**Rules**
- No GUI imports
- No persistence
- No mutation of ProjectState

---

## 🚰 Hydronics Engine — v3
**Status:** FROZEN  
**Path:** `HVAC/hydronics/`

**Authority**
- Flow, pressure, balancing, pumps
- Topology + physics only

**Rules**
- No GUI imports
- No heat-loss imports
- DTOs only across boundaries

---

## 🧱 Constructions & Fabric
**Status:** FROZEN  
**Path:** `HVAC/constructions/`

**Authority**
- Construction intent
- Fabric resolution
- U-value calculation

**Rules**
- GUI edits intent only
- Engines resolve physics
- Results immutable once committed

---

## 🖥️ GUI v3 — Core Shell
**Status:** ACTIVE (Phase F)
**Path:** `HVAC/gui_v3/`

### Frozen Components
- Docking model (Qt native)
- Adapter → DTO → Panel architecture
- No GUI → ProjectState mutation
- saveState / restoreState persistence only

### Active Components
- Panel population
- Visual density refinement
- Controller wiring (future phase)

---

## 📊 GUI v3 — Panels

### Heat-Loss Panel
**Status:** ACTIVE (Phase E → F)
**Bootstrap:** `HVAC/gui_v3/panels/Heat-Loss Panel (GUI v3).md`

### Environment Panel
**Status:** STABLE

### Project Panel
**Status:** STABLE

### Hydronics Schematic Panel
**Status:** FROZEN (Phase D)
- Read-only schematic
- DTO-driven
- No authority

---

## 🎨 GUI Theme & Accent System
**Status:** ACTIVE  
**Path:** `HVAC/gui_v3/common/`

**Rules**
- Accent colours only
- No semantic meaning
- Installation-level preference
- Blue de-emphasised by design

---

## 🚫 Explicit Non-Goals (Global)

The following are explicitly forbidden everywhere:

• GUI performing calculations  
• Panels mutating ProjectState  
• Implicit recalculation  
• Hidden authority  
• Cross-engine imports  
• GUI heuristics  

---

## 📍 Next Planned Work

• Heat-Loss panel population (widgets & layout)
• Controller layer (engine execution)
• Observer-only fabric inspection
• Accent scheme selector panel
• Dock coordination review *after* population

---

**Authoritative owner:** Ian Allison  
**Repository:** HVACgooee  
**Licence:** GPL-v3 (core)

Status: **CANONICAL**
