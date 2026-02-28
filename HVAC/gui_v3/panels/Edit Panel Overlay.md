======================================================================
HVACgooee Bootstrap — GUI v3 Heat-Loss Edit Overlay (HLPE)
======================================================================

Bootstrap ID: BL-GUI-HLPE-EDIT
Phase: GUI v3 — Phase F → Phase G
Status: ACTIVE (authoritative)
Date: 2026-02-12

----------------------------------------------------------------------
1. Purpose
----------------------------------------------------------------------

This bootstrap formalises the Heat-Loss Edit Overlay (HLPE) system.

It defines:
• How heat-loss editing is initiated
• Where edit state lives
• How edit intent propagates
• What is editable in v1
• What is explicitly NOT editable yet
• How this mirrors spreadsheet behaviour

This phase enables:
• Safe, explicit heat-loss editing
• Element-level edits via overlay panel
• Clear visual edit mode
• ESC-based exit semantics
• Zero ambiguity between view vs edit

----------------------------------------------------------------------
2. Canonical Mental Model (LOCKED)
----------------------------------------------------------------------

• Heat-Loss Panel (HLP) is READ-ONLY
• All edits occur in HLPE (overlay)
• Edit mode is temporary and contextual
• No edits occur inline in the worksheet
• Row click ≠ edit
• Column header click = edit intent

This is non-negotiable.

----------------------------------------------------------------------
3. Authority Boundaries (LOCKED)
----------------------------------------------------------------------

3.1 GUI

GUI MUST NOT:
• Mutate ProjectState directly
• Perform calculations
• Infer geometry
• Auto-apply defaults

GUI MAY:
• Capture user edit intent
• Open / close edit overlays
• Route intent to correct editor
• Display committed results only

3.2 ProjectState

ProjectState:
• Owns authoritative data
• Accepts committed edits only
• Remains calculation-free
• Does not know about GUI edit state

3.3 HLPE (Overlay)

HLPE:
• Is GUI-only
• Holds temporary edit state
• Emits APPLY or CANCEL intent
• Never commits directly
• Never calculates

----------------------------------------------------------------------
4. Edit Mode Semantics (LOCKED)
----------------------------------------------------------------------

4.1 Visual Language

• Normal HLP: neutral
• Edit mode (HLPE active): AMBER / ORANGE
• HLP itself does not change colour
• HLPE clearly announces: “EDIT MODE”

4.2 Entry into Edit Mode

Edit mode is entered ONLY via:

• Clicking column headers in HLP:
  - Area (m²) → geometry edit
  - U (W/m²K) → construction edit
  - Qf / losses → assumptions edit

Row click:
• Selects / inspects only
• NEVER opens edit mode

4.3 Exit from Edit Mode

• ESC always exits edit mode
• Cancel button exits edit mode
• Apply button exits edit mode after commit
• No silent exits

----------------------------------------------------------------------
5. Scope of Editing (Phase G / v1)
----------------------------------------------------------------------

5.1 Allowed in v1

• Element-level editing only
• Area override (derived, not geometry)
• Construction selection
• ΔT / Qf assumptions
• Internal losses enable / disable

5.2 Explicitly NOT in v1

• Room L/W/H editing
• Automatic recalculation
• Multi-element batch editing
• Implicit default propagation
• Auto-commit on change

These are deferred by design.

----------------------------------------------------------------------
6. Room 1 and Defaults (LOCKED)
----------------------------------------------------------------------

Room 1 is NOT special as a room.

What is special is:
• Default-authoring context

Rules:
• While defaults are not yet locked:
  - Edits MAY be promoted to project defaults
  - Promotion is explicit and opt-in
• In single-room projects:
  - Defaults exist but have no secondary consumers
• No separate “single-room mode” exists

One-room projects are normal projects.

----------------------------------------------------------------------
7. Edit Granularity (LOCKED)
----------------------------------------------------------------------

• One element edited at a time
• One scope per edit session
• No cross-element mutation
• No cross-room mutation

Exception:
• First room may author defaults explicitly

----------------------------------------------------------------------
8. Signal & Wiring Contract (LOCKED)
----------------------------------------------------------------------

8.1 HeatLossPanelV3 exposes:

• edit_area_requested
• edit_uvalue_requested
• edit_qf_requested

These are GUI intent signals only.

8.2 MainWindowV3:

• Wires signals → HLPE entry
• Owns overlay lifecycle
• Routes scope + room context
• Handles ESC exit

8.3 GuiProjectContext:

• Holds current_room_id
• Holds HLPE active state
• Broadcasts HLPE visibility changes
• Does NOT mutate ProjectState

----------------------------------------------------------------------
9. Spreadsheet Parity (RATIONALE)
----------------------------------------------------------------------

This design mirrors spreadsheet workflows:

• Worksheet = view
• Separate dialog = edit
• Explicit commit
• Auto-calc deferred or manual
• Defaults authored implicitly in first room

This is intentional and correct.

----------------------------------------------------------------------
10. What Is Now Stable
----------------------------------------------------------------------

LOCKED after this bootstrap:

• HLP read-only status
• Overlay-only editing
• Edit entry points
• Visual edit language
• ESC semantics
• Room 1 default-authoring model

All future work is additive.

----------------------------------------------------------------------
11. Next Canonical Steps (Not Part of This Bootstrap)
----------------------------------------------------------------------

Phase G-A:
• HLPE geometry widgets (area override)
• Validation only, no commit

Phase G-B:
• HLPE construction selector
• Delegation to Construction panel

Phase G-C:
• Commit pathway → ProjectState
• Manual recalculation trigger

----------------------------------------------------------------------
End of Bootstrap
