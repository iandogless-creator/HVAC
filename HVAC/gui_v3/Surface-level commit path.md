Writing
======================================================================
HVACgooee — Phase D.2 Bootstrap
Overlay Editing Pipeline (Selection → Edit → Commit → Refresh)
Timestamp: Tuesday 23 March 2026, 13:12 pm (UK)
Status: ACTIVE
======================================================================
0) Purpose

Establish a complete, stable editing pipeline:

Selection (worksheet)
→ Context routing
→ Overlay editor (auto-loaded from ProjectState)
→ Commit via controller/adapters
→ ProjectState update
→ UI refresh

This phase removes all legacy editing paths.

1) NON-NEGOTIABLE RULES

• Overlay is the ONLY editing path
• Worksheet is strictly read-only
• Adapters NEVER mutate ProjectState
• Overlay NEVER reads from UI — only from ProjectState
• Context is the ONLY signal routing layer
• Controllers perform all writes

2) Canonical Flow (LOCKED)
User clicks worksheet row
Panel emits: cell_selected(row_index)
Adapter resolves:
→ surface_id
→ edit kind (geometry / ach / surface)
Adapter calls:
context.request_edit(kind, surface_id)
Context emits:
edit_requested(kind, surface_id)
MainWindow receives:
_on_edit_requested(...)
OverlayController:
→ resolves authoritative values from ProjectState
→ activates overlay
→ injects EditContext + initial values
User edits → commits
Overlay emits:
commit_requested(EditContext, values)
Controller:
→ applies mutation to ProjectState
MainWindow:
→ refresh_all_adapters()
3) Data Contracts
EditContext (LOCKED)

kind: str
room_id: str
surface_id: Optional[str]

No logic. Pure routing.

WorksheetRowMeta (LOCKED)

surface_id: str
element: str
state: GREEN | ORANGE | RED
message: Optional[str]
columns: Dict[int, WorksheetCellMeta]

Overlay Input (DICT)

Geometry:
{
"length_m": float,
"width_m": float,
"height_m": float
}

ACH:
{
"ach": float
}

Surface:
{
"area_m2": float,
"u_value": float
}

4) Overlay Responsibilities

• Render correct editor based on EditContext.kind
• Load values ONLY from provided data dict
• Emit commit with same EditContext
• Never access ProjectState directly

5) Controller Responsibilities

• Validate input
• Apply mutation to ProjectState
• Mark heat-loss dirty
• NEVER touch GUI

6) Adapter Responsibilities

• Build worksheet rows from ProjectState
• Build WorksheetRowMeta
• Map row → surface_id
• Resolve edit intent
• NEVER mutate

7) Visual State System (LOCKED)

Row states:

GREEN → valid
ORANGE → incomplete (e.g. missing adjacency)
RED → invalid

Run button:

GREEN → enabled
ELSE → disabled

8) Removed / Deprecated (MUST NOT EXIST)

✗ GeometryMiniPanel (dock)
✗ ACHMiniPanel (dock)
✗ geometry_edit_requested signal
✗ ach_edit_requested signal
✗ direct MainWindow edit calls
✗ heatloss_run_context (unless proven required)

9) Immediate Implementation Tasks

[ ] Fix table signal ordering (create → connect)
[ ] Ensure panel emits cell_selected(row)
[ ] Ensure adapter resolves meta_for_row(row)
[ ] Ensure context.request_edit() exists
[ ] Ensure MainWindow listens to edit_requested
[ ] Ensure OverlayController resolves initial values
[ ] Ensure overlay.load_context(ctx, data) implemented
[ ] Ensure commit_requested wired to controller
[ ] Ensure refresh_all_adapters() is single exit

10) Exit Criteria (STRICT)

✔ Clicking any editable row opens correct overlay
✔ Overlay fields pre-populated correctly
✔ Editing + commit updates ProjectState
✔ Worksheet updates immediately
✔ No UI element writes directly to state
✔ No duplicate edit paths remain

11) Architectural Statement

Editing is contextual, not positional.

The worksheet expresses truth.
The overlay edits intent.
ProjectState remains the only authority.

12) Next Phase (Do NOT start yet)

Phase D.3 — Live Preview (pre-commit ghost updates)

Only after this pipeline is stable.

======================================================================
END OF BOOTSTRAP
======================================================================
🧠 Straight talk

You’ve now crossed from:

UI wiring phase

into:

interaction architecture phase

This bootstrap keeps you from accidentally:

reintroducing mini panels
leaking state into UI
duplicating edit paths
If you want next

I’d go:

👉 surface-level commit implementation (write-back using surface_id)
That completes the loop and makes everything feel “real”.

Just say 👍
