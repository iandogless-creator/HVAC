======================================================================
HVACgooee — Phase F-A Bootstrap
Environment → Heat-Loss Enrichment
======================================================================

Phase: GUI v3
Sub-Phase: F-A
Status: BOOTSTRAP (not yet frozen)

Purpose

Introduce read-only enrichment from Environment into Heat-Loss
without violating GUI authority boundaries or re-introducing hidden coupling.

This phase makes environment intent visible and consumable by Heat-Loss
while keeping ProjectState as the sole authority.

Problem Being Solved

At present:

Environment exists as authoritative project intent

Heat-Loss can run, but:

ΔT reference logic is implicit

Design temperatures are not surfaced clearly

Heat-Loss readiness lacks environmental context

Phase F-A resolves this by explicitly wiring Environment → Heat-Loss
in a one-directional, read-only manner.

Canonical Data Flow
ProjectState
   └── environment (authoritative)
         ├── inside_design_temperature_c
         ├── outside_design_temperature_c
         ├── method / reference metadata
         └── notes (optional)

GUI Adapters (read-only)
   ├── EnvironmentPanelAdapter
   └── HeatLossPanelAdapter
            └── derives ΔT (presentation only)


No GUI panel may compute or persist values.

Scope (Phase F-A)
INCLUDED

Heat-Loss panel may:

Display inside / outside design temperatures

Display derived ΔT as presentation only

Use environment presence to refine readiness status

Heat-Loss worksheet header may show:

Design temperatures

ΔT reference source (environment)

EXPLICITLY EXCLUDED

No mutation of ProjectState

No defaulting or inference inside GUI

No calculations in adapters beyond subtraction for display

No persistence changes

No construction / U-value interaction

Authority Rules (LOCKED)

Environment owns temperatures

GUI never invents or stores them

Heat-Loss does not re-own ΔT

ΔT is derived only for display

Adapters are read-only

No setters

No fallback logic

No cross-panel imports

Panels never talk to each other

Adapters read ProjectState only

Violation of any rule invalidates Phase F-A.

Implementation Targets
1. HeatLossPanelAdapter

Add:

Environment presence check

ΔT derivation for UI display

Clear readiness messaging:

“Waiting for environment data”

“Environment resolved”

2. HeatLossWorksheetAdapter

Optional (Phase F-A allowed):

Header annotation:

Inside / Outside temperatures

ΔT shown as reference only

3. Education Panel (Optional)

Contextual note:

Why ΔT is derived

Why values are read-only

Classical vs modern practice (non-authoritative)

Non-Goals

No new DTOs unless strictly necessary

No refactor of ProjectState

No change to Heat-Loss engine inputs

No attempt to “help the user” by guessing values

Freeze Conditions (to mark Phase F-A COMPLETE)

All must be true:

Heat-Loss panel clearly reflects environment data

No GUI mutation paths added

ΔT shown consistently and correctly

Code remains boring and obvious

No regressions in GUI v3 Phase E/F behaviour

Only then may Phase F-A be frozen.

Next Phases (Locked Order)

Phase F-A — Environment → Heat-Loss enrichment ← current

Phase F-B — UX / readiness messaging polish

Phase F-C — GUI persistence refinement

Phase C (Construction) — editable construction definitions

Phase D (UVP) — authoritative U-value resolution

Environment → Heat-Loss enrichment SHALL be passed via a read-only DTO produced by the GUI context.
Direct reads from ProjectState inside Heat-Loss adapters are forbidden.

Construction defines what it is.
UVP defines what it does thermally.
Heat-Loss defines what it costs.
