# HVACgooee Caveats

HVACgooee is an open-source engineering calculation project.

It aims to expose the physics, assumptions, and design choices behind HVAC calculations rather than hide them behind fixed tables or opaque software behaviour.

The following caveats explain how the project treats standards, published guidance, legacy practice, numerical methods, and user design judgement.

---

## Tables Are Guidance, Not Nature

Published guidance tables, including CIBSE, HIVE, BS, manufacturer data, and other recognised sources, are respected and preserved.

Many such tables are themselves derived from sound engineering physics, including recognised hydraulic methods such as Colebrook-White friction calculations.

They represent:

- Typical practice
- Practical design ranges
- Published assumptions
- Rounded engineering values
- Human experience
- Repeatable industry guidance

They do **not** represent:

- Absolute physical limits
- Mathematical boundaries
- Universal truth
- A substitute for understanding the assumptions underneath

HVACgooee treats tables as:

> “Useful advice, not natural law.”

This is not a criticism of published tables.

It means a table is a published engineering view of the physics, usually under stated or implied assumptions. The core engine should therefore preserve the underlying physics and allow tables, standards, and guidance to sit above it as design references rather than hard-coded natural limits.

---

## Physics First, Tables Second

Where possible, HVACgooee should calculate from first principles or accepted engineering equations.

For hydronics, this means the calculation route may include:

- Flow rate
- Pipe internal diameter
- Water properties
- Pipe roughness
- Reynolds number
- Friction factor
- Velocity
- Pressure gradient
- Fittings and local resistance
- Route pressure drop

Tables may then be used to:

- Check reasonableness
- Provide familiar design ranges
- Support educational explanation
- Compare with recognised practice
- Offer quick design guidance

A table may agree with the engine because both are derived from the same physics. That is desirable.

The table should not become the hidden authority if the engine can show the physics directly.

---

## Standards and Guidance

HVACgooee should respect standards, guides, and recognised practice.

However, standards and guides often depend on context:

- Country
- Date of publication
- Building type
- System type
- Pipe material
- Temperature regime
- Safety margin
- Assumed roughness
- Intended design method
- Regulatory purpose

Therefore, where a value comes from guidance, HVACgooee should try to make that clear.

Examples:

```text
Source: CIBSE guidance
Source: manufacturer data
Source: user design basis
Source: calculated from Colebrook-White
Source: provisional default
```

The user should be able to tell the difference between:

```text
calculated physics
published guidance
software default
user-entered design assumption
```

---

## Deterministic Core

The calculation core should be deterministic.

Given the same inputs, the same version of the engine should produce the same outputs.

The core should avoid hidden AI judgement, silent model choices, or unexplained assumptions.

AI may assist outside the core, for example in explanation, documentation, or workflow support, but the engineering result should remain traceable and reproducible.

---

## User Design Basis Remains Authoritative

HVACgooee may show evidence that one option appears better than another.

For example:

```text
F&R controlling Δp
F+RR controlling Δp
Route Δp change
Balancing burden
RR extra length
RR extra Δp
```

This evidence is guidance for the designer.

It should not automatically force the design choice.

A user may select a design basis for reasons the software does not yet fully model, including:

- Site constraints
- Pipe routing practicality
- Future maintenance
- Known installation conditions
- Existing pipework
- A preferred teaching/example mode
- A better physical layout than the current proxy calculation represents

Therefore:

> Evidence informs the design basis. It does not replace the designer.

---

## Preview Means Preview

Several HVACgooee stages are deliberately marked as preview-only.

Preview calculations may show:

- Candidate pipe sizes
- Route pressure differences
- Return arrangement comparisons
- Preliminary balancing burden
- Local K pressure effects
- Reverse-return suitability
- Provisional resistance differences

Unless explicitly committed, these previews do **not** mean:

- Final pipe sizing
- Pump selection
- Valve selection
- Final balancing
- Installation instruction
- Regulatory compliance statement

Preview rows should be treated as engineering evidence, not final design output.

---

## Reverse Return Caveat

Reverse return can be excellent when the physical layout suits it.

A good example is a central single-storey building with radiators arranged around the external perimeter. In that case, a reverse-return loop may naturally follow the building shape and may require little or no extra pipe allowance.

However, reverse return is not automatically better in every case.

Depending on layout, it may:

- Reduce balancing burden
- Increase pipe length
- Increase pressure drop
- Make routing simpler
- Make routing worse
- Be ideal for one subleg but not another

Therefore HVACgooee separates:

```text
RR return path
```

from:

```text
RR extra / added length allowance
```

A perfect physical loop may have:

```text
RR extra length = 0.00 m
```

A retrofit or proxy layout may require:

```text
RR extra length = derived or manually entered
```

This distinction is important.

---

## Manual Inputs Are Not Inferior

Manual input is not a weakness.

Some engineering decisions cannot be inferred reliably from a simplified model, especially before full geometry, pipe routing, or site constraints are known.

Manual entries may represent:

- Real measured lengths
- Designer judgement
- Site knowledge
- A known route not yet drawn
- A teaching example
- An accepted design assumption

Where manual input affects a result, HVACgooee should label it clearly.

Example:

```text
RR length basis: Manual allowance
RR extra length: 4.50 m
Source: user design basis
```

---

## Defaults Are Starting Points

Defaults are provided to make the software usable.

They are not universal recommendations.

Examples of defaults may include:

- Indoor temperature
- External design temperature
- Air change rate
- Pipe material
- Candidate pipe sizes
- Water density
- Design flow and return temperature
- Roughness assumption
- Local K values

Defaults should be visible, editable where appropriate, and documented.

A hidden default is dangerous.

A visible default is useful.

---

## Accuracy and Rounding

HVACgooee calculations may involve both exact formulae and rounded engineering presentation.

A result may be calculated internally with higher precision and displayed with sensible rounding.

For example:

```text
Internal: 28744.218 Pa
Display: 28,744 Pa
```

Displayed values are intended to be readable.

They should not be mistaken for a claim of unrealistic precision.

---

## Existing Practice and New Calculation Can Coexist

HVACgooee is not intended to discard established practice.

It is intended to make the calculation route visible.

The project should allow comparison between:

- Traditional table-based design
- Manufacturer guidance
- First-principles calculation
- User design basis
- Educational worked examples

Where these agree, confidence increases.

Where they differ, HVACgooee should help expose why.

Possible reasons include:

- Different roughness assumptions
- Different pipe internal diameters
- Different water temperature
- Different flow regime
- Different safety margins
- Different rounding
- Different design intent

---

## Not a Substitute for Professional Responsibility

HVACgooee is a calculation and education tool.

It does not remove the need for competent engineering judgement.

Users remain responsible for checking:

- Regulations
- Standards
- Manufacturer instructions
- Site conditions
- Safety requirements
- Installation constraints
- Commissioning requirements
- Maintenance access
- Client requirements

HVACgooee should help make decisions clearer.

It should not pretend to replace responsibility.

---

## Open Source Engineering Ethos

HVACgooee should remain transparent.

Where possible:

- Formulae should be visible
- Assumptions should be named
- Defaults should be documented
- Intermediate values should be inspectable
- Outputs should be explainable
- Data sources should be traceable

The aim is not only to produce an answer.

The aim is to show how the answer was reached.

---

## Summary

HVACgooee respects published tables, standards, and established HVAC practice.

It also recognises that those tables are usually assumption-bound presentations of physics, not the physics itself.

Therefore the project should:

- Preserve guidance
- Expose assumptions
- Calculate transparently
- Keep user design basis visible
- Avoid hidden authority
- Treat preview evidence as evidence
- Keep final responsibility with the designer

In short:

> Tables guide. Physics explains. The designer decides.
