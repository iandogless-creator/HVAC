# HVACgooee — Simple Heat-Loss Engine (v1)

Status: CANONICAL  
Applies to: HVACgooee v1

---

## Purpose

The Simple Heat-Loss engine provides a stable, worksheet-driven
heat-loss calculation suitable for v1 of HVACgooee.

It prioritises:
- transparency
- engineering familiarity
- tolerance of partial data
- explicit execution

This engine is the **default and only** heat-loss engine used in v1.

---

## Relationship to GUI v3

The GUI v3 Heat-Loss panel is a **worksheet**, not a wizard.

The Simple engine is designed to consume:
- explicit worksheet intent
- optional overrides
- project-level execution requests

The GUI:
- does not select the engine
- does not infer values
- does not validate correctness

---

## Worksheet Row Population (v1)

Worksheet rows are populated **before any calculation**.

Rows represent **existing project intent**, not results.

### Source of rows

For each room in `ProjectState.rooms`:

- each heat-loss relevant element produces one worksheet row

Examples:
- external walls
- windows / doors
- roof / ceiling
- floor

The existence of an element is sufficient to create a row.

---

## Column Semantics

| Column | Meaning |
|------|--------|
| Element | Human-readable element name |
| Kind | Element type (wall, window, roof, etc.) |
| Area (m²) | Derived from geometry |
| ΔT (K) | Preview ΔT from environment + room |
| U (W/m²K) | Construction value or worksheet override |
| Loss (W) | Result value (blank until run) |

Blank values indicate **unknown**, not zero.

---

## Override Layering

Values are displayed using the following priority:
worksheet override
→ calculation result
→ derived preview
→ blank


Overrides:
- do not modify geometry
- do not modify constructions
- only affect calculation when run

---

## Execution Model

- Heat-loss is executed explicitly by the user
- Execution is project-level
- Results are stored in ProjectState
- Worksheet intent is preserved between runs

The Simple engine performs no inference or compliance judgement.

---

## Non-Goals (v1)

The Simple engine does NOT:
- compute ψ-values
- model thermal mass
- perform compliance checks
- infer missing inputs
- auto-generate elements

These are reserved for later engines.

---

## Forward Compatibility

The Simple worksheet UI is engine-agnostic.

Future engines (Technical, Advanced) will reuse the same worksheet
surface with different execution depth.

No GUI rewrite is required to support future engines.

Where we are now (important to acknowledge)

GUI spine is stable

Worksheet exists and renders

Architecture is clean

Engines are correctly scoped

v1 scope is clear and defensible

