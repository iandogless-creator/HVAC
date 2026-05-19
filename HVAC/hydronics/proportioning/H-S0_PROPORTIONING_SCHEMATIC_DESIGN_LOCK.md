# HVACgooee — H-S0 Proportioning Schematic Design Lock

Status: ACTIVE design lock  
Branch: phase-hydronics-h-a  
Timestamp: Tuesday 19 May 2026, 07:00 pm UK

## Purpose

The Proportioning schematic is a read-only logic schematic showing how hydronic flow responsibility is distributed across:

- Common main
- Selected index route
- Non-index branch terminal
- No-emitter / unresolved

It is not a CAD pipe layout, not a pressure-loss model, and not a balancing calculation.

## Source authority

The schematic is derived from H-R branch/proportioning projection data.

Primary source:

- `HVAC/hydronics/proportioning/branch_proportioning_summary_v1.py`

The schematic must not mutate ProjectState.

## Visual meaning

The schematic answers:

> What must be proportioned against what?

It does not answer:

> Where exactly do the pipes physically run?

## v1 layout rule

Use a simple left-to-right logic spine:

```text
Boiler / Heat Source → Common main → Selected index route