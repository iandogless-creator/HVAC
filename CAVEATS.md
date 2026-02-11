# Caveats

This file exists to say a few important things that don’t belong in
equations, APIs, or tables — but absolutely belong in engineering.

Nothing here overrides the bootstraps.
Nothing here weakens the locks.
These are **intentional clarifications**, not apologies.

---

## There Are No Magical Size Limits

HVACgooee does **not** impose hard limits on:

- Pipe diameter
- Duct size
- Cross-sectional shape
- Aspect ratio
- Absolute flow rate

If the maths works, the maths works.

Physics does not stop at DN300.

Any limits encountered in real projects arise from:

- Manufacturing capability
- Installation and handling
- Structural behaviour
- Cost optimisation
- Standards and guidance

These are **technology limits**, not **physical limits**.

Core engines therefore:

- Remain continuous
- Remain geometry-agnostic
- Avoid baked-in historical assumptions

Constraints belong **above** physics, not inside it.

---

## Materials Are Not a Closed List

HVACgooee does **not** assume a fixed or authoritative list of materials.

Future versions are expected to support:

- User-defined material databases
- Arbitrary numbers of materials
- Full material property definitions, including (but not limited to):
  - Thermal conductivity (λ)
  - Density
  - Specific heat capacity
  - Vapour resistance / μ-values
  - Emissivity (where relevant)
  - Any additional properties required by future engines

There is **no architectural requirement** that materials come from a predefined catalogue.

---

### Why This Is Not Implemented Early

Early stages may expose:

- Reference materials
- Typical values
- Simplified construction presets

This is **scaffolding**, not a constraint.

It exists to:

- Keep early workflows legible
- Avoid committing to immature data models
- Prevent UI complexity from outrunning engine maturity
- Preserve clarity while core physics stabilises

It does **not** imply that:

- Material choice is fixed
- Properties are limited
- Future engines are constrained by early UI decisions

---

### User Databases Are First-Class Citizens (Eventually)

When material databases are introduced:

- User-defined materials will be treated as **equal** to built-in references
- Projects may reference **multiple material sources**
- Materials may be reused, versioned, or replaced without refactoring engines

Materials are **data**, not behaviour.

The engines care about numbers — not where they came from.

---

### Design Principle (Explicit)

> If a material can be described physically, it can be modelled.

Artificial limits on:

- Number of materials
- Number of properties
- Allowable ranges

…would be **software constraints**, not physical ones.

HVACgooee therefore avoids embedding such limits in its core design.

---

This completes a clean trio of caveats:

- No magical size limits
- No sacred tables
- No closed material lists

All three say the same thing from different angles:

**Physics first. Software second.**

---

## Tables Are Guidance, Not Nature

Legacy tables (CIBSE, HIVE, BS, etc.) are respected and preserved.

They represent:

- Typical practice
- Practical ranges
- Human experience

They do **not** represent:

- Absolute limits
- Mathematical boundaries
- Universal truth

HVACgooee treats tables as:

> “Useful advice, not natural law.”

---

## Why This Matters

This approach allows HVACgooee to:

- Model non-standard systems cleanly
- Scale from domestic to district systems
- Preserve legacy methods without freezing innovation
- Support future technology without refactoring core engines

It also prevents a common failure mode:

> 1970s assumptions accidentally becoming 2030s rules.

---

## About This File

This file is intentionally informal.

If you are looking for:

- Authority → read the bootstraps
- Contracts → read the architecture docs
- Physics → read the engines

If you are looking for:

- Philosophy
- Intent
- “Why it’s like this”

You’re in the right place.

---

*Nature has no lookup tables.*

— **HVACgooee**
