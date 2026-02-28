======================================================================
HVACgooee Bootstrap — Construction Wizard v1 (Fabric Authoring)
======================================================================

Bootstrap ID: BL-GUI-CONSTR-WIZARD-V1
Phase: GUI v3 — Phase I-C (Geometry → Fabric Instantiation)
Status: ACTIVE (authoritative)
Date: 2026-02-13

----------------------------------------------------------------------
1. Purpose
----------------------------------------------------------------------

This bootstrap formalises the **Construction Wizard v1**.

The wizard is the primary tool for authoring **fabric elements**
(walls, windows, doors, internal elements) from coarse room geometry.

It defines:
• What the wizard creates
• What inputs it consumes
• What outputs it emits
• How it interacts with geometry and HLPE
• What is explicitly deferred

This phase enables:
• A working heat-loss model at release
• Net wall areas without spreadsheets
• Progressive refinement from coarse to detailed

----------------------------------------------------------------------
2. Canonical Mental Model (LOCKED)
----------------------------------------------------------------------

The Construction Wizard answers:

    “What is the room made of?”

It does NOT answer:
• How big the room is (geometry)
• How heat-loss is calculated
• How results are displayed

The wizard:
• Consumes geometry intent
• Emits fabric intent
• Never performs heat-loss calculations

----------------------------------------------------------------------
3. Wizard Scope (v1) (LOCKED)
----------------------------------------------------------------------

The Construction Wizard v1 supports:

External fabric:
• One external wall group
• Optional windows
• Optional doors

Internal fabric:
• Internal wall group (optional)
• Internal ceiling/floor group (optional)

Orientation, junctions, and per-wall topology are explicitly out of scope.

----------------------------------------------------------------------
4. Inputs Consumed by the Wizard (LOCKED)
----------------------------------------------------------------------

The wizard SHALL consume the following authoritative inputs:

From Geometry Mini-Panel:
• Room height
• External wall length
• Derived gross external wall area

From user input:
• Construction selection (wall)
• Construction selection (window)
• Construction selection (door)
• Opening areas OR opening dimensions

The wizard SHALL NOT:
• Ask for room length / width
• Ask for orientation
• Ask for U-values directly

----------------------------------------------------------------------
5. External Wall Modelling (v1) (LOCKED)
----------------------------------------------------------------------

5.1 Gross Wall Area

Gross external wall area is defined as:

    external_wall_length × room_height

This value is read-only in the wizard.

5.2 Openings

The wizard supports:
• Zero or more windows
• Zero or more doors

Each opening has:
• A construction reference
• An area (m²) OR dimensions (w × h)

5.3 Net Wall Area

Net external wall area is derived as:

    net_wall_area = gross_wall_area − Σ(opening_areas)

Validation:
• Net wall area must be ≥ 0
• Over-subtraction blocks wizard completion

----------------------------------------------------------------------
6. Outputs Emitted by the Wizard (LOCKED)
----------------------------------------------------------------------

Upon completion, the wizard emits **fabric intent** in the form of
one or more fabric elements.

Minimum external output:

• External wall element
    - kind = "ext"
    - area_m2 = net_wall_area
    - construction_id = selected wall construction

Optional additional outputs:

• Window element(s)
    - kind = "ext"
    - area_m2 = window_area
    - construction_id = selected window construction

• Door element(s)
    - kind = "ext"
    - area_m2 = door_area
    - construction_id = selected door construction

Each emitted element:
• Is scoped to the current room
• Appears as a separate Qf row
• Has no orientation in v1

----------------------------------------------------------------------
7. Internal Fabric Modelling (v1) (LOCKED)
----------------------------------------------------------------------

Internal elements:
• Do not use external design temperature
• Are labelled kind = "int"
• Contribute to Qf using their own ΔT rules

Wizard support:
• Internal wall group (area input)
• Optional internal ceiling / floor group

Internal elements are optional in v1.

----------------------------------------------------------------------
8. Authority Boundaries (LOCKED)
----------------------------------------------------------------------

8.1 Construction Wizard

The wizard:
• Emits fabric intent only
• Does NOT calculate Qf
• Does NOT edit geometry intent
• Does NOT bypass readiness rules

8.2 Geometry Mini-Panel

The Geometry Mini-Panel:
• Remains the sole authority for room geometry
• Cannot be overridden by the wizard

8.3 Heat-Loss Worksheet

The worksheet:
• Displays emitted fabric elements
• Remains read-only for area and kind
• Never creates or edits fabric intent

----------------------------------------------------------------------
9. Progressive Refinement Model (RATIONALE)
----------------------------------------------------------------------

This wizard supports progressive accuracy:

• v1:
  - Single wall group
  - Aggregate openings
  - Fast modelling

• Later phases:
  - Per-wall elements
  - Orientation
  - Templates
  - Junctions

Earlier wizard outputs remain valid and editable.

No re-authoring is required.

----------------------------------------------------------------------
10. Validation & Readiness (LOCKED)
----------------------------------------------------------------------

Wizard completion blocks if:
• No wall construction selected
• Net wall area < 0
• Opening areas invalid

On successful completion:
• Fabric intent is stored
• Heat-loss is marked dirty
• No calculation is triggered automatically

----------------------------------------------------------------------
11. Explicit Non-Goals (v1)
----------------------------------------------------------------------

The Construction Wizard v1 does NOT include:
• Orientation
• Wall counts
• Thermal bridges
• Shading
• Multi-zone propagation
• Template automation

These are deferred intentionally.

----------------------------------------------------------------------
12. What Is Now Stable
----------------------------------------------------------------------

LOCKED after this bootstrap:

• Wizard consumes geometry, emits fabric
• Net wall area derivation model
• Separate Qf rows for walls and openings
• Internal vs external classification
• Progressive refinement philosophy

All future work is additive.

----------------------------------------------------------------------
13. Next Canonical Steps (Not Part of This Bootstrap)
----------------------------------------------------------------------

• HLPE Construction Editor (element-level refinement)
• U-value editing via Construction / UVP panels
• Phase F-E — partial execution modes
A room must define internal length and width to exist as a calculable
entity. All other geometric and fabric inputs build upon this base.
Scalar external wall length is a permanent modelling mode and remains
available alongside future orientation and vector-based geometry.

# ======================================================================
#
----------------------------------------------------------------------
End of Bootstrap
