======================================================================
HVACgooee — Phase II-A Freeze Note
Title: Fabric Authoring Navigation & U-Value Readiness
Status: FROZEN (CANONICAL)
Applies to: GUI v3 + ProjectState
Date: Monday 24 February 2026, 18:00 pm (UK)
======================================================================
1. Purpose of This Freeze

Phase II-A freezes the authoritative navigation and readiness contract for
fabric authoring in the heat-loss workflow.

This phase does not introduce physics, construction logic, or persistence.

It establishes:

A single unit of navigation: surface identity

A single path to U-Value authoring

A single readiness rule for missing / invalid U-Values

A single navigation authority (MainWindowV3)

This freeze exists to prevent:

parallel navigation models

panel-driven authority creep

readiness heuristics in the GUI

future circular dependencies

2. Scope (Exactly What Is Frozen)
2.1 In Scope

Surface-centric navigation model

Heat-Loss → Construction → U-Values flow

Signal contracts between panels

Readiness extension for U-Values

iter_fabric_surfaces() as a canonical API

Navigation wiring via MainWindowV3 only

2.2 Explicitly Out of Scope

Construction layer authoring

U-Value calculation engines

Fabric resolution engines

Persisted UI selection state

Hydronics coupling

Automatic surface creation

Anything in this list must not be added retroactively to Phase II-A.

3. Canonical Surface Identity (LOCKED)

A fabric surface is identified by a stable surface_id.

This identifier is the only unit of navigation and focus across the system.

The same surface_id flows through:

Heat-Loss worksheet rows

Construction panel focus

U-Values panel focus

Heat-loss readiness evaluation

There are no parallel identifiers:

no row IDs

no element indices

no panel-local aliases

Any new feature that introduces an alternative identity model
violates this freeze.

4. Authority Boundaries (LOCKED)
4.1 ProjectState

ProjectState is the single authority for:

Fabric intent

Resolved fabric surfaces

U-Value presence / validity

Heat-loss readiness evaluation

Rules:

Owns all readiness logic

Performs no GUI navigation

Readiness evaluation is non-mutating

Exposes fabric surfaces only via canonical iterators

4.2 GUI Panels

All GUI panels are:

Observers

Intent emitters

They must:

Never inspect ProjectState directly

Never evaluate readiness

Never open or raise other panels

Never infer missing data

4.3 Adapters

Adapters:

Translate ProjectState → UI state

Are read-only

Contain no business rules

4.4 MainWindowV3 (Navigation Hub)

MainWindowV3 is the only component allowed to:

Open

Raise

Focus

Route between docks

MainWindowV3 must not:

Evaluate readiness

Inspect fabric data

Contain heuristics

5. Phase II-A Surface Focus Model (LOCKED)
5.1 Source of Truth

The Heat-Loss Worksheet Adapter is the GUI source of surface selection.

It maps:

worksheet_row_index → surface_id

On row interaction, it emits navigation intent only.

It does not:

filter surfaces

infer participation

inspect U-Values

5.2 Context Propagation

Surface focus is propagated via GUI context only:

GuiProjectContext.set_uvp_focus(surface_id)

This is GUI-only state.

It does not mutate ProjectState.

Subscribers:

Construction Panel

U-Values Panel

6. Panel Responsibilities (FROZEN)
6.1 Heat-Loss Panel (HLP)

May:

Display worksheet rows

Track selected surface

Emit navigation intent

Signals:

open_construction_requested(surface_id | None)

open_uvalues_requested(surface_id | None)

Must not:

Inspect U-Values

Open docks

Evaluate readiness

6.2 Construction Panel

May:

Accept selected surface_id

Display construction placeholder state

Emit intent to author U-Values

Signals:

u_values_requested(surface_id | None)

Must not:

Calculate U-Values

Decide readiness

Open U-Values panel directly

6.3 U-Values Panel (UVP)

May:

Accept focused surface_id

Display / author thermal properties

Reflect missing or resolved state

Must not:

Navigate to other panels

Evaluate readiness

Open or raise docks

7. Navigation Wiring (CANONICAL)

All cross-panel navigation is wired only in MainWindowV3.

7.1 Required Handlers

_on_construction_focus_requested(surface_id)

_on_uvp_focus_requested(surface_id)

Responsibilities:

Raise appropriate dock

Apply surface focus via GUI context

7.2 Permitted Wiring

Heat-Loss Panel

open_construction_requested → _on_construction_focus_requested
open_uvalues_requested      → _on_uvp_focus_requested

Construction Panel

u_values_requested          → _on_uvp_focus_requested

No other wiring is permitted.

Any panel opening another panel directly
violates this freeze.

8. Heat-Loss Readiness — Phase II-A Extension (LOCKED)
8.1 Single Source of Readiness

All readiness evaluation flows through:

ProjectState.evaluate_heatloss_readiness()

This function:

Is non-mutating

Has no GUI knowledge

Produces explicit blocking reasons

8.2 U-Value Rule (Phase II-A)

For every surface yielded by the canonical iterator:

iter_fabric_surfaces()

Rule:

If surface.u_value is missing or invalid
→ Heat-loss execution is blocked

8.3 GUI Effects

When blocked due to missing U-Values:

“Run Heat-Loss” is disabled

Blocking reason is displayed

“Fix U-Values…” action is shown

8.4 Fix Action (LOCKED)

The “Fix U-Values…” action emits the same intent as:

Heat-Loss Panel “Open U-Values…”

Construction Panel “Open U-Values…”

There are:

no repair-only paths

no special-case wiring

One intent. One handler. One path.

9. iter_fabric_surfaces() — Canonical Contract (LOCKED)

This iterator is now a critical API.

It must:

Yield only heat-loss participating surfaces

Be order-stable

Be non-recursive

Have no side effects

It must never:

Call readiness evaluation

Call GUI code

Infer participation heuristics

All U-Value readiness depends on this iterator.

Any change to its semantics requires a new phase.

10. Phase II-A Completion Criteria (Satisfied)

✔ Worksheet row click selects a surface
✔ Construction panel reflects selected surface
✔ U-Values panel opens focused on that surface
✔ Missing U-Values block execution
✔ “Fix U-Values…” routes correctly
✔ No circular imports
✔ No duplicate signals
✔ MainWindowV3 is the only navigator

11. Forward Reference (Not Part of This Freeze)

Phase II-B may introduce:

Construction layer authoring

U-Value derivation logic

ResolvedFabricSurface lifecycle

Fabric engine execution

None of these may retroactively modify Phase II-A contracts.

======================================================================
Phase II-A is now frozen.
All future work must respect this contract.
======================================================================
