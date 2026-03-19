======================================================================
HVACgooee — Bootstrap: Templates Directory
======================================================================
Phase: Directional (Post-Phase H, Pre-Implementation)
Status: INTENT ONLY (NO CODE)
Authority: Architectural intent
======================================================================

Purpose

This document defines the role, scope, and boundaries of the Templates subsystem in HVACgooee.

Templates exist to declare intent, not to calculate, validate, or execute.

This bootstrap is directional only.
It authorises no code and introduces no new authority.
What Templates Are

    Templates are structured intent presets used to initialise or modify project data in a transparent, explicit way.

Templates may describe:

    usage assumptions

    regulatory defaults

    environmental intent

    specialised volume handling

Templates are not authoritative physics and never perform calculations.
What Templates May Contain

Templates may define declared intent defaults, including (but not limited to):
1. Usage & Occupancy Intent

    Dwelling

    Office

    Classroom

    Healthcare

    Industrial

    User-defined usage profiles

2. Environmental Assumptions

    Internal design temperatures

    External design temperature references

    Ventilation / infiltration assumptions

    Default ACH values

3. Geometry-Related Intent

    Specialised volume handling (e.g. atria, double-height spaces)

    Volume participation rules

    Assumed ceiling heights (where geometry is abstracted)

4. Regulatory Presets

    Region-specific defaults

    Standards-based assumptions

    Documented compliance starting points

All such values are explicitly declared and fully overridable.
What Templates Are NOT

Templates must never:

❌ Perform calculations
❌ Trigger execution
❌ Modify committed results
❌ Gate readiness
❌ Infer missing geometry
❌ Enforce regulatory compliance
❌ Introduce implicit defaults at run time

Templates do not “decide” anything.
Relationship to Core Architecture
Readiness

    Heat-loss readiness depends only on valid geometry

    Templates do not block or enable execution

Authority

    Templates populate declared intent only

    ProjectState remains the sole authority after commit

    Runner topology is untouched

Overrides

    Template values are normal declared inputs

    User overrides take precedence

    Templates never override user intent silently

Lifecycle (Conceptual)

    Template is selected or applied

    Declared intent is populated

    User may inspect or override values

    No calculation occurs

    Execution occurs only via explicit run

Templates participate before execution and outside authority.
Transparency Rule (Critical)

    All template-supplied values must be visible, inspectable, and overridable.

There must be no hidden assumptions.
Directory Intent (Proposed)

The Templates directory is expected to contain:

    declarative data (e.g. JSON / YAML / structured Python)

    documentation describing assumptions

    no executable logic

    no coupling to GUI or engines

Exact structure is intentionally undefined at this stage.
Why This Bootstrap Exists

This document exists to ensure that:

    Phase I UI clarity work does not leak template logic

    Regulatory complexity does not contaminate core readiness

    Defaults remain explicit and honest

    Future expansion is possible without refactoring the core

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
