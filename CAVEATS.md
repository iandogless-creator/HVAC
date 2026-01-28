# Caveats (Read This With a Cup of Tea)

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
Tables stop because humans do.

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
*We use them because we get tired.*

— HVACgooee
