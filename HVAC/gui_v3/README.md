# ======================================================================
# HVACgooee — GUI v3
# Mode: Observer (Read-Only)
# Status: FROZEN (Architecture)
# ======================================================================

Audience
--------
Developers, contributors, future maintainers.

This document defines the **canonical contract** for GUI v3.
All implementation must conform to this document unless a new
bootstrap is explicitly written and frozen.

---

## Purpose

GUI v3 exists to **observe authoritative engineering state**, not to
create, mutate, infer, or calculate it.

GUI v3 is deliberately non-authoritative.

It reflects *truth created elsewhere*.

If the GUI appears to make decisions, it is violating this contract.

---

## Authority Model (LOCKED)

### GUI v3 MAY:

• Read `ProjectState`
• Read immutable configuration objects
• Display committed engine results
• Display explanatory and educational information
• Persist **installation-level UI preferences**

### GUI v3 MUST NOT:

• Mutate `ProjectState`
• Create or edit engineering intent
• Trigger engines or calculations
• Infer validity or correctness
• Invent defaults
• Import engines or factories
• Auto-run any process

All engineering authority exists **outside** the GUI.

---

## Observer Panels (LOCKED)

GUI v3 is composed of **optional, detachable observer panels**.

No panel is required to understand or operate a project.

Panels observe truth; they do not create it.

---

### ProjectPanel

**Purpose:**  
Project identity and execution state.

**Displays:**
• Project metadata
• Engine run status flags

**Does NOT display:**
• Engineering results
• Derived values

---

### EnvironmentPanel

**Purpose:**  
Environmental boundary conditions.

**Displays:**
• Outdoor design temperature (To)
• Project default geometry height

**Does NOT:**
• Perform oversizing
• Infer defaults
• Display results

---

### SystemSummaryPanel

**Purpose:**  
System-level engineering results (read-only).

**Displays:**
• Total Qt
• Boiler capacity
• Boiler oversize percentage
• Aggregate emitter oversize percentage
• Flow / return temperatures
• Hydronics run status

This panel replaces legacy “global values” views.

---

### HydronicsSchematicPanel (v0)

**Purpose:**  
Read-only visualisation of hydronic topology.

**Displays:**
• Nodes
• Paths
• Flow / pressure indicators

**Explicitly FORBIDDEN:**
• Editing
• Interaction
• Authority
• Hit-testing
• Selection logic

---

### EducationPanel

**Purpose:**  
Explanatory mirror of engineering logic.

**Displays:**
• Classical formulae
• Substituted values
• Engineering explanations

**Driven by:**
• Hover context only

**Performs:**
• No calculations
• No inference
• No validation

---

## Interaction Rules (LOCKED)

• Hover → transient explanation (EducationPanel)
• Selection → persistent observation only

These roles **must never merge**.

If a panel feels “interactive”, it is doing too much.

---

## Configuration Layers (LOCKED)

### 1. Application Defaults
• Shipped with code
• Immutable at runtime

### 2. Installation Configuration
• Theme
• Accent scheme
• Panel layout & persistence
• UI behaviour preferences

Stored per installation.  
Never stored in `ProjectState`.

### 3. ProjectState
• Engineering intent
• Engineering results
• Portable
• Authoritative

No GUI preferences may leak into `ProjectState`.

---

## Overrides (LOCKED)

Where defaults and overrides exist (e.g. geometry height):

• The **effective value** is always displayed
• The **source** is indicated textually:
  `(default)` or `(override)`

Styling:
• Italic
• Muted
• Non-semantic

No icons, colours, warnings, or emphasis.

Overrides represent **intent**, not error.

---

## Styling & Presentation (LOCKED)

• GUI chrome (window, docks, titles) remains neutral
• Accent styling applies **only to panel surfaces**
• Panels must opt-in to styling explicitly
• No styling may imply correctness, error, or status

### Deferred (Intent Only)

• Light / dark contrast modes
• Advanced panel surface backgrounds
• Inner panel grouping surfaces

These are **explicitly deferred** and must not be partially implemented.

```text
Future: optional contrast modes (light/dark) — intentionally deferred
