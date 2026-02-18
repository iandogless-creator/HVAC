# ======================================================================
# HVACgooee — GUI v3 Phase G-C Freeze
# Heat-Loss Worksheet & HLPE Spine
# ======================================================================

Freeze ID: GUI-V3-PHASE-G-C
Status: FROZEN
Date: 2026-02-17
Applies to: commit 4e7443a and later

----------------------------------------------------------------------
1. Purpose
----------------------------------------------------------------------

This freeze formally locks the **GUI v3 Heat-Loss worksheet spine** and
the **Heat-Loss Edit Overlay (HLPE) interaction model**.

This phase proves that:
• The Heat-Loss worksheet can render deterministically
• Edit intent can be routed non-positionally
• GUI authority boundaries are respected
• No calculations are required to validate interaction flow

This freeze exists to prevent regression before engine integration.

----------------------------------------------------------------------
2. Canonical Behaviour (LOCKED)
----------------------------------------------------------------------

2.1 Heat-Loss Worksheet

• The worksheet is **read-only**
• Rows are populated by an observer adapter
• No inline editing is permitted
• The worksheet does not calculate, validate, or infer

Row population may be:
• DEV-only (pre-engine), or
• Engine-driven (future)

The worksheet does not know *where* data comes from.

----------------------------------------------------------------------
2.2 DEV Worksheet Rows (TEMPORARY, LOCKED BEHAVIOUR)

In Phase G-C:
• DEV rows MAY be used to populate the worksheet
• DEV rows MUST be deterministic
• DEV rows MUST NOT mutate ProjectState
• DEV rows MUST be isolated and removable

DEV rows exist solely to prove the GUI spine.
They are not a modelling feature.

Removal of DEV rows MUST preserve:
• Row → cell → HLPE routing
• Room scoping behaviour
• Non-positional signal flow

----------------------------------------------------------------------
2.3 HLPE (Heat-Loss Edit Overlay)

HLPE is **not an inline editor**.

HLPE is:
• A modal-like overlay
• Visually aligned with the worksheet
• Contextual to a single room and single element
• GUI-only state

HLPE:
• Emits edit intent
• Does NOT apply edits directly
• Does NOT calculate
• Does NOT own authority

Only one HLPE session may exist at a time (v1 rule).

----------------------------------------------------------------------
3. Edit Interaction Model (LOCKED)
----------------------------------------------------------------------

3.1 Entry

HLPE is entered via:
• Mouse left-click on an editable worksheet cell

Keyboard navigation is explicitly out of scope for v1.

3.2 Routing (CRITICAL)

Edit routing is **non-positional**.

Canonical signal path:
    Worksheet cell click
        → HeatLossPanel emits edit_requested(room_id, element_id, attribute)
            → MainWindow resolves scope
                → GuiProjectContext opens HLPE session
                    → HLPE overlay is shown

No widget assumes column index or screen position.

3.3 Exit

HLPE exits via:
• Apply
• Cancel
• ESC key

On exit:
• HLPE GUI state is cleared
• Observers refresh
• No automatic calculation is triggered

----------------------------------------------------------------------
4. Visual Semantics (LOCKED)
----------------------------------------------------------------------

• Selected room is highlighted in the Rooms panel (green)
• HLPE active state is visually indicated (accent only)
• Only the edited cell is visually emphasised
• Backgrounds remain neutral
• No global colour shifts occur during edit mode

Element names are **read-only in v1**.
Clicking an element name may show an informational tooltip only.

----------------------------------------------------------------------
5. Authority Boundaries (LOCKED)
----------------------------------------------------------------------

• GUI never mutates ProjectState directly
• GUI never calculates heat-loss
• Adapters are observer-only
• Controllers own execution
• ProjectState remains authoritative

Any change that violates these rules is a regression.

----------------------------------------------------------------------
6. Explicit Non-Goals (Phase G-C)
----------------------------------------------------------------------

This phase does NOT include:
• Engine-backed results
• Area / U-value / ΔT application
• Batch edits
• Keyboard navigation
• Construction wizard integration
• Geometry resolution
• Validation logic

All future work must be additive.

----------------------------------------------------------------------
7. Next Allowed Additive Steps
----------------------------------------------------------------------

After this freeze, permitted next steps include:
• Area HLPE end-to-end application
• ΔT HLPE application
• U-value HLPE application
• Replacement of DEV rows with engine previews
• Visual polish that does not alter interaction semantics

----------------------------------------------------------------------
END OF FREEZE
