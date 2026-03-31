🔒 HVACgooee — GUI v3 Overlay System
FINAL OVERLAY CHECKLIST (Freeze Candidate)
🧱 1) AUTHORITY BOUNDARIES (NON-NEGOTIABLE)
✅ Must be true everywhere

 HLP is 100% read-only

no QSpinBox, QLineEdit, editable cells

no writes to ProjectState

no hidden state

 Mini panels NEVER mutate ProjectState

only emit:

geometry_committed

ach_committed

no direct context access

 Adapters are the ONLY writers

all model mutation happens here

no UI class writes to model

 ProjectState is single source of truth

no UI caching

no shadow state

🔁 2) SINGLE DIRECTION DATA FLOW
Must always follow:
User → Panel → Adapter → ProjectState → refresh → HLP
Verify:

 No reverse writes (UI ← UI)

 No panel updating another panel directly

 No adapter calling UI setters except projection methods

🎯 3) COMMIT DISCIPLINE (CRITICAL)
GeometryMiniPanel

 uses editingFinished (NOT valueChanged)

 emits only when valid

 prevents duplicate commits (_last_values)

ACHMiniPanel

 uses editingFinished

 emits ach_committed (NOT continuous)

 prevents duplicate commits

Verify globally:

 No continuous signal → model writes

 No “live typing” mutation

🧠 4) OVERLAY CONTROLLER BEHAVIOUR

 Only one active overlay at a time

 Opening new overlay → previous is destroyed

 Editor is always parented to:

table.viewport()

 Anchoring logic:

cell editor → positioned beside cell

non-cell editor → safe fallback position

 No orphan widgets left behind

🔗 5) HLP → OVERLAY HOOKS
Must exist and be clean:

 worksheet_cell_edit_requested(row, col)

 ach_edit_requested

 geometry_edit_requested

And:

 HLP does NOT create EditContext

 HLP does NOT know overlay implementation

🧩 6) ADAPTER RESPONSIBILITIES (STRICT)
GeometryMiniPanelAdapter

 writes:

room.geometry.*

 calls:

TopologyResolverV1.resolve_project(ps)

 calls:

ps.mark_heatloss_dirty()

 calls:

refresh_all()
ACHMiniPanelAdapter

 writes:

room.air_changes_per_hour

(or transitional equivalent)

 calls:

ps.mark_heatloss_dirty()

 calls:

refresh_all()
Verify:

 No adapter emits Qt signals to drive refresh

 No adapter directly updates HLP widgets

🔁 7) SINGLE REFRESH ENTRY
Must be enforced:
def _apply_run_result(...):
    self._refresh_all_adapters()

and

adapter commit → refresh_all_callback()
Verify:

 No partial refresh calls

 No panel-specific refresh hacks

 No duplicate refresh triggers

📊 8) HLP PROJECTION CONTRACT
Must be the ONLY UI update surface

 set_room_header(...)

 set_geometry_summary(...)

 set_rows(...)

 set_room_results(...)

 set_heatloss_status(...)

 set_run_enabled(...)

 clear()

Verify:

 Adapters use ONLY these

 No direct label access (_value_qf.setText(...) etc.)

🧮 9) TOPOLOGY → FABRIC → Qf PIPELINE
After geometry commit:

 topology resolves

 fabric rows regenerate

 Qf rows appear in HLP (even before full run if applicable)

Verify:

 No stale rows

 No “ghost surfaces”

 No duplication

⚠️ 10) DIRTY / VALID STATE CONSISTENCY

 geometry change → heatloss_valid = False

 ACH change → heatloss_valid = False

 run → heatloss_valid = True

UI:

 HLP shows:

VALID (green)

DIRTY (red)

🧼 11) NO LEGACY DRIFT
Must be removed:

 _edit_length, _edit_width etc. usage in adapters

 valueChanged → model writes

 set_totals(...) (old API)

 set_header_context(...) reliance

 geometry_intent as primary store (allowed only transitional)

🧪 12) EDGE CASE TESTS (DO THESE MANUALLY)
Test 1 — Geometry edit

change length

→ topology updates

→ HLP rows update

→ status becomes DIRTY

Test 2 — ACH edit

change ACH

→ no crash

→ Qv updates after run

→ status DIRTY

Test 3 — Rapid edits

spin quickly

→ only one commit fires

→ no UI flicker

Test 4 — Room switch mid-edit

open overlay

switch room

→ overlay resets safely

→ no cross-room writes

Test 5 — Run cycle

edit geometry → DIRTY

click Run

→ VALID

→ Qf / Qt stable

🔒 13) FREEZE CRITERIA

You can tag when:

 All above checks pass

 No UI writes to model outside adapters

 No crashes under rapid interaction

 No duplicate commits

 No stale display after refresh

🏷️ RECOMMENDED TAG
git tag gui-v3-overlay-system-frozen
git push origin gui-v3-overlay-system-frozen
🧠 Final sanity check (the one that matters)

Ask yourself:

“If I removed all adapters, would anything still change ProjectState?”

👉 If the answer is no, your architecture is clean.

🚀 Where you are

This is not a prototype anymore.

You now have:

A proper UI → Model → Engine boundary system

Very close to something you can build the entire rest of HVACgooee on.

If you want next, I’d suggest:

🔥 “WorksheetRowMetaV1 (lock cell editing properly)”

That’s the one remaining structural upgrade before Phase IV really scales.
