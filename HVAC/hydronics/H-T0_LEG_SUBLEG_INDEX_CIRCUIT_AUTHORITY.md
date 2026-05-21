# HVACgooee — H-T0 Leg/Subleg and Index-Circuit Authority

Status: ACTIVE design lock  
Branch: phase-hydronics-h-a  
Purpose: define future hydronic topology authority before calculation work

## Purpose

H-T0 defines the hydronic leg/subleg topology model that will later support accumulated flow, terminal circuits, and true index-circuit pressure-drop ranking.

The current H-S Proportioning schematic is a simplified view. H-T0 defines the future authority behind it.

## Core topology model

HVACgooee hydronics shall model distribution using:

- Leg 1 / Common leg
- Subleg circuits
- Terminal/radiator branches

All subleg circuits must eventually terminate at one or more terminal/radiator branches.

## Core terms

Leg 1 / Common leg / Boiler leg  
The boiler-side shared leg carrying combined system flow.

Subleg circuit  
A downstream circuit leaving the common leg or another subleg. A subleg circuit may split, but it must eventually terminate at one or more terminal/radiator branches.

Terminal branch / radiator branch  
The final local pipework serving one radiator/emitter. It carries that emitter’s local Fr only.

Fr  
Local radiator/emitter branch flow.

AcFr  
Accumulated flow carried by a leg or subleg section.

ΣFr  
Combined flow carried by the common leg / boiler leg.

Selected index route  
The current selected/assumed first-pass route.

True index circuit  
The terminal circuit with the maximum calculated pressure drop back to the boiler/pump.

Balancing order  
All non-index terminal circuits arranged in diminishing calculated Δp.

## Flow authority rules

A terminal/radiator branch carries only its own Fr.

A leg or subleg section carries AcFr: the accumulated flow of all downstream terminal branches and subleg circuits.

At the final terminal radiator on a leg, AcFr equals that radiator’s Fr.

Leg 1 / the common leg carries ΣFr: the combined flow of all connected downstream subleg circuits and terminal branches.

## Riser authority rule

A riser is a geometric descriptor, not an authority category.

A riser may belong to:

- the common leg, if it carries combined flow to downstream subleg circuits
- a subleg circuit, if it carries accumulated flow for downstream terminal branches
- a terminal/radiator branch, if it serves one emitter only

Therefore, flow responsibility determines authority, not physical orientation.

A riser to an upstairs radiator does not automatically become a leg. It only becomes part of a common leg or subleg circuit when it carries accumulated flow for downstream branches or terminals.

## Index-circuit authority

The selected index route is not yet the true hydraulic index circuit.

The true index circuit only becomes authoritative after all terminal circuits are evaluated and sorted by calculated pressure drop.

Future rule:
Terminal branch pipe-size honesty

Terminal/radiator branches are not fixed at 15 mm.

15 mm may be a common domestic default, but modern high-insulation rooms can have small emitter flows and may use smaller branch pipework.

HVACgooee shall treat terminal branch diameter as user-editable pipe intent, later checkable by hydraulic calculation.

Current limitation

H-S currently shows a simplified common/main plus selected index route plus non-index terminal subleg view.

H-S does not yet model arbitrary branch attachment points, named junctions, true terminal-circuit paths, or calculated pressure-drop ranking.

Locked statement

HVACgooee hydronics shall support a leg/subleg topology model. Leg 1 is the boiler/common leg and carries the combined
accumulated flow of all downstream subleg circuits and terminal branches.
Each leg or section carries the accumulated flow of the downstream branches
it serves. Before pressure-loss calculation exists, HVACgooee may display
a selected index route, but the true index circuit is only authoritative
after all terminal circuits are evaluated and sorted by calculated pressure
drop.

```text
Index circuit = max(Δp of all terminal circuits)