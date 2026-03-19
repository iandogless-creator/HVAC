======================================================================
HVACgooee — Bootstrap: Edit Heat-Loss Mode
======================================================================
Phase: Directional (Post-Phase H, Pre-Implementation)
Status: INTENT ONLY (NO CODE)
Authority: Architectural intent
======================================================================

Purpose

This document defines the conceptual Edit Heat-Loss Mode that HVACgooee is heading toward.

It exists to:

    clarify user flow

    prevent accidental authority leaks

    ensure Phase I UI work does not contradict future intent

This document does not authorise implementation.
Context

HVACgooee currently distinguishes between:

    Committed authoritative state

    Declared intent (pre-run)

    Explicit execution (Runner invocation)

However, without an explicit Edit Mode concept, UI affordances risk implying:

    auto-calculation

    soft commits

    preview semantics

This bootstrap defines Edit Heat-Loss Mode as a future, explicit interaction layer — so Phase I work remains aligned.
Definition — Edit Heat-Loss Mode

    Edit Heat-Loss Mode is a bounded state in which the user may modify declared heat-loss intent without triggering calculation or committing authority.

It is not a calculation mode.

It is not a preview mode.

It is not an inspection mode (though inspection may occur within it).
Entry & Exit (Conceptual)
Entering Edit Mode

    Explicit user action

    Intent fields become editable

    System enters a dirty intent state

    No execution occurs

Exiting Edit Mode

One of three explicit decisions:

    Exit (Discard changes)
    → Declared intent reverts
    → No calculation

    Exit (Keep changes)
    → Declared intent retained
    → Still no calculation

    Calculate / Run
    → Declared intent committed
    → Runner invoked
    → New authoritative state produced

There are no implicit exits.
Relationship to Inspection Context

Inspection context is subordinate to Edit Mode.
Inspection Context:

    Triggered by selecting a column in the edit panel

    Read-only

    Visual comparison only

    Cross-panel identity echo

    Exited via defocus toggle or selection change

    Inspection never asks the user to decide.
    Only Edit Mode does.

Explicit Non-Behaviour

Edit Heat-Loss Mode must never:

❌ Trigger recalculation
❌ Preview results
❌ Mutate committed state
❌ Auto-commit on exit
❌ Imply execution
❌ Bypass Runner topology

All calculation remains explicit and deliberate.
Authority Guarantees

This model guarantees:

    One authority at a time

    No mixed states

    No convenience execution

    No UI-driven physics

It preserves:

    Runner purity

    Override semantics

    GUI v3 observer rules

    Phase H execution topology

Relationship to Phase I

Phase I:

✔ May acknowledge the existence of Edit Heat-Loss Mode
✔ May prepare UI affordances visually
✔ May improve inspection clarity

Phase I must not:

    implement edit mode

    add commit logic

    add execution decisions

    change flow semantics

Phase I work must remain compatible, not implementational.
Why This Bootstrap Exists

This document exists to answer one question clearly:

    “When the user edits heat-loss inputs, what is the software doing?”

Answer:

    Nothing — until the user explicitly tells it to calculate.

Status

This bootstrap is:

✔ Directionally complete
✔ Non-binding
✔ Phase-safe
✔ Future-proof

No code may be written under this document.

======================================================================
END OF DOCUMENT
======================================================================
Canonical Concept
IntentOverlayPanel (abstract base)

A bounded, explicit UI surface for editing declared intent without triggering calculation or committing authority.

This is the formula-bar pattern, formalised.

1. Core Responsibilities (LOCKED)

Every overlay panel must:

Be explicitly entered

Edit intent only

Never calculate

Never commit results

Never mutate authoritative state directly

Be discardable without side effects

The overlay exists above ProjectState, not inside it.

2. Base Class Responsibilities

The base class provides behaviour, not domain meaning.

Always provided by base class

Overlay lifecycle (open / close)

Dirty-intent tracking (local to overlay)

Explicit exit actions

Guardrails (no silent exit)

Standard footer buttons

Never provided by base class

Domain fields

Validation rules

Execution logic

Controller calls

3. Canonical Exit Model (DO NOT VARY)

All overlays must expose exactly three exits:

Discard

Revert intent buffer

Close overlay

No state mutation

Keep Changes

Retain declared intent

Close overlay

Mark project dirty

Still no calculation

Run / Apply

Commit intent

Call domain controller

Produce new authoritative state

Close overlay

No implicit commit
No auto-run
No close-equals-save

This is non-negotiable — it’s what keeps the system sane.

4. The Options You Asked For (Minimal, Powerful)

You only need a couple of options, and they should be orthogonal.

Option 1 — Scope
scope = "local" | "global"


local

Single row / pipe / node

Example: one room’s losses, one pipe segment

global

System-wide intent

Example: hydronic design velocities, ΔT policy

Used by:

HL row overlays

Pipe click overlays

Topology-level editors

Option 2 — Edit Mode
edit_mode = "parameter" | "topology"


parameter

Editing numbers / flags

No graph mutation

topology

Structural changes

Must be explicitly entered

Usually modal / stronger visual affordance

This is how you safely separate:

pipe sizing edits

pipe existence edits

Option 3 — Inspection Support (optional but useful)
inspection_enabled = True | False


If enabled:

Hover / select highlights

Cross-panel echo

Read-only comparisons

Inspection is subordinate to editing and never blocks exit.

5. What a Domain Overlay Adds

Each concrete overlay panel supplies only:

Intent DTO(s)

Field widgets

Domain-specific validation messages

Which controller to call on “Run”

Examples
Heat-Loss
HeatLossOverlayPanel
  scope = local
  edit_mode = parameter

Hydronics — pipe click
PipeOverlayPanel
  scope = local
  edit_mode = parameter

Hydronics — topology edit
TopologyOverlayPanel
  scope = global
  edit_mode = topology

Emitters
EmitterSizingOverlayPanel
  scope = local
  edit_mode = parameter


Same base behaviour. Different intent.

6. Authority Guarantees (why this works everywhere)

Because the base class enforces:

explicit entry

explicit exit

no silent commits

no auto-execution

You automatically preserve:

runner purity

controller authority

GUI v3 observer rules

K-D dirty-state semantics

spreadsheet mental model

This is why it scales across domains.

7. One-Sentence Rule (worth writing down)

If a panel edits intent without calculation, it must inherit from IntentOverlayPanel.

That single rule prevents 90% of future UI mistakes.