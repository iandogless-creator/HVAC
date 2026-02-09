======================================================================
HVACgooee — RoomTreePanel
GUI v3 Bootstrap
Phase: A — Navigation Scaffold
Status: DRAFT
======================================================================
Purpose

Provide a read-only navigation panel for selecting rooms within a project.

The RoomTreePanel is a navigation authority only.
It does not calculate, validate, or mutate domain data.

Canonical Responsibilities (LOCKED)
RoomTreePanel

Display project room hierarchy (flat or nested)

Allow user selection of a room

Emit intent only:

room_selected(room_id)

Explicitly Forbidden

Calculations

Readiness logic

Controller access

Writing to ProjectState

Formatting results

Triggering adapter refreshes

Authority Model
RoomTreePanel (UI)
    ↓ emits intent
RoomTreeAdapter
    ↓ writes intent
ProjectState.active_room_id
    ↓ observed by
All observer panels (Heat-Loss, Environment, Education, etc.)


RoomTreePanel never talks to other panels.

Phase A Scope (Minimal, Deliberate)
Included

Dockable / floatable panel

Flat list of rooms (tree optional later)

Single-selection only

Emits room_selected(room_id)

Excluded (Future Phases)

Zones / floors

Drag & drop

Icons

Context menus

Multi-selection

Persisted expansion state

Adapter Contract (Phase A)

Input

ProjectState.rooms (or equivalent room list)

Output

Writes:

ProjectState.active_room_id

No other state mutations allowed.

UI Placement (Default)

Dock: Left

Allowed areas: Left | Right

Hidden by default in Simple Mode (future)

Naming (Canonical)

Panel: RoomTreePanel

Adapter: RoomTreeAdapter

Signal: room_selected(room_id: str)

Success Criteria (Phase A)

Selecting a room updates ProjectState.active_room_id

Heat-Loss panel updates automatically via observer refresh

No coupling between RoomTreePanel and any other panel

No calculations triggered

Exit Condition

RoomTreePanel is considered Phase A complete when:

It can select rooms reliably

It does not break existing GUI wiring

It remains boring and stable