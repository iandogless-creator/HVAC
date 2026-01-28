# Design Philosophy

This document explains **how HVACgooee thinks**.

It does not describe APIs.
It does not replace bootstraps.
It exists to preserve *engineering intent* over time.

If you are modifying core systems, read this first.

---

## 1. Intent Before Physics

HVACgooee strictly separates:

- **Declared intent**
- **Physical calculation**
- **Result consumption**

Factories assemble intent.
Engines perform physics.
Orchestrators sequence and commit results.

No layer is allowed to do the job of another.

This prevents:
- Hidden assumptions
- Accidental coupling
- “Helpful” shortcuts that break authority

---

## 2. Authority Is Explicit

There is exactly one source of truth at any time.

- `ProjectState` is authoritative
- Engines read, never mutate
- GUI observes, never decides
- Validity is declared, never inferred

If something is valid, it was committed.
If it was not committed, it is not valid.

There is no implicit state.

---

## 3. Physics Is Continuous

The physical equations used by HVACgooee:

- Have no intrinsic size limits
- Have no preferred geometry
- Do not encode historical table bounds

If the mathematics remains valid, the engine remains valid.

Constraints arising from:
- Manufacturing
- Installation
- Cost
- Standards

are applied **above** core physics, never inside it.

(See also: `CAVEATS.md`)

---

## 4. Tables Are Treated as Guidance

Legacy tables are preserved and respected.

They represent:
- Typical practice
- Historical context
- Human experience

They do not represent:
- Absolute physical limits
- Mathematical boundaries

HVACgooee treats tables as *advisory*, not authoritative.

---

## 5. Additions, Not Rewrites

Once a bootstrap is frozen:

- New features are added **above** it
- Existing contracts are not widened
- Existing engines are not repurposed

If a change requires breaking a locked rule,
a **new bootstrap** must be written.

This is a feature, not friction.

---

## 6. Determinism Over Convenience

Given the same inputs, HVACgooee must always:

- Produce the same results
- In the same order
- Without side effects

Determinism is valued above:
- Cleverness
- Performance micro-optimisations
- Implicit caching

This makes the system testable, auditable, and teachable.

---

## 7. Humans Are Part of the System

HVACgooee is designed for:

- Engineers who reason
- Not button-pushers
- Not black boxes

Clarity is preferred over brevity.
Explicitness is preferred over automation.
Understanding is preferred over “magic”.

---

## Related Documents

- `README.md` — project overview
- `BOOTSTRAP_EURIKA.md` — architectural authority
- `CAVEATS.md` — clarifications and intent

---

*Good engineering survives its authors.*
This document exists to help with that.

— HVACgooee
